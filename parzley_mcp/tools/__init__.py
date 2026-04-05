"""
Import all tool modules so their @mcp.tool() decorators are registered
on the shared FastMCP instance.
"""

from parzley_mcp.tools import session  # noqa: F401
from parzley_mcp.tools import chat     # noqa: F401
from parzley_mcp.tools import editor   # noqa: F401
from parzley_mcp.tools import content  # noqa: F401
from parzley_mcp.tools import display  # noqa: F401

