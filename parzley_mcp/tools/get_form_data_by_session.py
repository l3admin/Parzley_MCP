"""Fetch saved form field values for a session."""

from parzley_mcp.instructions import FLOW_GET_FORM_TOOLS, PREREQUISITE_START_SESSION
from parzley_mcp.server import mcp
from parzley_mcp.http_client import _get


@mcp.tool()
async def get_form_data_by_session(session_id: str) -> dict:
    f"""
    Retrieve saved form field values for a session (`GET /form-data/by-session/{{session_id}}`).

    **Not shortcode lookup:** `session_id` is the **internal session identifier** returned by **`start_session`**
    (typically a UUID string). **Do not** pass a **5- or 6-character shortcode** — crew codes and session
    shortcodes are **not** `session_id`. To resolve a shortcode, call **`start_session(shortcode)`** first,
    then use the returned **`session_id`** here.

    {PREREQUISITE_START_SESSION}

    {FLOW_GET_FORM_TOOLS}

    Returns all field values that have been collected/submitted during
    the session, including which fields the user has filled out so far.

    Args:
        session_id: From **`start_session`** → `session_id` (never a shortcode).

    Returns:
        Form data record with id, form_id, user_id, session_id, data (field values),
        created_at, and updated_at.
    """
    sid = session_id.strip()
    if len(sid) in (5, 6):
        return {
            "error": (
                "`session_id` must be the identifier from `start_session` (e.g. UUID), not a 5- or 6-character "
                "**shortcode**. This endpoint is `GET /form-data/by-session/{session_id}`. "
                "**Fix:** call `start_session` with the user’s shortcode, then pass the returned `session_id`."
            )
        }
    return await _get(f"/form-data/by-session/{sid}", auth=False)
