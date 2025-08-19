# syntax=docker/dockerfile:1.7

############################
# Stage 1: Build wheels
############################
FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Install toolchain + git for cloning
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl ca-certificates git && \
    rm -rf /var/lib/apt/lists/*

# Allow overriding repo/ref at build time
ARG REPO_URL=https://github.com/stevereiner/python-alfresco-mcp-server.git
ARG REPO_REF=main

# Upgrade pip tooling
RUN python -m pip install --upgrade pip wheel setuptools

# Clone source via SSH (requires BuildKit and --ssh)
# Then build wheels from the repo
WORKDIR /src
RUN --mount=type=ssh \
    git clone "$REPO_URL" . && \
    git checkout "$REPO_REF" && \
    python -m pip wheel --wheel-dir /wheels .

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

# Install the built wheels
COPY --from=builder /wheels /wheels
RUN python -m pip install --no-cache-dir /wheels/*

# Bring in helper/entry docs from the cloned repo
COPY --from=builder /src/run_server.py ./run_server.py
COPY --from=builder /src/README.md ./README.md

ENV ALFRESCO_URL="http://localhost:8080" \
    ALFRESCO_USERNAME="admin" \
    ALFRESCO_PASSWORD="admin" \
    ALFRESCO_VERIFY_SSL="false" \
    LOG_LEVEL="INFO"

EXPOSE 8003

USER appuser
ENV TRANSPORT="http" HOST="0.0.0.0" PORT="8003"

ENTRYPOINT ["python", "run_server.py"]
CMD ["--transport", "http", "--host", "0.0.0.0", "--port", "8003"]