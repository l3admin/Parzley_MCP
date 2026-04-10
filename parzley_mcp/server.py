"""
FastMCP application instance with system-level instructions.

Instruction text lives in ``parzley_mcp.instructions`` so the same blocks can be
reused in tool docstrings for clients that do not surface server instructions.
"""

from fastmcp import FastMCP

from parzley_mcp.instructions import SERVER_INSTRUCTIONS

mcp = FastMCP(
    name="Parzley",
    instructions=SERVER_INSTRUCTIONS,
)
