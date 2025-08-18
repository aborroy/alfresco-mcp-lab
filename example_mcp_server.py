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
    # Streamable HTTP transport → endpoint at http://0.0.0.0:3001/mcp
    # Using 0.0.0.0 allows Docker containers to connect from host.docker.internal
    mcp.run(transport="http", host="0.0.0.0", port=3001)
