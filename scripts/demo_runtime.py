"""Private files, verified binaries, and owned processes for the demo launcher."""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
import platform
import re
import signal
import socket
import subprocess
import tarfile
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from contextlib import contextmanager
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RELEASE_API = "https://api.github.com/repos/cloudflare/cloudflared/releases/latest"
ASSET_NAME = "cloudflared-darwin-arm64.tgz"


class DemoError(RuntimeError):
    """Safe user-facing error, with no credential or request contents."""


def private_dir(directory):
    directory = Path(directory)
    if directory.is_symlink():
        raise DemoError("The private runtime directory must not be a symbolic link.")
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    directory.chmod(0o700)
    return directory


def private_json(filename, value):
    filename = Path(filename)
    private_dir(filename.parent)
    if filename.is_symlink():
        raise DemoError("The private runtime file must not be a symbolic link.")
    with tempfile.NamedTemporaryFile(mode="w", dir=filename.parent, delete=False, encoding="utf-8") as stream:
        temporary = Path(stream.name)
        try:
            os.fchmod(stream.fileno(), 0o600)
            json.dump(value, stream, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        except BaseException:
            temporary.unlink(missing_ok=True)
            raise
    try:
        temporary.replace(filename)
    finally:
        temporary.unlink(missing_ok=True)


@contextmanager
def runtime_lock(root=ROOT):
    directory = private_dir(Path(root) / ".cache/demo")
    descriptor = os.open(directory / "runtime.lock", os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    try:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise DemoError("Another demo start or stop is running. Try again shortly.") from None
        yield
    finally:
        os.close(descriptor)


def read_connection(root=ROOT):
    filename = Path(root) / ".cache/demo/connection.json"
    if not filename.exists():
        return None
    if filename.is_symlink():
        raise DemoError("Refusing to read a linked runtime connection file.")
    try:
        if filename.stat().st_size > 32_768:
            raise ValueError
        record = json.loads(filename.read_text())
        if not isinstance(record, dict) or record.get("root") != str(Path(root).resolve()):
            raise ValueError
    except (OSError, ValueError, TypeError):
        raise DemoError("The connection file is invalid for this repository; existing processes were left untouched.") from None
    filename.chmod(0o600)
    return record


def _process_snapshot(pid, kind):
    if type(pid) is not int or pid <= 1:
        return None
    result = subprocess.run(["/bin/ps", "-p", str(pid), "-o", "uid=,lstart=,command="],
                            capture_output=True, text=True, timeout=3,
                            env=dict(os.environ, LC_ALL="C"))
    match = re.match(r"\s*(\d+)\s+(\w{3}\s+\w{3}\s+\d+\s+\d\d:\d\d:\d\d\s+\d{4})\s+(.+)", result.stdout)
    if result.returncode or not match:
        return None
    return {"pid": pid, "uid": int(match[1]), "started": match[2], "command": match[3].strip(), "kind": kind}


def process_record(pid, kind):
    # macOS Python launchers re-exec into Python.app shortly after Popen returns.
    # Capture a stable identity rather than the transient launcher command.
    previous = _process_snapshot(pid, kind)
    for _ in range(8):
        if previous is None:
            return None
        time.sleep(.03)
        current = _process_snapshot(pid, kind)
        if current == previous:
            return current
        previous = current
    return None


def is_owned(record, root=ROOT):
    if not isinstance(record, dict) or record.get("kind") not in {"api", "tunnel"}:
        return False
    if record.get("uid") != os.getuid() or str(Path(root).resolve()) not in record.get("command", ""):
        return False
    try:
        current = process_record(record.get("pid"), record.get("kind"))
    except (OSError, subprocess.SubprocessError):
        return False
    return bool(current and current == record)


def stop_owned(record, root=ROOT, timeout=8):
    if not is_owned(record, root):
        return False
    pid = record["pid"]
    try:
        os.kill(pid, signal.SIGTERM)
    except ProcessLookupError:
        return True
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if not is_owned(record, root):
            return True
        time.sleep(.1)
    # Recheck the exact PID/start/user/command immediately before escalation.
    if is_owned(record, root):
        try:
            os.kill(pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    deadline = time.monotonic() + 2
    while time.monotonic() < deadline and is_owned(record, root):
        time.sleep(.1)
    if is_owned(record, root):
        raise DemoError("An owned process did not stop. Its connection metadata was preserved.")
    return True


def stop_record(record, root=ROOT):
    return sum(stop_owned(record.get(kind), root) for kind in ("tunnel", "api"))


def require_free_port(port):
    with socket.socket() as listener:
        try:
            listener.bind(("127.0.0.1", port))
        except OSError:
            raise DemoError("The requested port is already in use. Stop its owner or choose another --port.") from None


def spawn_owned(argv, kind, root=ROOT):
    directory = private_dir(Path(root) / ".cache/demo")
    log_path = directory / f"{kind}.log"
    descriptor = os.open(log_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_NOFOLLOW, 0o600)
    os.fchmod(descriptor, 0o600)
    with os.fdopen(descriptor, "wb") as stream:
        env = os.environ.copy()
        if kind == "tunnel":
            env.pop("OTHERWISE_API_TOKEN", None)
            for key in list(env):
                if key.startswith("TUNNEL_"):
                    env.pop(key, None)
        process = subprocess.Popen(argv, cwd=root, env=env, stdin=subprocess.DEVNULL,
                                   stdout=stream, stderr=subprocess.STDOUT, start_new_session=True)
    for _ in range(20):
        record = process_record(process.pid, kind)
        if record:
            return process, record
        if process.poll() is not None:
            break
        time.sleep(.05)
    # This is the exact Popen object just created, so terminating it is safe.
    process.terminate()
    process.wait(timeout=5)
    raise DemoError("The demo process could not start. Check its private runtime log.")


def health_ready(endpoint):
    try:
        request = urllib.request.Request(endpoint.rstrip("/") + "/health", headers={"User-Agent": "OtherWise-demo"})
        with urllib.request.urlopen(request, timeout=2) as response:
            return response.status == 200 and json.loads(response.read(2048)).get("ready") is True
    except (OSError, ValueError, urllib.error.URLError):
        return False


def authenticated_ready(endpoint, token):
    """Prove this endpoint serves our newly generated token, not a port rival."""
    if not isinstance(token, str) or not token:
        return False
    target = endpoint.rstrip("/") + "/api/recommend"
    payload = json.dumps({"keywords": ["Gardening"], "mode": "path", "focus": "Gardening",
                          "expansion_level": 0, "limit": 1}).encode()
    try:
        denied = urllib.request.Request(target, data=payload, headers={"Content-Type": "application/json", "Authorization": "Bearer invalid-" + token})
        try:
            with urllib.request.urlopen(denied, timeout=3):
                return False
        except urllib.error.HTTPError as response:
            if response.code != 401:
                return False
        approved = urllib.request.Request(target, data=payload, headers={"Content-Type": "application/json", "Authorization": "Bearer " + token})
        with urllib.request.urlopen(approved, timeout=5) as response:
            result = json.loads(response.read(16_384))
            return response.status == 200 and isinstance(result.get("recommendations"), list) and result.get("mode") == "path"
    except (OSError, ValueError, urllib.error.URLError):
        return False


def wait_ready(endpoint, record, root=ROOT, timeout=120, token=None):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if not is_owned(record, root):
            raise DemoError("The backend stopped before it was ready. Check .cache/demo/api.log.")
        if health_ready(endpoint) and authenticated_ready(endpoint, token):
            return
        time.sleep(.5)
    raise DemoError("The backend did not become ready before the deadline. Check .cache/demo/api.log.")


def release_asset(release):
    asset = next((item for item in release.get("assets", []) if item.get("name") == ASSET_NAME), None)
    if not asset:
        raise DemoError("The official release does not include the Darwin arm64 download.")
    url = asset.get("browser_download_url", "")
    if not url.startswith("https://github.com/cloudflare/cloudflared/releases/download/"):
        raise DemoError("Refusing a download outside the official Cloudflare release repository.")
    digest = asset.get("digest") or ""
    if re.fullmatch(r"sha256:[a-fA-F0-9]{64}", digest):
        checksum = digest.split(":", 1)[1].lower()
    else:
        match = re.search(re.escape(ASSET_NAME) + r":\s*([a-fA-F0-9]{64})", release.get("body", ""))
        if not match:
            raise DemoError("The official release has no SHA256 checksum; no executable was installed.")
        checksum = match[1].lower()
    return {"url": url, "sha256": checksum, "release": release.get("tag_name", "unknown")}


def official_download(url, limit):
    request = urllib.request.Request(url, headers={"User-Agent": "OtherWise-demo", "Accept": "application/vnd.github+json" if url == RELEASE_API else "application/octet-stream"})
    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            final = urllib.parse.urlsplit(response.url)
            if final.scheme != "https" or final.hostname not in {"api.github.com", "github.com", "release-assets.githubusercontent.com", "objects.githubusercontent.com"}:
                raise DemoError("The official download redirected to an unexpected host.")
            data = response.read(limit + 1)
            if len(data) > limit:
                raise DemoError("The official download exceeded the expected size.")
            return data
    except (OSError, urllib.error.URLError):
        raise DemoError("The official cloudflared download is unavailable. Try again or use --local-only.") from None


def ensure_cloudflared(root=ROOT):
    if platform.system() != "Darwin" or platform.machine().lower() not in {"arm64", "aarch64"}:
        raise DemoError("The shared launcher currently supports Apple Silicon Macs. Use --local-only elsewhere.")
    directory = private_dir(Path(root) / ".cache/bin")
    executable, metadata = directory / "cloudflared", directory / "cloudflared-release.json"
    if executable.exists() and not executable.is_symlink() and metadata.exists():
        try:
            info = json.loads(metadata.read_text())
            if hashlib.sha256(executable.read_bytes()).hexdigest() == info["binary_sha256"]:
                return executable
        except (OSError, ValueError, KeyError):
            pass
    try:
        asset = release_asset(json.loads(official_download(RELEASE_API, 2_000_000)))
    except (ValueError, TypeError):
        raise DemoError("The official release metadata was invalid; no executable was installed.") from None
    archive = official_download(asset["url"], 64_000_000)
    if hashlib.sha256(archive).hexdigest() != asset["sha256"]:
        raise DemoError("The cloudflared archive checksum did not match the official release; installation stopped.")
    import io
    try:
        with tarfile.open(fileobj=io.BytesIO(archive), mode="r:gz") as bundle:
            members = [member for member in bundle.getmembers() if Path(member.name).name == "cloudflared" and member.isfile()]
            if len(members) != 1 or members[0].size > 100_000_000:
                raise DemoError("The verified archive had an unexpected executable layout.")
            binary = bundle.extractfile(members[0]).read()
    except tarfile.TarError:
        raise DemoError("The verified cloudflared archive could not be opened.") from None
    with tempfile.NamedTemporaryFile(dir=directory, delete=False) as stream:
        temporary = Path(stream.name)
        try:
            stream.write(binary)
            os.fchmod(stream.fileno(), 0o755)
            stream.flush()
            os.fsync(stream.fileno())
        except BaseException:
            temporary.unlink(missing_ok=True)
            raise
    try:
        temporary.replace(executable)
    finally:
        temporary.unlink(missing_ok=True)
    private_json(metadata, {"release": asset["release"], "asset_url": asset["url"],
                            "archive_sha256": asset["sha256"], "binary_sha256": hashlib.sha256(binary).hexdigest()})
    return executable


def wait_tunnel(record, root=ROOT, timeout=90, token=None):
    deadline = time.monotonic() + timeout
    log = Path(root) / ".cache/demo/tunnel.log"
    endpoint = None
    while time.monotonic() < deadline:
        if not is_owned(record, root):
            raise DemoError("The tunnel stopped before connecting. Check .cache/demo/tunnel.log.")
        if endpoint is None:
            text = log.read_text(errors="replace")[-65_536:]
            match = re.search(r"https://[a-z0-9-]+\.trycloudflare\.com", text)
            if match:
                endpoint = match[0]
        if endpoint and health_ready(endpoint) and authenticated_ready(endpoint, token):
            return endpoint
        time.sleep(.5)
    raise DemoError("The shared tunnel did not become ready. Check .cache/demo/tunnel.log or use --local-only.")
