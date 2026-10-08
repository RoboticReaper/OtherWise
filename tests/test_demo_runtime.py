"""Launcher safety: real private files/processes and offline release fixtures."""

import importlib
import json
import os
import signal
import runpy
import subprocess
import sys
import time
from pathlib import Path

import pytest


def runtime():
    try:
        return importlib.import_module("scripts.demo_runtime")
    except ModuleNotFoundError:
        pytest.fail("The owned demo runtime has not been implemented.")


def test_connection_file_and_directory_are_private_even_on_overwrite(tmp_path):
    module = runtime()
    filename = tmp_path / ".cache/demo/connection.json"
    module.private_json(filename, {"token": "private-test-token"})
    assert filename.stat().st_mode & 0o777 == 0o600
    assert filename.parent.stat().st_mode & 0o777 == 0o700
    filename.chmod(0o644)
    module.private_json(filename, {"token": "new-private-test-token"})
    assert filename.stat().st_mode & 0o777 == 0o600
    assert json.loads(filename.read_text())["token"] == "new-private-test-token"


def test_release_asset_digest_is_preferred_to_stale_release_body_checksum():
    module = runtime()
    correct, stale = "a" * 64, "b" * 64
    release = {"tag_name": "2026.9.1", "body": f"cloudflared-darwin-arm64.tgz: {stale}", "assets": [{"name": "cloudflared-darwin-arm64.tgz", "digest": f"sha256:{correct}", "browser_download_url": "https://github.com/cloudflare/cloudflared/releases/download/2026.9.1/cloudflared-darwin-arm64.tgz"}]}
    assert module.release_asset(release)["sha256"] == correct


def test_release_without_official_checksum_or_with_foreign_url_is_rejected():
    module = runtime()
    asset = {"name": "cloudflared-darwin-arm64.tgz", "browser_download_url": "https://foreign.example/cloudflared.tgz"}
    with pytest.raises(module.DemoError):
        module.release_asset({"assets": [asset], "body": ""})
    asset["digest"] = "sha256:" + "a" * 64
    with pytest.raises(module.DemoError):
        module.release_asset({"assets": [asset], "body": ""})


def test_stale_pid_metadata_never_stops_an_unrelated_live_process(tmp_path):
    module = runtime()
    process = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"])
    try:
        record = {"pid": process.pid, "uid": os.getuid(), "started": "old start time", "command": "old owned command", "kind": "api"}
        assert not module.stop_owned(record, tmp_path, timeout=.1)
        assert process.poll() is None
    finally:
        process.terminate()
        process.wait(timeout=5)


def test_stop_owned_verifies_command_start_time_and_user_before_signaling(tmp_path):
    module = runtime()
    process = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)", str(tmp_path)])
    try:
        record = module.process_record(process.pid, "api")
        assert module.is_owned(record, tmp_path)
        changed = record | {"command": record["command"] + " changed"}
        assert not module.is_owned(changed, tmp_path)
        changed_user = record | {"uid": -1}
        assert not module.is_owned(changed_user, tmp_path)
        assert module.stop_owned(record, tmp_path, timeout=.5)
        process.wait(timeout=5)
        assert process.returncode == -signal.SIGTERM
    finally:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=5)


def test_lock_prevents_overlapping_start_stop_and_releases_cleanly(tmp_path):
    module = runtime()
    with module.runtime_lock(tmp_path):
        with pytest.raises(module.DemoError):
            with module.runtime_lock(tmp_path):
                pass
    with module.runtime_lock(tmp_path):
        pass


def test_read_connection_refuses_wrong_repository_without_exposing_token(tmp_path):
    module = runtime()
    filename = tmp_path / ".cache/demo/connection.json"
    module.private_json(filename, {"root": "/other/repo", "token": "private-should-not-echo"})
    with pytest.raises(module.DemoError) as exception:
        module.read_connection(tmp_path)
    assert "private-should-not-echo" not in str(exception.value)


@pytest.mark.parametrize("reuse_address", [0, 1])
@pytest.mark.parametrize("bind_address", ["127.0.0.1", "0.0.0.0"])
def test_failure_to_bind_does_not_reuse_an_unowned_backend(tmp_path, reuse_address, bind_address):
    import socket
    module = runtime()
    with socket.socket() as listener:
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, reuse_address)
        listener.bind((bind_address, 0))
        listener.listen()
        with pytest.raises(module.DemoError):
            module.require_free_port(listener.getsockname()[1])


def test_closed_server_connections_do_not_prevent_an_immediate_restart():
    import socket
    module = runtime()
    with socket.socket() as listener:
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listener.bind(("127.0.0.1", 0))
        listener.listen()
        port = listener.getsockname()[1]
        with socket.create_connection(("127.0.0.1", port)) as client:
            connection, _ = listener.accept()
            # The server closes first, leaving its port in TCP TIME_WAIT.
            connection.close()
            assert client.recv(1) == b""
    module.require_free_port(port)


def test_tunnel_does_not_inherit_backend_or_named_tunnel_credentials(tmp_path, monkeypatch):
    module = runtime()
    monkeypatch.setenv("OTHERWISE_API_TOKEN", "private-backend-token")
    monkeypatch.setenv("TUNNEL_TOKEN", "private-named-tunnel-token")
    process, record = module.spawn_owned([
        sys.executable, "-c", "import os,time; print(int('OTHERWISE_API_TOKEN' in os.environ or 'TUNNEL_TOKEN' in os.environ),flush=True); time.sleep(30)", str(tmp_path),
    ], "tunnel", tmp_path)
    try:
        log = tmp_path / ".cache/demo/tunnel.log"
        for _ in range(20):
            if log.read_text().strip():
                break
            time.sleep(.05)
        assert log.read_text().strip() == "0"
        assert log.stat().st_mode & 0o777 == 0o600
    finally:
        module.stop_owned(record, tmp_path)
        process.wait(timeout=5)


def test_stop_help_does_not_remove_connection_or_attempt_shutdown(tmp_path, monkeypatch):
    module = runtime()
    connection = tmp_path / ".cache/demo/connection.json"
    module.private_json(connection, {"root": str(tmp_path.resolve()), "token": "private-help-test", "api": None, "tunnel": None})
    monkeypatch.syspath_prepend(str(Path(module.__file__).parent))
    namespace = runpy.run_path(str(Path(module.__file__).with_name("stop_demo.py")), run_name="test_stop_help")
    namespace["main"].__globals__["ROOT"] = tmp_path
    monkeypatch.setattr(sys, "argv", ["stop_demo.py", "--help"])
    with pytest.raises(SystemExit) as result:
        namespace["main"]()
    assert result.value.code == 0
    assert connection.exists()


def test_foreign_healthy_server_cannot_satisfy_owned_backend_readiness(tmp_path):
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
    import threading
    module = runtime()

    class ForeignServer(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'{"ready":true}')

        def do_POST(self):
            self.send_response(401)
            self.end_headers()

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), ForeignServer)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    process = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)", str(tmp_path)])
    try:
        record = module.process_record(process.pid, "api")
        with pytest.raises(module.DemoError):
            module.wait_ready(f"http://127.0.0.1:{server.server_port}", record, tmp_path, timeout=.1, token="private-test-token")
    finally:
        server.shutdown()
        server.server_close()
        process.terminate()
        process.wait(timeout=5)


@pytest.mark.parametrize("local_only,expected_mode", [(True, "1"), (False, "0")])
def test_launcher_explicitly_selects_auth_mode_and_restores_environment(tmp_path, monkeypatch, local_only, expected_mode):
    module = runtime()
    monkeypatch.syspath_prepend(str(Path(module.__file__).parent))
    namespace = runpy.run_path(str(Path(module.__file__).with_name("start_demo.py")), run_name="test_start")
    start = namespace["start"]
    (tmp_path / ".venv/bin").mkdir(parents=True)
    (tmp_path / ".venv/bin/python").symlink_to(sys.executable)
    monkeypatch.setenv("OTHERWISE_LOCAL_MODE", "inherited-value")
    spawned = []

    def spawn(argv, kind, root):
        spawned.append((kind, os.environ.get("OTHERWISE_LOCAL_MODE"), argv))
        return None, {"kind": kind}

    for key, value in {
        "ROOT": tmp_path, "spawn_owned": spawn, "require_free_port": lambda port: None,
        "wait_ready": lambda *args, **kwargs: None,
        "ensure_cloudflared": lambda root: tmp_path / "cloudflared",
        "wait_tunnel": lambda *args, **kwargs: "https://test.trycloudflare.com",
    }.items():
        monkeypatch.setitem(start.__globals__, key, value)
    record = start(local_only=local_only)
    assert spawned[0][0:2] == ("api", expected_mode)
    assert record["auth_mode"] == ("local" if local_only else "token")
    assert os.environ["OTHERWISE_LOCAL_MODE"] == "inherited-value"
    assert record["ready"] is True
    assert record["token"] not in " ".join(spawned[0][2])
