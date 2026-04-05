"""
Session tools — shortcode resolution and form metadata retrieval.
"""

import uuid
import httpx
from parzley_mcp.server import mcp
from parzley_mcp.http_client import _get


@mcp.tool()
async def start_session(shortcode: str) -> dict:
    """
    Start a new Parzley form-filling session. This MUST be the first tool called.

    The user provides a shortcode:
      - 5-character shortcode → used directly as the crew_shortcode;
        a new session_id is generated automatically.
      - 6-character shortcode → resolved via the Parzley API to obtain
        both the crew_shortcode and the session_id.

    If the shortcode is invalid (not 5 or 6 characters), an error is returned
    and you should ask the user to try again.

    Args:
        shortcode: The 5 or 6 character shortcode provided by the user.

    Returns:
        A dict with session_id, crew_shortcode, and a welcome message —
        or an error message if the shortcode is invalid.
    """
    shortcode = shortcode.strip()

    if len(shortcode) == 5:
        # Direct crew shortcode — resolve mission to get form_id, then generate a fresh session
        try:
            mission = await _get(f"/missions/by-shortcode/{shortcode}", auth=False)
        except httpx.HTTPStatusError as exc:
            return {
                "error": f"Could not resolve shortcode '{shortcode}': "
                         f"{exc.response.status_code} {exc.response.text}"
            }
        except Exception as exc:
            return {"error": f"Failed to resolve shortcode '{shortcode}': {exc}"}

        form_id = mission.get("form_definition_id")
        session_id = str(uuid.uuid4())
        return {
            "session_id": session_id,
            "crew_shortcode": shortcode,
            "form_id": form_id,
            "mission_name": mission.get("mission_name"),
            "form_name": mission.get("form_name"),
            "message": (
                f"Session started! Your crew shortcode is '{shortcode}' "
                f"and your session ID is '{session_id}'. "
                f"Form: '{mission.get('form_name')}' (id: {form_id}). "
                "You can now start filling out your form — just type your answers."
            ),
        }

    if len(shortcode) == 6:
        # Temporary/shared shortcode — resolve via API
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
                    f"Session started! Resolved shortcode '{shortcode}' → "
                    f"crew '{crew_shortcode}', session '{session_id}', form '{form_id}'. "
                    "You can now start filling out your form — just type your answers."
                ),
            }
        except httpx.HTTPStatusError as exc:
            return {
                "error": f"Could not resolve shortcode '{shortcode}': "
                         f"{exc.response.status_code} {exc.response.text}"
            }
        except Exception as exc:
            return {"error": f"Failed to resolve shortcode '{shortcode}': {exc}"}

    # Invalid length
    return {
        "error": (
            f"'{shortcode}' is not a valid shortcode. "
            "Please provide a 5-character crew shortcode or a 6-character temporary shortcode."
        )
    }


@mcp.tool()
async def get_form_data_by_session(session_id: str) -> dict:
    """
    Retrieve the form data filled by the user for a given session.

    Returns all field values that have been collected/submitted during
    the session, including which fields the user has filled out so far.

    Args:
        session_id: The session ID returned by start_session.

    Returns:
        Form data record with id, form_id, user_id, session_id, data (field values),
        created_at, and updated_at.
    """
    return await _get(f"/form-data/by-session/{session_id}", auth=False)


@mcp.tool()
async def get_form(form_id: str) -> dict:
    """
    Retrieve the full form definition for a given form ID.

    Use this to understand exactly what fields the form contains,
    which are required, their types, labels, validation rules,
    and UI hints — before or during a form-filling session.

    The returned schema lets you answer questions like:
      - How many fields does this form have?
      - Which fields are required?
      - What are the allowed values / options for a field?
      - What is the field order?

    Key fields in the response:
      - title / introduction / welcome_message: Human-readable form metadata.
      - schema.properties: Dict of field_name → { type, title, format, enum, minimum, … }
      - schema.required: List of required field names.

    Note: uiSchema (widget hints), uiStyle (colours/fonts), formContext (field
    descriptions), and after_submission_message are included in the response but
    are for rendering purposes only; they are not needed to understand the fields.

    Args:
        form_id: The MongoDB ObjectId string of the form (e.g. obtained from
                 start_session → form_id, or known in advance).

    Returns:
        Full form definition including schema, uiSchema, uiStyle, formContext,
        and all metadata fields.
    """
    return await _get(f"/forms/{form_id}", auth=False)

