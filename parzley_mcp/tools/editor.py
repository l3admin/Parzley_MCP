"""
Editor suggestion tool — retrieve structured document output for a session.
"""

from parzley_mcp.server import mcp
from parzley_mcp.http_client import _get


@mcp.tool()
async def get_editor_suggestion(session_id: str) -> dict:
    """
    Retrieve the latest editor suggestion for a session.

    After a `send_message` turn, call this to get the structured document
    output that represents the current state of the form being filled.

    Args:
        session_id: The session ID from `start_session` (same as used in `send_message`).

    Returns:
        { status, text_output, type, session_id, _id, created_at, updated_at }
    """
    return await _get(f"/editor-suggestion/{session_id}", auth=False)

