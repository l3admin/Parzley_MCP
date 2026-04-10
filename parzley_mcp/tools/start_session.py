"""Resolve a crew or session shortcode and start a Parzley form-filling session."""

import uuid

import httpx

from parzley_mcp.instructions import (
    FLOW_CONNECT,
    FLOW_NEW_SESSION_FIVE_CHAR,
    FLOW_START_SESSION,
    INTRO,
    PARZLEY_CONCEPTS,
)
from parzley_mcp.server import mcp
from parzley_mcp.http_client import _get


@mcp.tool()
async def start_session(shortcode: str) -> dict:
    f"""
    Start a new Parzley form-filling session. This MUST be the first tool called.

    {INTRO}

    {PARZLEY_CONCEPTS}

    {FLOW_CONNECT}

    {FLOW_START_SESSION}

    {FLOW_NEW_SESSION_FIVE_CHAR}

    Shortcodes (quick reference for this tool):
      - **5 characters** — the crew’s form template (empty form); starts a new session (`session_id` is new).
      - **6 characters** — an existing session’s handle: ties to saved form data and a stable
        `session_id` (resume or continue partial/filled work).

    Resolution:
      - 5-character shortcode → used directly as the crew_shortcode;
        a new session_id is generated automatically.
      - 6-character shortcode → resolved via the Parzley API to obtain
        both the crew_shortcode and the session_id.

    If the shortcode is invalid (not 5 or 6 characters), an error is returned
    and you should ask the user to try again.

    Args:
        shortcode: The 5 or 6 character shortcode provided by the user.

    Returns:
        On success: `session_id`, `crew_shortcode`, `form_id`, `form_name`, optional `mission_name`
        (API display label for the crew/form), `message`, and for 6-char
        flows optionally `form_data_id`. On failure: `error`.
    """
    shortcode = shortcode.strip()

    if len(shortcode) == 5:
        try:
            crew_template = await _get(f"/missions/by-shortcode/{shortcode}", auth=False)
        except httpx.HTTPStatusError as exc:
            return {
                "error": f"Could not resolve shortcode '{shortcode}': "
                f"{exc.response.status_code} {exc.response.text}"
            }
        except Exception as exc:
            return {"error": f"Failed to resolve shortcode '{shortcode}': {exc}"}

        form_id = crew_template.get("form_definition_id")
        session_id = str(uuid.uuid4())
        return {
            "session_id": session_id,
            "crew_shortcode": shortcode,
            "form_id": form_id,
            "mission_name": crew_template.get("mission_name"),
            "form_name": crew_template.get("form_name"),
            "message": (
                f"Session started with 5-character crew shortcode '{shortcode}' (empty form template). "
                f"session_id={session_id}, form_id={form_id}, form={crew_template.get('form_name')!r}. "
                "Documentation (also in this tool's description): the 6-character shortcode is the "
                "session handle — it appears after the first successful parzley_message_turn "
                "(see session_shortcode in that response). It identifies this form instance and saved "
                "answers; users resume with it via start_session; use it for session email "
                "(the 6-character session code as the local part, e.g. Ab12xY@Parzley.com), "
                "submit_form_data, and register_respondent as described in PARZLEY CONCEPTS / "
                "Proactive communication. Required next tool call: parzley_message_turn with a "
                "welcome/greeting — do not skip it for get_form_definition."
            ),
        }

    if len(shortcode) == 6:
        try:
            data = await _get(f"/shortcodes/{shortcode}", auth=False)
            crew_shortcode = data.get("crew_shortcode")
            session_id = data.get("session_id")
            form_data_id = data.get("form_data_id")
            form_id = data.get("form_id")
            if not crew_shortcode or not session_id:
                return {
                    "error": "The API response was missing crew_shortcode or session_id. "
                    "Please try again."
                }
            return {
                "session_id": session_id,
                "crew_shortcode": crew_shortcode,
                "form_data_id": form_data_id,
                "form_id": form_id,
                "message": (
                    f"Session resumed with 6-character session shortcode '{shortcode}' "
                    f"(this code identifies this form instance and saved answers). "
                    f"crew_shortcode={crew_shortcode}, session_id={session_id}, form_id={form_id}. "
                    f"Proactively share session email {shortcode}@Parzley.com per server instructions; "
                    "web app URL for viewing data follows registration rules in PARZLEY CONCEPTS."
                ),
            }
        except httpx.HTTPStatusError as exc:
            return {
                "error": f"Could not resolve shortcode '{shortcode}': "
                f"{exc.response.status_code} {exc.response.text}"
            }
        except Exception as exc:
            return {"error": f"Failed to resolve shortcode '{shortcode}': {exc}"}

    return {
        "error": (
            f"'{shortcode}' is not a valid shortcode. "
            "Please provide a 5-character crew shortcode or a 6-character temporary shortcode."
        )
    }
