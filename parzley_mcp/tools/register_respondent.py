"""Register a respondent (name + email) for the current Parzley session."""

from typing import Annotated

import httpx
from pydantic import Field

from parzley_mcp.instructions import (
    PREREQUISITE_GET_FORM_WITH_SHORTCODE,
    PROACTIVE_COMMUNICATION,
    REGISTRATION,
)
from parzley_mcp.mcp_tool_doc import join_tool_doc
from parzley_mcp.server import mcp
from parzley_mcp.http_client import _post

_REGISTER_RESPONDENT_DESCRIPTION = join_tool_doc(
    "Register a respondent record linked to the current session.",
    PREREQUISITE_GET_FORM_WITH_SHORTCODE,
    "**When to call:** Only after **`session_shortcode`** (6-character) exists from **`parzley_message_turn`**. "
    "The assistant should **already have invited** the user to register (session email + ask for name / email for "
    "web access) per **Registration** — do not silently skip that outreach.",
    "Registration is **optional** for the **user** to complete (they may decline), but **asking** is **not** "
    "optional for the assistant once `session_shortcode` exists. See **Registration** below.",
    REGISTRATION,
    PROACTIVE_COMMUNICATION,
    "**Returns:** The created respondent record, or an error dict.",
)


@mcp.tool(description=_REGISTER_RESPONDENT_DESCRIPTION)
async def register_respondent(
    session_id: Annotated[
        str,
        Field(
            description=(
                "Prefer session_id_from_api from the latest parzley_message_turn when present; "
                "otherwise session_id from get_form_with_shortcode."
            ),
        ),
    ],
    first_name: Annotated[str, Field(description="Respondent's first name.")],
    last_name: Annotated[str, Field(description="Respondent's last name.")],
    email: Annotated[str, Field(description="Respondent's email address.")],
    shortcode: Annotated[
        str | None,
        Field(
            description=(
                "6-character session shortcode from parzley_message_turn (session_shortcode). "
                "Strongly recommended — many deployments require it."
            ),
        ),
    ] = None,
) -> dict:
    """Link name and email to session; full guidance is in the MCP tool description."""
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
