"""Fetch saved form field values for a session."""

from typing import Annotated

from pydantic import Field

from parzley_mcp.instructions import FLOW_GET_FORM_TOOLS, PREREQUISITE_GET_FORM_WITH_SHORTCODE
from parzley_mcp.mcp_tool_doc import join_tool_doc
from parzley_mcp.server import mcp
from parzley_mcp.http_client import _get

_GET_FORM_DATA_BY_SESSION_DESCRIPTION = join_tool_doc(
    "Retrieve saved form field values for a session (`GET /form-data/by-session/{session_id}`).",
    "**Not shortcode lookup:** `session_id` is the **internal session identifier** returned by **`get_form_with_shortcode`** "
    "(typically a UUID string). **Do not** pass a **5- or 6-character shortcode** — crew codes and session "
    "shortcodes are **not** `session_id`. To resolve a shortcode, call **`get_form_with_shortcode(shortcode)`** first, "
    "then use the returned **`session_id`** here.",
    PREREQUISITE_GET_FORM_WITH_SHORTCODE,
    FLOW_GET_FORM_TOOLS,
    "Returns all field values that have been collected/submitted during the session, including which fields the user has filled out so far.",
    "**Returns:** Form data record with id, form_id, user_id, session_id, data (field values), created_at, and updated_at.",
)


@mcp.tool(description=_GET_FORM_DATA_BY_SESSION_DESCRIPTION)
async def get_form_data_by_session(
    session_id: Annotated[
        str,
        Field(
            description=(
                "Internal session ID from get_form_with_shortcode (often a UUID). **Never** a 5- or 6-character shortcode."
            ),
        ),
    ],
) -> dict:
    """Fetch saved values by session_id; full guidance is in the MCP tool description."""
    sid = session_id.strip()
    if len(sid) in (5, 6):
        return {
            "error": (
                "`session_id` must be the identifier from `get_form_with_shortcode` (e.g. UUID), not a 5- or 6-character "
                "**shortcode**. This endpoint is `GET /form-data/by-session/{session_id}`. "
                "**Fix:** call `get_form_with_shortcode` with the user’s shortcode, then pass the returned `session_id`."
            )
        }
    return await _get(f"/form-data/by-session/{sid}", auth=False)
