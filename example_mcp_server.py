# mcp_server.py
from fastmcp import FastMCP

mcp = FastMCP(
    name="demo-mcp",
)


@mcp.tool
def add(a: float, b: float) -> float:
    """Add two numbers and return the sum."""
    return a + b


@mcp.tool
def echo(text: str) -> str:
    """Echo back the provided text."""
    return text


if __name__ == "__main__":
    # Streamable HTTP transport → endpoint at http://127.0.0.1:3001/mcp
    mcp.run(transport="http", host="127.0.0.1", port=3001)
