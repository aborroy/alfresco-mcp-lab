# Alfresco MCP Lab

Available in https://github.com/aborroy/alfresco-mcp-lab

# Components

* Community project for Alfresco MCP Server: https://github.com/aborroy/alfresco-mcp-lab
* Alfresco Installer: https://github.com/aborroy/alf-cli
* [Optional] MCP CLI: https://github.com/chrishayuk/mcp-cli

# Installing

## Alfresco ACS Stack

Download the right binary for your computer from Assets in 

https://github.com/aborroy/alf-cli/releases/tag/0.1.1

Create a folder named `alfresco` and run the program to create the Docker Assets to run Alfresco Community

```bash
mv alfresco_darwin_arm64 alf && chmod +x alf

./alf docker-compose

Which ACS version do you want to use?: 25.2
Do you want to enable HTTPS?: No
What is the name of your server?: localhost
Choose the password for your 'admin' user: •••••
What HTTP port do you want to use (all the services are using the same port)?: 8080
Do you want to specify a custom binding IP for HTTP?: No
Do you want to use FTP (default port is 2121)?: No
Which Database Engine do you want to use?: postgres
Are you using content in different languages (this is the most common scenario)?: Yes
Do you want to search in the content of the documents?: Yes
Which Solr communication method do you want to use?: secret
Do you want to use the Events service (ActiveMQ)?: No
Select the addons to be installed: (none)
Do you want Docker to manage volume storage (recommended when dealing with permission issues)?: Yes
```

Start Alfresco

```bash
docker compose up --build
```

> Alfresco will be ready listening in http://localhost:8080/alfresco

## Alfresco MCP Server

Clone the Alfresco MCP Server by Steve Reiner

```bash
git clone git@github.com:stevereiner/python-alfresco-mcp-server.git
cd python-alfresco-mcp-server
```

Create the Dockerfile for the project

```bash
echo "# syntax=docker/dockerfile:1.7

############################
# Stage 1: Build wheels
############################
FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# System deps (build)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl ca-certificates && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy project metadata first for layer caching
COPY pyproject.toml ./
# If you have a requirements.txt, uncomment the next line:
# COPY requirements.txt ./

# Build wheels for the project and deps
RUN python -m pip install --upgrade pip wheel setuptools

# Copy the full source
COPY . .

# Build a wheel for the project (and pre-resolve deps into a local wheelhouse)
RUN python -m pip wheel --wheel-dir /wheels .

############################
# Stage 2: Runtime
############################
FROM python:3.11-slim AS runtime

# --- OCI + MCP Catalog labels (fill fields as needed) ---
LABEL org.opencontainers.image.title="python-alfresco-mcp-server" \
      org.opencontainers.image.description="FastMCP 2.0 server for Alfresco Content Services" \
      org.opencontainers.image.url="https://github.com/stevereiner/python-alfresco-mcp-server" \
      org.opencontainers.image.source="https://github.com/stevereiner/python-alfresco-mcp-server" \
      org.opencontainers.image.licenses="Apache-2.0" \
      org.opencontainers.image.vendor="Community" \
      org.opencontainers.image.version="1.1.0" \
      # Suggested keys for Docker MCP Catalog
      io.docker.mcp.kind="server" \
      io.docker.mcp.transports="stdio,http,sse" \
      io.docker.mcp.default_transport="http" \
      io.docker.mcp.port="8003" \
      io.docker.mcp.docs="README.md"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Security: non-root user
RUN useradd -u 10001 -m appuser

# System deps (runtime)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install built wheels
COPY --from=builder /wheels /wheels
RUN python -m pip install --no-cache-dir /wheels/*

# Copy only what’s needed at runtime (scripts, docs for reference)
COPY run_server.py ./run_server.py
COPY README.md ./README.md

# Default environment (override in compose or docker run)
# These map to alfresco_mcp_server.config (env-first precedence)
ENV ALFRESCO_URL="http://localhost:8080" \
    ALFRESCO_USERNAME="admin" \
    ALFRESCO_PASSWORD="admin" \
    ALFRESCO_VERIFY_SSL="false" \
    LOG_LEVEL="INFO"

# Expose HTTP/SSE port used by FastMCP when not using stdio
EXPOSE 8003

# Healthcheck (HTTP transport)
HEALTHCHECK --interval=30s --timeout=5s --retries=5 CMD curl -fsS http://127.0.0.1:8003/health || exit 1

USER appuser

# Default: HTTP transport on 0.0.0.0:8003
# Change via: --env TRANSPORT=stdio or sse (see compose example)
ENV TRANSPORT="http" HOST="0.0.0.0" PORT="8003"

ENTRYPOINT ["python", "run_server.py"]
CMD ["--transport", "http", "--host", "0.0.0.0", "--port", "8003"]

" >> Dockerfile
```

Create the Docker Compose asset to run it in Compose

```bash
echo "services:
  alfresco-mcp:
    build:
      context: .
      dockerfile: Dockerfile
    image: ghcr.io/your-org/python-alfresco-mcp-server:1.1.0
    container_name: alfresco-mcp
    environment:
      # Transport: http | stdio | sse
      TRANSPORT: "${TRANSPORT:-http}"
      HOST: "0.0.0.0"
      PORT: "${MCP_PORT:-8003}"

      # ---- Alfresco connection (from .env) ----
      ALFRESCO_URL: "${ALFRESCO_URL}"
      ALFRESCO_USERNAME: "${ALFRESCO_USERNAME}"
      ALFRESCO_PASSWORD: "${ALFRESCO_PASSWORD}"
      # Optional tuning
      ALFRESCO_VERIFY_SSL: "${ALFRESCO_VERIFY_SSL:-false}"
      LOG_LEVEL: "${LOG_LEVEL:-INFO}"

    ports:
      - "${MCP_PORT:-8003}:8003"
    healthcheck:
      test: ["CMD-SHELL", "curl -fsS http://127.0.0.1:8003/health || exit 1"]
      interval: 30s
      timeout: 5s
      retries: 5
    restart: unless-stopped

" >> compose.yaml
```

Create the environment variables

```bash
echo "# Docker MCP server port (external)
MCP_PORT=8003

# Transport mode for the FastMCP server (http | stdio | sse)
TRANSPORT=http

# ---- Alfresco connection ----
# If you run Alfresco locally, include protocol and port:
#   http://host.docker.internal:8080   (Mac/Windows Docker Desktop)
#   http://<your-host-ip>:8080         (Linux or remote)
ALFRESCO_URL=http://host.docker.internal:8080
ALFRESCO_USERNAME=admin
ALFRESCO_PASSWORD=admin
ALFRESCO_VERIFY_SSL=false

# Logging
LOG_LEVEL=INFO" >> .env
```

The project is now ready to be started using Docker Compose, just type

```bash
docker compose up --build
```

The MCP Server will be ready listening in http://localhost:8083/mcp

## MCP Client

There is a number of tools you can use as MCP Client, like Claude Desktop. Steve Reiner provides detailed instructions for this in https://github.com/stevereiner/python-alfresco-mcp-server?tab=readme-ov-file#mcp-client-setup-and-use.

For this Lab we're using a local LLM (`gpt-oss`) with Ollama. This is why we're using the project https://github.com/chrishayuk/mcp-cli.

Be sure that Ollama is running and `gpt-oss` is available

```bash
ollama list
gpt-oss:latest              aa4295ac10c3    13 GB
```

Install `mcp-proxy` to access MCP Server using HTTP protocol

```bash
uv tool install mcp-proxy
```

Install the `mcp-cli`

```bash
uvx mcp-cli --help
```

Create the configuration file for `mcp-cli`

```bash
echo "$ cat -p server_config.json
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
}" >> server_config.json
```

Run the MCP Client using the Alfresco MCP Server configuration

```bash
uvx mcp-cli chat --server alfresco
```

# Testing

Once everything is ready, you can test some of the prompts provided by Steve Reiner in https://github.com/stevereiner/python-alfresco-mcp-server/blob/main/prompts-for-claude.md.

For instance:

```bash
> I need to search for documents in Alfresco. Can you search for:
- Documents containing "budget"
- Maximum 5 results

─────────────────────────────── Assistant ───────────────────────────────

Here are the first five documents that contain the word “budget”:                                                                                                                                 
                                                                                                                                                                                                   │
   #   Title / File                           Node ID                                Type         Created                              
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   1   budget.xls                             5fa74ad3-9b5b-461b-9df5-de407f1f4fe7   cm:content   2011‑02‑15 21:35:26
   2   42fcbae6-b1fe-4028-9f85-9ad7f81a8e3b   db31dce5-2469-4c68-8641-9becad64a756   dl:issue     2011‑02‑15 22:18:03
   3   Meetings                               1373739a-2849-4647-9e97-7a4e05cc5841   cm:content   2011‑02‑15 21:50:49
   4   Milestones                             3c73aace-9f54-420d-a1c0-c54b6a116dcf   cm:content   2011‑02‑15 21:59:31
   5   Meeting Notes 2011‑01‑27.doc           f3bb5d08-9fd1-46da-a94a-97f20f1ef208   cm:content   2011‑02‑24 16:16:37
 
 If you’d like to see more details about any of these items (e.g., download the file, view properties, or open it in Alfresco), just let me know the node ID and the action you’d like to perform.
```