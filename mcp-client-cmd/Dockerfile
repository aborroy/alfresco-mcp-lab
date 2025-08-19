# syntax=docker/dockerfile:1.7

FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim

ENV UV_LINK_MODE=copy \
    PATH="/root/.local/bin:${PATH}" \
    # Defaults (override in compose)
    LLM_PROVIDER=ollama \
    LLM_MODEL=gpt-oss \
    OLLAMA_FORWARD_TARGET=host.docker.internal:11434 \
    OLLAMA_LOCAL_URL=http://127.0.0.1:11434

WORKDIR /work

# System deps
RUN apt-get update \
 && apt-get install -y --no-install-recommends socat ca-certificates curl \
 && rm -rf /var/lib/apt/lists/*

# Tools
RUN --mount=type=cache,target=/root/.cache/uv \
    uv tool install mcp-cli \
 && uv tool install mcp-proxy

# Optional: include your server config (or mount it via a volume)
COPY server_config.json /work/server_config.json

# Entrypoint wrapper: start socat forwarder, write ~/.chuk_llm/config.yaml, exec mcp-cli
RUN cat >/usr/local/bin/entrypoint.sh <<'SH'
#!/bin/sh
set -eu

# Allow runtime overrides
: "${LLM_PROVIDER:=ollama}"
: "${LLM_MODEL:=gpt-oss}"
: "${OLLAMA_FORWARD_TARGET:=host.docker.internal:11434}"
: "${OLLAMA_LOCAL_URL:=http://127.0.0.1:11434}"

# 1) Forward container 127.0.0.1:11434 -> host.docker.internal:11434
socat TCP-LISTEN:11434,fork,reuseaddr TCP:"${OLLAMA_FORWARD_TARGET}" &
SOCAT_PID=$!

# 2) Generate config on each start
mkdir -p /root/.chuk_llm
API_BASE="${OLLAMA_LOCAL_URL}"
case "$API_BASE" in http://*|https://*) ;; *) API_BASE="http://${API_BASE}";; esac

printf "%s:\n  api_base: %s\n  default_model: %s\n" \
  "${LLM_PROVIDER}" "${API_BASE}" "${LLM_MODEL}" > /root/.chuk_llm/config.yaml

echo "---- /root/.chuk_llm/config.yaml ----"
cat /root/.chuk_llm/config.yaml
echo "-------------------------------------"
echo "Forwarding 127.0.0.1:11434 -> ${OLLAMA_FORWARD_TARGET} (pid ${SOCAT_PID})"

# 3) Run mcp-cli (pass through any args from CMD)
exec uvx mcp-cli "$@"
SH

RUN chmod +x /usr/local/bin/entrypoint.sh

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["chat", "--server", "alfresco", "--config-file", "/work/server_config.json"]