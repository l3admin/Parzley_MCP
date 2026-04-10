"""Register a respondent (name + email) for the current Parzley session."""

import httpx

from parzley_mcp.instructions import FLOW_RESUME_SIX_CHAR, PROACTIVE_COMMUNICATION
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

    {PROACTIVE_COMMUNICATION}

    {FLOW_RESUME_SIX_CHAR}

    When the user agrees to register, call this with the **latest** `parzley_message_turn` result: use
    **`session_id_from_api`** as `session_id` when present (otherwise `session_id` from `start_session`),
    and pass **`session_shortcode`** as `shortcode` when present.

    Only for **new** sessions that began with a **5-character** shortcode. Skip this tool if the user
    started with a **6-character** shortcode (respondent is already registered).

    Call only after the first `parzley_message_turn` has succeeded. Registration is
    **optional** but **strongly recommended** so the user can access their data later; collect
    first_name, last_name, and email when the user agrees to register — do not require this before
    logging answers via `parzley_message_turn`.

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
