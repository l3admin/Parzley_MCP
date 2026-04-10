"""Final form submission — lock session and run downstream workflows."""

import httpx

from parzley_mcp.instructions import OTHER_TOOLS, PREREQUISITE_START_SESSION
from parzley_mcp.server import mcp
from parzley_mcp.http_client import _post


@mcp.tool()
async def submit_form_data(shortcode: str, data: dict | None = None) -> dict:
    f"""
    Submit Form Data — final submission: locks the form, persists Parzley-held data, and runs downstream
    workflows. Irreversible — the form cannot be reopened or unsubmitted.

    {PREREQUISITE_START_SESSION}

    {OTHER_TOOLS}

    Pass ``data`` only if the API needs extra display metadata; otherwise omit it or
    pass null — form field values are already stored server-side.

    Args:
        shortcode: The **6-character session shortcode** only (`session_shortcode` from
            `parzley_message_turn`). **Do not** pass the **5-character crew** shortcode — the API will
            return 404.
        data: Optional JSON object for the request body; use null/omit when only a
            trigger is needed.

    Returns:
        API confirmation.
    """
    code = shortcode.strip()
    if len(code) != 6:
        return {
            "error": (
                "submit_form_data requires the **6-character session shortcode** (from "
                "`parzley_message_turn`, e.g. `session_shortcode`). "
                f"You passed {len(code)} character(s); a **5-character crew** code is not valid here — "
                "the response-display endpoint returns 404 for crew shortcodes."
            )
        }

    try:
        return await _post(f"/response-display/submit/{code}", data, auth=False)
    except httpx.HTTPStatusError as exc:
        detail: object = exc.response.text
        try:
            detail = exc.response.json()
        except Exception:
            pass
        return {
            "error": (
                f"submit_form_data failed ({exc.response.status_code}): {detail}. "
                "Confirm you used the **6-character session** shortcode, not the crew code."
            )
        }
    except Exception as exc:
        return {"error": f"submit_form_data failed: {exc}"}
