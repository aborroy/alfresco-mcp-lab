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

# Remove macOS quarantine flag (if on MacOS)
xattr -d com.apple.quarantine ./alf

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
Chat App will be available at [http://localhost:8000/](http://localhost:8000)

## 2) Build & Run the Alfresco MCP Server

We are using Steve Reiner's Python Alfresco MCP

* [Python Alfresco MCP Server (GitHub)](https://github.com/stevereiner/python-alfresco-mcp-server)

### Clone the Alfresco MCP Server

From within this repository directory, clone the Alfresco MCP server:

```bash
git clone https://github.com/stevereiner/python-alfresco-mcp-server.git
```

### Create `.env`

```ini
# ---- LLM Connection ---- #
LITELLM_API_KEY=<your-api-key>
LITELLM_API_BASE=https://api.ai.dev.experience.hyland.com/litellm
LITELLM_MODEL=litellm_proxy/anthropic.claude-sonnet-4-20250514-v1:0
# MCP server URL (we serve streamable HTTP on /mcp)
MCP_URL=http://127.0.0.1:3001/mcp

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

## Optional - Running the Chat UI Outside of Docker

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
export LITELLM_MODEL="litellm_proxy/anthropic.claude-sonnet-4-20250514-v1:0"
# If using a LiteLLM proxy:
# export LITELLM_BASE="https://api.ai.dev.experience.hyland.com/litellm"
# Point the app to the MCP SSE endpoint:
export MCP_URL=http://127.0.0.1:3001/mcp
```

### 5. Launch Chainlit

```bash
python -m chainlit run app.py -w
```

## Credits & Acknowledgements

* [Alfresco Installer](https://github.com/aborroy/alf-cli) (`alf-cli`) generates ACS Docker assets
* [Python Alfresco MCP Server](https://github.com/stevereiner/python-alfresco-mcp-server) by *Steve Reiner*
* [MCP CLI](https://github.com/chrishayuk/mcp-cli) by *chrishayuk* (used here with `mcp-proxy` setup)