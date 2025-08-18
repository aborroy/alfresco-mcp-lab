# Alfresco MCP Lab

> A reproducible laboratory to experiment with the **Model Context Protocol (MCP)** against **Alfresco Community Edition** using Docker

## Table of Contents

* [Goals & Audience](#goals--audience)
* [Architecture](#architecture)
* [Prerequisites](#prerequisites)
* [1) Install Alfresco ACS Stack](#1-install-alfresco-acs-stack)
* [2) Build & Run the Alfresco MCP Server](#2-build--run-the-alfresco-mcp-server)
* [3) Configure an MCP Client](#3-configure-an-mcp-client)
* [4) Test Scenarios](#4-test-scenarios)
* [Troubleshooting](#troubleshooting)
* [Credits & Acknowledgements](#credits--acknowledgements)

## Goals & Audience

You will learn to:

* Spin up **Alfresco Community Edition** locally with Docker
* Run a **Python-based MCP Server** that talks to Alfresco
* Use an **MCP client** (CLI) to query and act on Alfresco content via MCP

**Who is this for?** Developers evaluating MCP + Alfresco integrations, PoCs, and demos

## Architecture

```
[MCP Client] --(streamable HTTP via mcp-proxy)--> [MCP Server] ---> [Alfresco ACS]
    |                             |                     |                 |
 Ollama                          CLI                  Docker            Docker
```

* We use a Python MCP server implementation for Alfresco
* Communication from CLI uses `mcp-proxy` over HTTP to the server’s `/mcp` endpoint

## Prerequisites

* Docker and Docker Compose
* Git
* For the CLI path described here:

  * Ollama with the `gpt-oss` model pulled (around 13 GB)
  * uv (Python tool launcher) for `mcp-proxy` / `mcp-cli` usage

## 1) Install Alfresco ACS Stack

Use the **alfresco installer** (`alf-cli`) to generate the Docker assets.

1. Download the correct binary for your platform from `alf-cli` v0.1.1 release assets available in https://github.com/aborroy/alf-cli/releases/tag/0.1.1
2. Create a folder and run the program to generate Docker assets

```bash
mv alfresco_darwin_arm64 alf && chmod +x alf

./alf docker-compose

# Example answers:
# ACS version: 25.2
# HTTPS: No
# Server name: localhost
# Admin password: *****
# HTTP port: 8080
# Custom bind IP: No
# FTP: No
# Database: postgres
# Multilingual content: Yes
# Full-text search: Yes
# Solr comms: secret
# Events (ActiveMQ): No
# Addons: (none)
# Docker manages volumes: Yes
```

3. Start Alfresco:

```bash
docker compose up --build
```

Alfresco will be available at [http://localhost:8080/alfresco](http://localhost:8080/alfresco)

## 2) Build & Run the Alfresco MCP Server

Clone the **Python Alfresco MCP Server** (by Steve Reiner) and prepare Docker files

```bash
git clone git@github.com:stevereiner/python-alfresco-mcp-server.git
cd python-alfresco-mcp-server
```

### Create `Dockerfile`

```dockerfile
# syntax=docker/dockerfile:1.7

############################
# Stage 1: Build wheels
############################
FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl ca-certificates && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml ./
RUN python -m pip install --upgrade pip wheel setuptools
COPY . .
RUN python -m pip wheel --wheel-dir /wheels .

############################
# Stage 2: Runtime
############################
FROM python:3.11-slim AS runtime

LABEL org.opencontainers.image.title="python-alfresco-mcp-server" \
      org.opencontainers.image.description="FastMCP 2.0 server for Alfresco Content Services" \
      org.opencontainers.image.url="https://github.com/stevereiner/python-alfresco-mcp-server" \
      org.opencontainers.image.source="https://github.com/stevereiner/python-alfresco-mcp-server" \
      org.opencontainers.image.licenses="Apache-2.0" \
      org.opencontainers.image.vendor="Community" \
      org.opencontainers.image.version="1.1.0" \
      io.docker.mcp.kind="server" \
      io.docker.mcp.transports="stdio,http,sse" \
      io.docker.mcp.default_transport="http" \
      io.docker.mcp.port="8003" \
      io.docker.mcp.docs="README.md"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN useradd -u 10001 -m appuser
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY --from=builder /wheels /wheels
RUN python -m pip install --no-cache-dir /wheels/*

# Adjust if your repo uses a different entrypoint
COPY run_server.py ./run_server.py
COPY README.md ./README.md

ENV ALFRESCO_URL="http://localhost:8080" \
    ALFRESCO_USERNAME="admin" \
    ALFRESCO_PASSWORD="admin" \
    ALFRESCO_VERIFY_SSL="false" \
    LOG_LEVEL="INFO"

EXPOSE 8003
HEALTHCHECK --interval=30s --timeout=5s --retries=5 \
  CMD curl -fsS http://127.0.0.1:8003/health || exit 1

USER appuser
ENV TRANSPORT="http" HOST="0.0.0.0" PORT="8003"

ENTRYPOINT ["python", "run_server.py"]
CMD ["--transport", "http", "--host", "0.0.0.0", "--port", "8003"]
```

### Create `compose.yaml`

```yaml
services:
  alfresco-mcp:
    build:
      context: .
      dockerfile: Dockerfile
    image: ghcr.io/your-org/python-alfresco-mcp-server:1.1.0
    container_name: alfresco-mcp
    environment:
      TRANSPORT: ${TRANSPORT:-http}   # http | stdio | sse
      HOST: 0.0.0.0
      PORT: ${MCP_PORT:-8003}

      # ---- Alfresco connection (from .env) ----
      ALFRESCO_URL: ${ALFRESCO_URL}
      ALFRESCO_USERNAME: ${ALFRESCO_USERNAME}
      ALFRESCO_PASSWORD: ${ALFRESCO_PASSWORD}
      ALFRESCO_VERIFY_SSL: ${ALFRESCO_VERIFY_SSL:-false}
      LOG_LEVEL: ${LOG_LEVEL:-INFO}

    ports:
      - "${MCP_PORT:-8003}:8003"
    healthcheck:
      test: ["CMD-SHELL", "curl -fsS http://127.0.0.1:8003/health || exit 1"]
      interval: 30s
      timeout: 5s
      retries: 5
    restart: unless-stopped
```

### Create `.env`

```ini
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

### Start the server

```bash
docker compose up --build
```

> The MCP Server will be available at [http://localhost:8003/mcp](http://localhost:8003/mcp)

## 3) Configure an MCP Client

There is a number of tools you can use as MCP Client, like Claude Desktop. Steve Reiner provides detailed instructions for this in https://github.com/stevereiner/python-alfresco-mcp-server?tab=readme-ov-file#mcp-client-setup-and-use.

For this lab we use a **local LLM (`gpt-oss`) via Ollama** and the **`mcp-cli`** tool driven through **`mcp-proxy`**:

1. Ensure the model is present:

```bash
ollama list
# Expect:
# gpt-oss:latest  ... 13 GB
```

2. Install `mcp-proxy` and check `mcp-cli`:

```bash
uv tool install mcp-proxy
uvx mcp-cli --help
```

3. Create `server_config.json`:

```json
{
  "mcpServers": {
    "alfresco": {
      "command": "mcp-proxy",
      "args": [
        "--transport", "streamablehttp",
        "http://localhost:8003/mcp"
      ]
    }
  }
}
```

4. Run the CLI:

```bash
uvx mcp-cli chat --server alfresco
```

## 4) Test Scenarios

Use [Steve Reiner sample prompts](https://github.com/stevereiner/python-alfresco-mcp-server/blob/main/prompts-for-claude.md) to validate end-to-end flows (search, fetch docs, metadata, etc.). Example search:

> “Search Alfresco for documents containing *budget*, return at most 5 results.”

Expected: tabular results (title, node ID, type, created date) with follow-up actions (download/view properties).&#x20;

## Troubleshooting

* **MCP can’t reach Alfresco**

  * On macOS/Windows use `ALFRESCO_URL=http://host.docker.internal:8080`.
  * On Linux, use your host IP (e.g., `http://172.17.0.1:8080`), **not** `localhost`, since the container’s `localhost` is not the host network.

* **Port already in use**

  * Change `MCP_PORT` in `.env` and the mapping in `compose.yaml`

* **SSL errors**

  * Set `ALFRESCO_VERIFY_SSL=false` for local non-TLS labs only. Use proper certs in real environments

* **Ollama / model missing**

  * Pull `gpt-oss` before launching the CLI; verify `ollama list`

  ## Running the Chat UI

  Follow these steps to set up and run the Chat UI locally:

  ### 1. Create & Activate a Virtual Environment (Recommended)

  ```bash
  python -m venv .venv
  source .venv/bin/activate
  ```

  ### 2. Install Dependencies

  ```bash
  pip install -r requirements.txt
  ```

  ### 3. Start a Local MCP Server (SSE)

  ```bash
  python example_mcp_server.py --server_type sse --host 127.0.0.1 --port 3001
  ```
  > Leave this terminal running.

  ### 4. Configure Environment for LiteLLM + MCP

  In a new terminal, set the required environment variables:

  ```bash
  export LITELLM_MODEL="openai/gpt-4o-mini"
  # If using a LiteLLM proxy:
  # export LITELLM_BASE="https://api.ai.dev.experience.hyland.com/litellm"
  # Point the app to the MCP SSE endpoint:
  export MCP_SSE_URL="http://127.0.0.1:3001/sse"
  ```

  ### 5. Launch Chainlit

  ```bash
  chainlit run app.py -w
  ```

## Credits & Acknowledgements

* [Alfresco Installer](https://github.com/aborroy/alf-cli) (`alf-cli`) generates ACS Docker assets
* [Python Alfresco MCP Server](https://github.com/stevereiner/python-alfresco-mcp-server) by *Steve Reiner*
* [MCP CLI](https://github.com/chrishayuk/mcp-cli) by *chrishayuk* (used here with `mcp-proxy` setup)