# Run the OtherWise recommendation demo

The extension connects to the real MPNet recommendation API running on this Mac. The shared demo uses a temporary Cloudflare HTTPS URL and a bearer token. Keep the Mac awake while teammates use it.

## Start and connect

1. Double-click **Start-OtherWise-Demo.command**. It starts the backend, waits for the real model to become ready, and opens a temporary HTTPS tunnel. The first start downloads Cloudflare's official Apple Silicon executable into `.cache/bin`, verifies its SHA256 against the official release metadata, and installs nothing globally.
2. Open `.cache/demo/connection.json` in a text editor. Hidden folders can be reached in Finder with **Go → Go to Folder**. Copy `endpoint` and `token` into the extension's connection settings. The launcher prints the endpoint and private file location; it never prints the token.
3. Share that endpoint and token directly with your intended teammates. The token is a shared secret, so keep it out of screenshots, repository files, and public posts. Browser history stays local; approved interests and network metadata reach the backend and tunnel.
4. Double-click **Stop-OtherWise-Demo.command** when finished. It checks each recorded process's user, start time, command, and repository association before stopping it, then removes the saved token. It never stops an unrelated process just because a recorded PID was reused.

Starting again while the same ready demo is running reuses it. After stopping and starting again, the endpoint and token change; update the extension settings. If startup fails or is cancelled, its owned processes are stopped and its incomplete connection file is removed. Private runtime logs are in `.cache/demo/api.log` and `.cache/demo/tunnel.log`; all `.cache` content is gitignored, and credentials are never passed on the process command line.

Readiness also checks that a deliberately wrong token is denied and the generated token succeeds, using the public catalog topic Gardening as a synthetic probe. This prevents another service that takes the same port from being exposed accidentally. The tunnel uses an isolated empty configuration and does not inherit unrelated named-tunnel credentials.

## Local-only testing

Double-click **Start-OtherWise-Local.command** to start the local backend without
a public tunnel. The same stop command and private connection file apply.

From the repository directory:

```sh
.venv/bin/python scripts/start_demo.py --local-only
.venv/bin/python scripts/stop_demo.py
```

This uses `http://127.0.0.1:8000`, generates the same private token file, and starts no public tunnel or tunnel download. For a busy port, add `--port 8765`. Startup waits up to 120 seconds by default; use `--startup-timeout 300` if the first model download needs longer. The launcher binds only to the local loopback address, uses one backend worker, and disables HTTP access logs.

## Python setup

The checked-out project's `.venv` and cached model can be reused. On another Mac with Python 3.13 installed, create a local environment and install the recorded project dependencies:

```sh
python3.13 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pip install -r requirements-layout.txt
```

The first model load downloads MPNet into `.cache/models`; subsequent launches reuse it and the catalog embeddings. There is no synthetic fallback if model loading fails. Automatic device selection uses available MPS on Apple Silicon, otherwise CPU. If needed, prefix the launch command with `OTHERWISE_MODEL_DEVICE=cpu`. Shared tunnel download currently targets Apple Silicon macOS; local-only mode works on other supported Python platforms.

After changing `data/topics.json`, prepare its embeddings before an interactive
launch so startup does not spend its readiness timeout encoding a large catalog:

```sh
.venv/bin/python -c 'from service.engine import RecommendationEngine; from service.discovery import DiscoveryEngine; engine = RecommendationEngine(); engine.initialize(); DiscoveryEngine(engine).initialize()'
```

Rebuild the Galaxy layout and extension from that exact same embedding cache.
The catalog and original-vector identities must match for Focus recommendations.
Source imports are separate maintenance commands; normal backend startup never
downloads Wikipedia or Wikidata topics.

The temporary hostname changes after restarting, ends when the tunnel stops, and has no uptime guarantee. It is intended for a short team demo. Recommendation requests still require the bearer token even when someone knows the public URL. See [Cloudflare's Quick Tunnel documentation](https://developers.cloudflare.com/tunnel/get-started/quick-tunnels/) and the [official cloudflared releases](https://github.com/cloudflare/cloudflared/releases). The installer prefers the asset-level SHA256 digest over release-body checksums and refuses a download without an official checksum.

## Adjustable Galaxy layouts

The layout dependencies above enable Galaxy’s **Layout settings → Generate preview**. The backend recomputes the same public MPNet catalog, using bounded exact neighborhoods and UMAP. Requests carry only the public catalog/vector identity and four layout controls; saved interests and browsing history are not sent. The authenticated POST starts a job and authenticated GET polls its status. Only one new layout is computed at a time; repeated parameters reuse a bounded public geometry cache. Health and recommendations remain available while a layout runs. The first computation can take longer while original-vector neighbors are prepared.

The packaged B layout works without a connection or these numerical dependencies. A failed preview retains the previous map. Restart the backend after updating its code; then copy the new local connection token into Settings if the launcher generated a new one.
