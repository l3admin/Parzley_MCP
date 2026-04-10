"""
Import all tool modules so their @mcp.tool() decorators register on the shared FastMCP instance.
"""

from parzley_mcp.tools import analyse_content  # noqa: F401
from parzley_mcp.tools import register_respondent  # noqa: F401
from parzley_mcp.tools import extract_content  # noqa: F401
from parzley_mcp.tools import get_form_data_feedback  # noqa: F401
from parzley_mcp.tools import get_form_definition  # noqa: F401
from parzley_mcp.tools import get_form_data_by_session  # noqa: F401
from parzley_mcp.tools import parzley_message_turn  # noqa: F401
from parzley_mcp.tools import start_session  # noqa: F401
from parzley_mcp.tools import submit_form_data  # noqa: F401
