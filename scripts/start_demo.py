#!/usr/bin/env python3
"""Start the local real-model API and, by default, an authenticated HTTPS demo."""

from __future__ import annotations

import argparse
import os
import secrets
import sys
import time

from demo_runtime import (
    ROOT, DemoError, authenticated_ready, ensure_cloudflared, health_ready, is_owned, private_json,
    read_connection, require_free_port, runtime_lock, spawn_owned, stop_record,
    wait_ready, wait_tunnel,
)


def start(port=8000, local_only=False, startup_timeout=120):
    python = ROOT / ".venv/bin/python"
    if not python.exists():
        raise DemoError("The project .venv is missing. Follow docs/demo-backend.md to set it up.")
    with runtime_lock(ROOT):
        previous = read_connection(ROOT)
        if previous:
            active = (is_owned(previous.get("api"), ROOT) and health_ready(previous.get("local_endpoint", ""))
                      and authenticated_ready(previous.get("local_endpoint", ""), previous.get("token")))
            tunnel_ok = previous.get("local_only") or (is_owned(previous.get("tunnel"), ROOT) and health_ready(previous.get("endpoint", "")))
            if active and tunnel_ok and previous.get("local_only") == local_only and previous.get("port") == port:
                print("OtherWise demo is already running.")
                print(f"Endpoint: {previous['endpoint']}")
                print("Private token: .cache/demo/connection.json (not printed)")
                return previous
            stop_record(previous, ROOT)
        require_free_port(port)
        executable = None if local_only else ensure_cloudflared(ROOT)
        token = secrets.token_urlsafe(32)
        local_endpoint = f"http://127.0.0.1:{port}"
        record = {"schema": 1, "root": str(ROOT), "created_at": int(time.time()),
                  "port": port, "local_only": local_only, "local_endpoint": local_endpoint,
                  "endpoint": local_endpoint, "token": token, "api": None, "tunnel": None,
                  "ready": False}
        connection = ROOT / ".cache/demo/connection.json"
        private_json(connection, record)
        prior_token = os.environ.get("OTHERWISE_API_TOKEN")
        try:
            os.environ["OTHERWISE_API_TOKEN"] = token
            print("Starting the real recommendation model. This can take a moment.")
            _, record["api"] = spawn_owned([
                str(python), "-m", "uvicorn", "main:app", "--app-dir", str(ROOT),
                "--host", "127.0.0.1", "--port", str(port), "--workers", "1", "--no-access-log",
            ], "api", ROOT)
            private_json(connection, record)
            wait_ready(local_endpoint, record["api"], ROOT, timeout=startup_timeout, token=token)
            if not local_only:
                print("Connecting the temporary HTTPS demo tunnel.")
                config = ROOT / ".cache/demo/cloudflared-empty.yml"
                private_json(config, {})
                _, record["tunnel"] = spawn_owned([
                    str(executable), "tunnel", "--config", str(config),
                    "--no-autoupdate", "--url", local_endpoint, "--protocol", "http2",
                    "--loglevel", "info", "--metrics", "127.0.0.1:0", "--grace-period", "2s",
                ], "tunnel", ROOT)
                private_json(connection, record)
                record["endpoint"] = wait_tunnel(record["tunnel"], ROOT, token=token)
            record["ready"] = True
            private_json(connection, record)
        except BaseException:
            stop_record(record, ROOT)
            connection.unlink(missing_ok=True)
            raise
        finally:
            if prior_token is None:
                os.environ.pop("OTHERWISE_API_TOKEN", None)
            else:
                os.environ["OTHERWISE_API_TOKEN"] = prior_token
        print("OtherWise demo is ready.")
        print(f"Endpoint: {record['endpoint']}")
        print("Private token: .cache/demo/connection.json (not printed)")
        print("Stop with Stop-OtherWise-Demo.command or scripts/stop_demo.py.")
        return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--local-only", action="store_true", help="Do not download or start a public tunnel.")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--startup-timeout", type=float, default=120)
    args = parser.parse_args()
    if not 1024 <= args.port <= 65535 or not 1 <= args.startup_timeout <= 600:
        parser.error("port must be 1024–65535 and startup timeout must be 1–600 seconds")
    try:
        start(port=args.port, local_only=args.local_only, startup_timeout=args.startup_timeout)
    except DemoError as exception:
        print(f"Could not start OtherWise: {exception}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("Startup cancelled; the owned demo processes were stopped.", file=sys.stderr)
        return 130
    except Exception:
        print("Could not start OtherWise. Check the private .cache/demo logs; no credentials were printed.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
