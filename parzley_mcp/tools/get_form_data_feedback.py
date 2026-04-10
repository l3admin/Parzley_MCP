"""Feedback on form data quality, gaps, and validation for the current session (not concierge dialogue)."""

from typing import Annotated

from pydantic import Field

from parzley_mcp.instructions import FLOW_PARZLEY_MESSAGE_TURN, PREREQUISITE_GET_FORM_WITH_SHORTCODE
from parzley_mcp.mcp_tool_doc import join_tool_doc
from parzley_mcp.server import mcp
from parzley_mcp.http_client import _get

_GET_FORM_DATA_FEEDBACK_DESCRIPTION = join_tool_doc(
    "Retrieve **feedback on the current session’s form data** — errors, shortfalls, missing fields, "
    "validation issues, and answer-quality notes. This complements the concierge in `parzley_message_turn`, "
    "which guides *what to ask next*; this call surfaces *what is wrong or incomplete* in what has been "
    "captured so far.",
    PREREQUISITE_GET_FORM_WITH_SHORTCODE,
    FLOW_PARZLEY_MESSAGE_TURN,
    "**Cadence:** Call after every **second** `parzley_message_turn` (after the 2nd, 4th, 6th, …), as in the flow block above.",
    "**Returns:** { status, text_output, type, session_id, _id, created_at, updated_at }",
)


@mcp.tool(description=_GET_FORM_DATA_FEEDBACK_DESCRIPTION)
async def get_form_data_feedback(
    session_id: Annotated[
        str,
        Field(
            description="Session ID from get_form_with_shortcode (same as used in parzley_message_turn). Not a shortcode.",
        ),
    ],
) -> dict:
    """Structured feedback on saved data; full guidance is in the MCP tool description."""
    return await _get(f"/editor-suggestion/{session_id}", auth=False)
