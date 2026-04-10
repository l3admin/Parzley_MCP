"""Final form submission — lock session and run downstream workflows."""

from typing import Annotated

import httpx
from pydantic import Field

from parzley_mcp.instructions import OTHER_TOOLS, PREREQUISITE_GET_FORM_WITH_SHORTCODE
from parzley_mcp.mcp_tool_doc import join_tool_doc
from parzley_mcp.server import mcp
from parzley_mcp.http_client import _post

_SUBMIT_FORM_DATA_DESCRIPTION = join_tool_doc(
    "Submit Form Data — final submission: locks the form, persists Parzley-held data, and runs downstream "
    "workflows. Irreversible — the form cannot be reopened or unsubmitted.",
    PREREQUISITE_GET_FORM_WITH_SHORTCODE,
    OTHER_TOOLS,
    "Pass `data` only if the API needs extra display metadata; otherwise omit it or pass null — "
    "form field values are already stored server-side.",
    "**Returns:** API confirmation.",
)


@mcp.tool(description=_SUBMIT_FORM_DATA_DESCRIPTION)
async def submit_form_data(
    shortcode: Annotated[
        str,
        Field(
            description=(
                "**6-character session shortcode only** (`session_shortcode` from parzley_message_turn). "
                "**Do not** pass the 5-character crew code — the API returns 404."
            ),
        ),
    ],
    data: Annotated[
        dict | None,
        Field(description="Optional JSON body for extra display metadata; omit when only triggering submit."),
    ] = None,
) -> dict:
    """Final submit; full guidance is in the MCP tool description."""
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
