# MCP Client (CLI) in Docker — `mcp-client-cmd`

A minimal Docker setup to run the **Model Context Protocol (MCP) CLI** against an **Alfresco MCP Server**

It ships an opinionated entrypoint that:

- Launches `mcp-cli` in interactive mode
- Proxies the MCP Server via `mcp-proxy` (StreamableHTTP)
- For **Ollama** on your host, forwards `127.0.0.1:11434` inside the container to your host’s `11434` using `socat`, so tools that expect a local Ollama "just work"

> This README is specific to the `mcp-client-cmd/` folder. It assumes you already have an MCP Server running (for example, the Alfresco MCP Server from this repository)

## Architecture

```
Host (your laptop)                    Container: mcp-client
┌───────────────────────────┐        ┌─────────────────────────────────────┐
│  Ollama @ localhost:11434 │  ◄──►  │ 127.0.0.1:11434  (forward via socat)│
│  Alfresco MCP Server      │  ◄──►  │ mcp-cli + mcp-proxy (streamablehttp)│
│  @ localhost:8003/mcp     │        │                                     │
└───────────────────────────┘        └─────────────────────────────────────┘
```

* **mcp-cli** runs interactively
* **mcp-proxy** connects to your Alfresco MCP Server over HTTP
* **socat** forwards the container’s `127.0.0.1:11434` to the host `11434` so the Ollama client looks "local" from inside the container

## Prerequisites

- Docker and Docker Compose
- An **Alfresco MCP Server** listening on `http://localhost:8003/mcp` (or another reachable URL)
- **Ollama** running on your host and a model available (defaults to `gpt-oss`):  
  ```bash
  # Install/start Ollama and pre-pull the model you want
  ollama pull gpt-oss
  ollama serve
  ```

> macOS & Windows: `host.docker.internal` resolves to the host automatically
> Linux: add `extra_hosts` or `--add-host=host.docker.internal:host-gateway`

## Quick start (best path)

From this `mcp-client-cmd/` folder:

```bash
docker compose up --build
```

You should see the MCP CLI banner, then you can start chatting. The service uses the included `server_config.json` by default.

Stop with `Ctrl+C`. Remove with `docker compose down`.

## Configuration

### MCP server URL

`server_config.json` is mounted read‑only into the container and points `mcp-proxy` to your MCP server:

```jsonc
{
  "mcpServers": {
    "alfresco": {
      "command": "mcp-proxy",
      "args": [
        "--transport", "streamablehttp",
        "http://host.docker.internal:8003/mcp"
      ]
    }
  }
}
```

- **Change the URL** if your server is elsewhere (e.g., another host/port)
- For Linux hosts, also see the `extra_hosts` tip below

### LLM provider (Ollama) and model

The container writes an internal `~/.chuk_llm/config.yaml` on startup using these env vars:

- `LLM_PROVIDER` (default: `ollama`)
- `LLM_MODEL` (default: `gpt-oss`)
- `OLLAMA_LOCAL_URL` (default: `http://127.0.0.1:11434`) — what the client will use inside the container
- `OLLAMA_FORWARD_TARGET` (default: `host.docker.internal:11434`) — where to forward to on the host

Example of what the generated config looks like for Ollama:

```yaml
ollama:
  api_base: http://127.0.0.1:11434
  default_model: gpt-oss
```

> To use a different model, set `LLM_MODEL=mistral` (or any local model you’ve pulled with Ollama)

### Environment variables

These are defined in `compose.yaml`. Override them via `docker compose` or the environment:

```yaml
services:
  mcp-client:
    build: .
    tty: true
    stdin_open: true
    environment:
      LLM_PROVIDER: ollama
      LLM_MODEL: gpt-oss
      OLLAMA_FORWARD_TARGET: host.docker.internal:11434
      OLLAMA_LOCAL_URL: http://127.0.0.1:11434
    volumes:
      - ./server_config.json:/work/server_config.json:ro
```

## Commands

The container’s default command runs:

```bash
mcp-cli chat --server alfresco --config-file /work/server_config.json
```

Other handy commands once you’re in the container shell (or by changing `CMD`):

```bash
# List MCP providers
mcp-cli providers --config-file /work/server_config.json

# Check server connectivity
mcp-cli ping --server alfresco --config-file /work/server_config.json

# List tools exposed by the server
mcp-cli tools --server alfresco --config-file /work/server_config.json
```

## Troubleshooting

**1) Invalid API base URL: http://host.docker.internal:11434**  
Inside the container, the client speaks to **`http://127.0.0.1:11434`** (not `host.docker.internal`). The entrypoint already forwards that to your host’s `11434`. Make sure:

- Ollama is running on the host (`curl http://localhost:11434/api/tags`)
- `OLLAMA_FORWARD_TARGET` is correct (host IP/port)
- You didn’t override `OLLAMA_LOCAL_URL` away from `http://127.0.0.1:11434`

**2) Linux: `host.docker.internal` does not resolve**  
Add this to `compose.yaml` under the service or run with `--add-host`:

```yaml
extra_hosts:
  - "host.docker.internal:host-gateway"
```

**3) The MCP server isn’t reachable**  
- Ensure it’s listening on the right interface/port (`0.0.0.0:8003` if running in Docker)
- Update `server_config.json` to the correct URL
- Test from the host: `curl http://localhost:8003/mcp` (you should get a response/handshake endpoint)

**4) No Ollama models available**  
Run on the host: `ollama pull gpt-oss` (or your chosen model)