# MCP Client UI (`mcp-client-ui`)

A minimal **web UI built with Chainlit** to chat with an MCP Server

It’s containerized, configurable via `.env`, and uses **LiteLLM** as the LLM gateway

## What you get

- Chainlit front-end (`app.py`) that starts a chat UI on port 8000
- MCP connection via an HTTP endpoint provided in `MCP_URL` (Streamable HTTP, typically `/mcp`)
- LiteLLM integration via `LITELLM_API_BASE`, `LITELLM_API_KEY`, and `LITELLM_MODEL`

> No MCP proxy or Ollama forwarding is set up here. Point the UI directly at your MCP Server’s Streamable HTTP endpoint using `MCP_URL`

## Prerequisites

- Docker and Docker Compose
- An MCP Server reachable via HTTP (e.g., `http://host.docker.internal:8003/mcp`)
- A LiteLLM endpoint + API key (public cloud or your internal proxy)

## Quick start

1) Copy the example env file:
```bash
cp .env.example .env
```

2) Edit `.env` with your values:
```dotenv
# LiteLLM (required)
LITELLM_API_KEY=sk-...
LITELLM_API_BASE=https://<your-litellm-endpoint>
LITELLM_MODEL=litellm_proxy/anthropic.claude-sonnet-4-20250514-v1:0

# MCP server (required)
MCP_URL=http://host.docker.internal:8003/mcp

LOG_LEVEL=INFO
```

> macOS/Windows: `host.docker.internal` resolves to the host automatically.  
> Linux: replace with your host IP (e.g., `http://172.17.0.1:8003/mcp`).

3) Build and run:
```bash
docker compose up --build
```

4) Open the UI: http://localhost:8000

Stop with `Ctrl+C`. Remove with `docker compose down`

## Local development (without Docker)

1) Python 3.12+ and a virtual environment:
```bash
python -m venv .venv
. .venv/bin/activate  # (Windows) .\.venv\Scripts\activate
```

2) Install dependencies:
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

3) Copy env and edit values:
```bash
cp .env.example .env
# edit .env
```

4) Run the app:
```bash
chainlit run app.py --host 0.0.0.0 --port 8000
```

Open http://localhost:8000

## Configuration reference

These variables are read from `.env` (Compose will also pick them up automatically):

- LITELLM_API_KEY — API key for your LiteLLM gateway.
- LITELLM_API_BASE — Base URL of the LiteLLM gateway (e.g., `https://api.example.com/litellm`).
- LITELLM_MODEL — Fully-qualified model name understood by your LiteLLM.
- MCP_URL — Streamable HTTP endpoint of your MCP Server (typically ends with `/mcp`).  
  Examples:
  - `http://host.docker.internal:8003/mcp` (Docker Desktop on macOS/Windows)
  - `http://172.17.0.1:8003/mcp` (Linux; replace with your host IP)
- LOG_LEVEL — e.g., `DEBUG`, `INFO`, `WARNING`.

The included `compose.yaml` wires these environment variables into the container and publishes port **8000**

## Troubleshooting

1) Blank UI or "cannot connect" errors
- Ensure `MCP_URL` is reachable from the container host. Test from your host:
  ```bash
  curl -i http://host.docker.internal:8003/mcp
  ```
- On Linux, replace `host.docker.internal` with your host IP

2) 401/403 from the LLM
- Double-check `LITELLM_API_KEY` and `LITELLM_API_BASE`
- Confirm the `LITELLM_MODEL` exists/allowed in your gateway

3) Port 8000 already in use
- Edit the port mapping in `compose.yaml`, e.g. `- "8080:8000"`