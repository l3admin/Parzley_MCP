"""Build MCP tool descriptions for @mcp.tool(description=...).

Python does not assign a docstring when the first statement is an f-string (triple-quoted f-string),
so FastMCP was emitting tools with description=None. Use join_tool_doc with plain strings instead of
f-string \"docstrings\" on tool functions.
"""


def join_tool_doc(*parts: str) -> str:
    return "\n\n".join(p.strip() for p in parts if p and p.strip())
