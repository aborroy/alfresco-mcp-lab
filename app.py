# app.py
import os
import json
import chainlit as cl
from chainlit.input_widget import Select, TextInput

try:
    import litellm  # type: ignore
except Exception:  # pragma: no cover
    litellm = None  # fallback if not installed directly
from dotenv import load_dotenv  # .env support

# LlamaIndex (FunctionAgent + events)
from llama_index.core.agent.workflow import (
    FunctionAgent,
    AgentStream,
    ToolCall,
    ToolCallResult,
)
from llama_index.core.llms import ChatMessage

# LiteLLM LLM wrapper for LlamaIndex
# pip install llama-index-llms-litellm
from llama_index.llms.litellm import LiteLLM

# MCP ToolSpec & Client
# pip install llama-index-tools-mcp
from llama_index.tools.mcp import BasicMCPClient, McpToolSpec


# ---------- Config helpers ----------
def _env(name: str, default: str | None = None) -> str | None:
    v = os.getenv(name)
    return v if v is not None else default


# You can run an SSE MCP server (see mcp_server.py below) or use stdio:
#   SSE:   export MCP_SSE_URL="http://127.0.0.1:3001/sse"
#   STDIO: export MCP_CMD="python"; export MCP_ARGS="mcp_server.py --server_type=stdio"
#
# LiteLLM config (either direct or via proxy):
#   export LITELLM_MODEL="openai/gpt-4o-mini"   # or "anthropic/claude-3-5-sonnet" etc
#   export LITELLM_API_KEY="..."                # if your proxy expects it; or OPENAI_API_KEY etc
#   export LITELLM_BASE="http://127.0.0.1:4000" # LiteLLM proxy base, optional
#
# Load .env early (if present) so downstream _env lookups work.
load_dotenv(override=False)

# Optional: drop unsupported params automatically for providers (e.g., Bedrock Claude)
if litellm is not None:
    try:
        litellm.drop_params = (
            True  # instruct LiteLLM to silently omit unsupported params
        )
    except Exception:
        pass

# System prompt tweak:
SYSTEM_PROMPT = _env(
    "SYSTEM_PROMPT",
    "You are a helpful assistant. Use MCP tools when appropriate. "
    "Explain your reasoning briefly",
)


async def build_agent(model: str = None, system_prompt: str = None) -> FunctionAgent:
    # ---- LLM via LiteLLM (works with LiteLLM proxy or direct provider keys) ----
    # Docs: https://docs.llamaindex.ai/.../llms/litellm/
    model = model or _env(
        "LITELLM_MODEL", "litellm_proxy/anthropic.claude-sonnet-4-20250514-v1:0"
    )
    # Allow both LITELLM_BASE (preferred) and legacy LITELLM_API_BASE
    api_base = _env("LITELLM_BASE", _env("LITELLM_API_BASE", None))
    api_key = _env("LITELLM_API_KEY", None)

    llm = LiteLLM(model=model, api_base=api_base, api_key=api_key)

    # ---- Connect MCP tools via streamable HTTP only ----
    # Server now exposes a unified streaming endpoint at /mcp (no separate /sse path).
    # Primary env var: MCP_URL. We allow legacy MCP_SSE_URL for backward compatibility.
    mcp_url = _env("MCP_URL", _env("MCP_SSE_URL", "http://127.0.0.1:3001/mcp"))

    if not (mcp_url.startswith("http://") or mcp_url.startswith("https://")):
        raise ValueError(
            "MCP_URL must be an HTTP/HTTPS URL (got: %s). Update your .env." % mcp_url
        )

    mcp_client = BasicMCPClient(mcp_url)

    mcp_tool_spec = McpToolSpec(client=mcp_client)
    tools = await mcp_tool_spec.to_tool_list_async()

    # Use provided system prompt or fall back to env/default
    effective_system_prompt = system_prompt or SYSTEM_PROMPT

    # ---- FunctionAgent with streaming enabled ----
    # Docs: FunctionAgent & events (AgentStream, ToolCall, ToolCallResult)
    agent = FunctionAgent(
        tools=tools,
        llm=llm,
        system_prompt=effective_system_prompt,
    )
    return agent


@cl.on_chat_start
async def on_start():
    # Show settings UI first
    settings = await cl.ChatSettings(
        [
            Select(
                id="Model",
                label="LLM Model",
                values=[
                    "litellm_proxy/anthropic.claude-sonnet-4-20250514-v1:0",
                    "litellm_proxy/anthropic.claude-3-5-sonnet-20241022-v2:0",
                ],
                initial_index=0,
            ),
            TextInput(
                id="SystemPrompt",
                label="System Prompt",
                initial=SYSTEM_PROMPT,
                multiline=True,
            ),
        ]
    ).send()

    # Build agent with selected settings
    selected_model = settings["Model"]
    selected_system_prompt = settings["SystemPrompt"]

    agent = await build_agent(
        model=selected_model, system_prompt=selected_system_prompt
    )
    cl.user_session.set("agent", agent)
    cl.user_session.set("model", selected_model)
    cl.user_session.set("system_prompt", selected_system_prompt)
    # Initialize empty chat history
    cl.user_session.set("chat_history", [])

    await cl.Message(
        author="system",
        content=(
            "🤝 Ready! Send me a message "
            "\n\n"
            f"• Model: `{selected_model}`\n"
            f"• MCP URL: `{_env('MCP_URL', _env('MCP_SSE_URL', 'http://127.0.0.1:3001/mcp'))}`"
        ),
    ).send()


@cl.on_settings_update
async def on_settings_update(settings):
    """Handle settings changes and rebuild agent"""
    selected_model = settings["Model"]
    selected_system_prompt = settings["SystemPrompt"]

    # Rebuild agent with new settings
    agent = await build_agent(
        model=selected_model, system_prompt=selected_system_prompt
    )
    cl.user_session.set("agent", agent)
    cl.user_session.set("model", selected_model)
    cl.user_session.set("system_prompt", selected_system_prompt)
    # Reset chat history when settings change
    cl.user_session.set("chat_history", [])

    await cl.Message(
        author="system",
        content=f"✅ Settings updated!\n• Model: `{selected_model}`\n• System prompt updated",
    ).send()


@cl.on_message
async def on_message(message: cl.Message):
    agent: FunctionAgent = cl.user_session.get("agent")
    if agent is None:
        agent = await build_agent()
        cl.user_session.set("agent", agent)

    # Get chat history and add current user message
    chat_history = cl.user_session.get("chat_history", [])
    chat_history.append({"role": "user", "content": message.content})

    # Convert chat history to LlamaIndex ChatMessage format
    llama_messages = []
    for msg in chat_history:
        llama_messages.append(ChatMessage(role=msg["role"], content=msg["content"]))

    # Outgoing assistant message (we'll stream tokens into it)
    out = cl.Message(content="")
    await out.send()

    # Keep track of tool steps by tool_id so we can append outputs later
    tool_steps: dict[str, cl.Step] = {}

    # Start the run WITH chat history
    handler = agent.run(user_msg=message.content, chat_history=llama_messages)

    async for event in handler.stream_events():
        # LLM token delta
        if isinstance(event, AgentStream):
            await out.stream_token(event.delta)

        # Tool call started
        elif isinstance(event, ToolCall):
            step = cl.Step(
                name=f"🛠️ {event.tool_name}",
                type="tool",
            )
            step.input = json.dumps(event.tool_kwargs, indent=2)
            await step.send()
            tool_steps[event.tool_id] = step

        # Tool call finished
        elif isinstance(event, ToolCallResult):
            step = tool_steps.get(event.tool_id)
            if step:
                # tool_output may be a ToolOutput with .content or raw str/obj
                output = getattr(event.tool_output, "content", event.tool_output)
                try:
                    step.output = (
                        output
                        if isinstance(output, str)
                        else json.dumps(output, indent=2, ensure_ascii=False)
                    )
                except Exception:
                    step.output = str(output)
                await step.update()

    # Finalize the run, display the consolidated assistant response (if any)
    result = await handler  # returns AgentOutput (has .response)
    if getattr(result, "response", None):
        final_text = str(result.response)
        # Ensure the last chunk is printed (in case streaming was partial)
        await out.stream_token("")
        out.content = final_text
        await out.update()

        # Add assistant response to chat history
        chat_history.append({"role": "assistant", "content": final_text})
        cl.user_session.set("chat_history", chat_history)
