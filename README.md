# Alfresco MCP Lab

> A reproducible laboratory to experiment with the **Model Context Protocol (MCP)** against **Alfresco Community Edition** using Docker

## Architecture

```                                                                                                          
    ┌────────────────┐ 
    │                │ 
    │     Ollama     │ 
    │                │ 
    └────────────────┘                                                                                                           
            |                                                                                                
            | 11434                                                                                                
            |                                                                                                 
    ┌────────────────┐        ┌───────────────────┐        ┌───────────────────┐                             
    │                │        │                   │        │                   │                             
    │                │  8003  │                   │  8080  │                   │                             
    │   MCP CLIENT   │________│    MCP SERVER     │________│     ALFRESCO      │                             
    │      CMD       │        │                   │        │                   │                             
    │                │        │                   │        │                   │                             
    └────────────────┘        └───────────────────┘        └───────────────────┘                             
                                       |                                                                                    
                                       |                                                                                     
                                       |                                                                                      
    ┌────────────────┐                 | 8003
    │                │                 |
    │                │                 |
    │   MCP CLIENT   │_________________| 
    │      UI        │ 
    │                │ 
    └──────8000──────┘                                                                                                                  
```

* [ALFRESCO](alfresco): Default installation for ACS Community Edition available at [http://localhost:8080/alfresco](http://localhost:8080/alfresco)
* [MCP SERVER](mcp-server): [Python Alfresco MCP Server](https://github.com/stevereiner/python-alfresco-mcp-server) by *Steve Reiner* avaialable in available at [http://localhost:8003/mcp](http://localhost:8003/mcp)
* [MCP CLIENT - CMD](mcp-client-cmd): [MCP CLI](https://github.com/chrishayuk/mcp-cli) by *chrishayuk* (used here with `mcp-proxy` setup)
  * [Ollama](https://ollama.com/): a lightweight open-source runtime that lets you run, manage, and interact with large language models locally on your computer
* [MCP CLIENT - UI](mcp-client-ui): [Chainlit](https://chainlit.io) app using by default Claude Sonnet as service, using [LiteLLM](https://www.litellm.ai) for model access

## Prerequisites

* Docker and Docker Compose
* For the CLI
  * Ollama with the `gpt-oss` model pulled (around 13 GB)
* For the UI
  * LITELLM_API_KEY as environment variable used to store the API key for authenticating LLM requests

## Backend deployment

Alfresco and MCP Server deployment for Docker Compose is available in `compose.yaml`

```bash
cat compose.yaml

include:
  - mcp-server/compose.yaml
  - alfresco/compose.yaml
```

They can be started using the regular Docker Compose command:

```bash
docker compose up --build
```

Once started, following services will be available:

* Alfresco Repository: http://localhost:8080/alfresco
* MCP Server: http://localhost:8003/mcp

## CLI usage

There is a number of tools you can use as MCP Client, like Claude Desktop. Steve Reiner provides detailed instructions for this in https://github.com/stevereiner/python-alfresco-mcp-server?tab=readme-ov-file#mcp-client-setup-and-use.

### MCP Client using CMD

For this client we use a **local LLM (`gpt-oss`) via Ollama**

Ensure `ollama` is running and the model is present:

```bash
ollama list
# Expect:
# gpt-oss:latest  ... 13 GB
```

Run the CLI using following command: 

```bash
cd mcp-client-cmd
docker compose run --rm mcp-client
```

Type a sample prompt:

```bash
> Search Alfresco for documents containing "budget", return at most 5 results.
```

> You may use Steve Reiner sample prompts](https://github.com/stevereiner/python-alfresco-mcp-server/blob/main/prompts-for-claude.md) to validate end-to-end flows (search, fetch docs, metadata, etc.).

### MCP Client using UI

Create a `.env` file from `.env.example` with `LITELLM` credentials:

```bash
copy .env.example .env

cat .env

LITELLM_API_KEY=123456
LITELLM_API_BASE=https://api.ai.dev.experience.hyland.com/litellm
LITELLM_MODEL=litellm_proxy/anthropic.claude-sonnet-4-20250514-v1:0
MCP_URL=http://host.docker.internal:8083/mcp

ALFRESCO_URL=http://host.docker.internal:8080
ALFRESCO_USERNAME=admin
ALFRESCO_PASSWORD=admin
ALFRESCO_VERIFY_SSL=false

# Logging
LOG_LEVEL=INFO
```

Run the UI using following command:

```bash
docker compose up --build
```

The application will be available in http://localhost:8000

![MCP UI Sample Prompt](docs/mcp-ui-sample.png)

## Additional information

If you're interested in building every tool from scratch, follow this [instructions](doc/instrutions.md)

## Credits & Acknowledgements

* [Alfresco Installer](https://github.com/aborroy/alf-cli) (`alf-cli`) generates ACS Docker assets
* [Python Alfresco MCP Server](https://github.com/stevereiner/python-alfresco-mcp-server) by *Steve Reiner*
* [MCP CLI](https://github.com/chrishayuk/mcp-cli) by *chrishayuk* (used here with `mcp-proxy` setup)
* MCP CLI UI uses [chainlit](https://chainlit.io)