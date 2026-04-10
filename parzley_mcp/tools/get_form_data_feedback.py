"""Feedback on form data quality, gaps, and validation for the current session (not concierge dialogue)."""

from parzley_mcp.instructions import FLOW_PARZLEY_MESSAGE_TURN
from parzley_mcp.server import mcp
from parzley_mcp.http_client import _get


@mcp.tool()
async def get_form_data_feedback(session_id: str) -> dict:
    f"""
    Retrieve **feedback on the current session’s form data** — errors, shortfalls, missing fields,
    validation issues, and answer-quality notes. This complements the concierge in `parzley_message_turn`,
    which guides *what to ask next*; this call surfaces *what is wrong or incomplete* in what has been
    captured so far.

    {FLOW_PARZLEY_MESSAGE_TURN}

    **Cadence:** Call after every **second** `parzley_message_turn` (after the 2nd, 4th, 6th, …), as in the flow block above.

    Args:
        session_id: The session ID from `start_session` (same as used in `parzley_message_turn`).

    Returns:
        {{ status, text_output, type, session_id, _id, created_at, updated_at }}
    """
    return await _get(f"/editor-suggestion/{session_id}", auth=False)
