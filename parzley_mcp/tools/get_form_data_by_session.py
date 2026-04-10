"""Fetch saved form field values for a session."""

from parzley_mcp.instructions import FLOW_GET_FORM_TOOLS
from parzley_mcp.server import mcp
from parzley_mcp.http_client import _get


@mcp.tool()
async def get_form_data_by_session(session_id: str) -> dict:
    f"""
    Retrieve the form data filled by the user for a given session.

    {FLOW_GET_FORM_TOOLS}

    Returns all field values that have been collected/submitted during
    the session, including which fields the user has filled out so far.

    Args:
        session_id: The session ID returned by start_session.

    Returns:
        Form data record with id, form_id, user_id, session_id, data (field values),
        created_at, and updated_at.
    """
    return await _get(f"/form-data/by-session/{session_id}", auth=False)
