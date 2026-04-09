"""
Session tools — shortcode resolution, respondent creation, and form metadata retrieval.
"""

import uuid
import httpx
from parzley_mcp.server import mcp
from parzley_mcp.http_client import _get, _post


@mcp.tool()
async def start_session(shortcode: str) -> dict:
    """
    Start a new Parzley form-filling session. This MUST be the first tool called.

    Shortcodes (see server instructions for crews & concepts):
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
        (API display label for the crew/form — see server instructions), `message`, and for 6-char
        flows optionally `form_data_id`. On failure: `error`.
    """
    shortcode = shortcode.strip()

    if len(shortcode) == 5:
        # 5-char shortcode = crew handle: resolve form template from Parzley API, then new session_id
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
                f"Session started! Your crew shortcode is '{shortcode}' "
                f"and your session ID is '{session_id}'. "
                f"Form: '{crew_template.get('form_name')}' (id: {form_id}). "
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
async def create_respondent(
    session_id: str,
    first_name: str,
    last_name: str,
    email: str,
    shortcode: str | None = None,
) -> dict:
    """
    Create a respondent record linked to the current session.

    Only for **new** sessions that began with a **5-character** shortcode. Skip this tool if the user
    started with a **6-character** shortcode (respondent is already registered).

    Call only after the first `send_message` has succeeded (see server instructions). Registration is
    **optional** but **strongly recommended** so the user can access their data later; collect
    first_name, last_name, and email when the user agrees to register — do not require this before
    logging answers via `send_message`.

    Args:
        session_id:  Prefer `session_id_from_api` from the latest `send_message` result when present;
          otherwise the `session_id` from `start_session`. The API ties respondents to the live session.
        first_name:  Respondent's first name.
        last_name:   Respondent's last name.
        email:       Respondent's email address.
        shortcode:   The **6-character** session shortcode from `send_message` (`session_shortcode` when
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
                f"Failed to create respondent ({exc.response.status_code}): {detail}"
            )
        }
    except Exception as exc:
        return {"error": f"Failed to create respondent: {exc}"}


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

