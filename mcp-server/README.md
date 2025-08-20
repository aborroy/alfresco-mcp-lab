# Alfresco MCP Server (`mcp-server`)

Containerized **MCP Server** for Alfresco, exposing a Streamable HTTP endpoint (default **`/mcp` on port `8003`**)

## What this provides

- A Docker image that runs the MCP server (`ENTRYPOINT ["python", "run_server.py"]`)
- **Transport selection** via env: `TRANSPORT=http|stdio|sse` (default: `http`)
  When `http`, the server binds `HOST`/`PORT` and listens on **`/mcp`**.
- **Alfresco connection** is configured via `.env` (`ALFRESCO_URL`, `ALFRESCO_USERNAME`, `ALFRESCO_PASSWORD`, `ALFRESCO_VERIFY_SSL`)
- Log level configurable via `LOG_LEVEL` (default: `INFO`)

> The Dockerfile builds a Python image and launches `run_server.py`. No extra reverse proxy or sidecars are used here.

## Quick start (Docker Compose)

1) **Edit `.env`** to match your setup (see [Configuration](#configuration)). Defaults are suitable for Docker Desktop with Alfresco on the host.

2) **Run the server**:
```bash
docker compose up --build
```

3) **Endpoint (HTTP transport)**:
- URL: `http://localhost:${MCP_PORT:-8003}/mcp`  
- Example quick probe:
  ```bash
  curl -i http://localhost:8003/mcp
  ```

Stop with `Ctrl+C`. Clean up with:
```bash
docker compose down -v
```

## Configuration

All settings come from `.env` and are passed into the container by `compose.yaml`:

### Core server
- **`MCP_PORT`** — host port to publish (default `8003`). Container always listens on `8003`
- **`TRANSPORT`** — `http` (default) | `stdio` | `sse`  
  - `http`: binds `HOST`:`PORT` and serves at `/mcp`
  - `stdio`/`sse`: intended for non-HTTP transports; the published port isn’t used
- **`LOG_LEVEL`** — `DEBUG` | `INFO` | `WARNING` | `ERROR` (default `INFO`)

### Alfresco connection (used by server tools)
- **`ALFRESCO_URL`** — base URL of Alfresco (e.g., `http://host.docker.internal:8080` on macOS/Windows, or `http://172.17.0.1:8080` on Linux)
- **`ALFRESCO_USERNAME`**, **`ALFRESCO_PASSWORD`** credentials
- **`ALFRESCO_VERIFY_SSL`** — `true`/`false` (default `false`). Set `true` for proper TLS verification in production

**Example `.env`** (shipped in this folder):
```dotenv
# MCP server port (host)
MCP_PORT=8003

# Transport for the server: http | stdio | sse
TRANSPORT=http

# ---- Alfresco connection ----
# If Alfresco runs on the same host:
# - macOS/Windows Docker Desktop: http://host.docker.internal:8080
# - Linux: http://<your-host-ip>:8080 (e.g., http://172.17.0.1:8080)
ALFRESCO_URL=http://host.docker.internal:8080
ALFRESCO_USERNAME=admin
ALFRESCO_PASSWORD=admin
ALFRESCO_VERIFY_SSL=false

# Logging
LOG_LEVEL=INFO
```

## Compose service

`compose.yaml` defines a single service, publishes the port, and wires env vars:

```yaml
services:
  alfresco-mcp:
    build:
      context: .
    environment:
      TRANSPORT: ${TRANSPORT:-http}   # http | stdio | sse
      HOST: 0.0.0.0
      PORT: ${MCP_PORT:-8003}
      ALFRESCO_URL: ${ALFRESCO_URL}
      ALFRESCO_USERNAME: ${ALFRESCO_USERNAME}
      ALFRESCO_PASSWORD: ${ALFRESCO_PASSWORD}
      ALFRESCO_VERIFY_SSL: ${ALFRESCO_VERIFY_SSL:-false}
      LOG_LEVEL: ${LOG_LEVEL:-INFO}
    ports:
      - "${MCP_PORT:-8003}:8003"
```

> The container always exposes **8003**. Change the **host** side with `MCP_PORT`

## Verifying the server

- **HTTP (default)**: After `docker compose up`, verify the endpoint is listening:
  ```bash
  curl -i http://localhost:${MCP_PORT:-8003}/mcp
  ```
  You should receive an HTTP response from the MCP endpoint
- **With a client**: Point your MCP client to `http://localhost:${MCP_PORT:-8003}/mcp`

## Transport notes

- **`http`**: easiest to use with containerized or desktop clients (recommended for this lab)
- **`stdio` / `sse`**: specialized transports; you typically won’t map ports. If you switch to these, ensure your client matches and adjust Compose accordingly (you may remove the `ports` mapping)

## Troubleshooting

- **Cannot reach `ALFRESCO_URL` from the container**  
  - macOS/Windows: use `http://host.docker.internal:8080`
  - Linux: use your host IP (e.g., `http://172.17.0.1:8080`) or add `--add-host` mapping
- **401/403 from Alfresco**  
  - Check `ALFRESCO_USERNAME`/`ALFRESCO_PASSWORD` and permissions
- **Port already in use**  
  - Change `MCP_PORT` in `.env`, e.g., `MCP_PORT=8013`
- **SSL verification failures**  
  - For self-signed dev setups, set `ALFRESCO_VERIFY_SSL=false`. For production, use valid TLS and `true`