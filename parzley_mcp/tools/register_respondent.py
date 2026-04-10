"""Register a respondent (name + email) for the current Parzley session."""

import httpx

from parzley_mcp.instructions import (
    PREREQUISITE_START_SESSION,
    PROACTIVE_COMMUNICATION,
    REGISTRATION,
)
from parzley_mcp.server import mcp
from parzley_mcp.http_client import _post


@mcp.tool()
async def register_respondent(
    session_id: str,
    first_name: str,
    last_name: str,
    email: str,
    shortcode: str | None = None,
) -> dict:
    f"""
    Register a respondent record linked to the current session.

    {PREREQUISITE_START_SESSION}

    **When to call:** Only after **`session_shortcode`** (6-character) exists from **`parzley_message_turn`**.
    The assistant should **already have invited** the user to register (session email + ask for name / email for
    web access) per **Registration** (5-character path — when and how to invite) — do not silently skip that outreach.

    Registration is **optional** for the **user** to complete (they may decline), but **asking** is **not**
    optional for the assistant once `session_shortcode` exists. See **Registration** below.

    {REGISTRATION}

    {PROACTIVE_COMMUNICATION}

    Args:
        session_id:  Prefer `session_id_from_api` from the latest `parzley_message_turn` result when present;
          otherwise the `session_id` from `start_session`. The API ties respondents to the live session.
        first_name:  Respondent's first name.
        last_name:   Respondent's last name.
        email:       Respondent's email address.
        shortcode:   The **6-character** session shortcode from `parzley_message_turn` (`session_shortcode` when
          returned). Strongly recommended — many Parzley deployments require it to link the respondent
          to the correct form session.

    Returns:
        The created respondent record, or an error dict.
    """
    payload = {
        "first_name": first_name.strip(),
        "last_name": last_name.strip(),
        "email": email.strip(),
        "session_id": session_id.strip(),
    }
    if shortcode:
        payload["shortcode"] = shortcode.strip()

    try:
        result = await _post("/respondents/", payload, auth=False)
        return result
    except httpx.HTTPStatusError as exc:
        detail: object = exc.response.text
        try:
            detail = exc.response.json()
        except Exception:
            pass
        return {
            "error": (
                f"Failed to register respondent ({exc.response.status_code}): {detail}"
            )
        }
    except Exception as exc:
        return {"error": f"Failed to register respondent: {exc}"}
