"""Fetch the full form definition from the API (schema, UI hints, and per-field AI guidance)."""

import httpx
from pydantic import Field
from typing import Annotated

from parzley_mcp.instructions import FLOW_GET_FORM_TOOLS, PREREQUISITE_GET_FORM_WITH_SHORTCODE
from parzley_mcp.mcp_tool_doc import join_tool_doc
from parzley_mcp.server import mcp
from parzley_mcp.http_client import _get

_GET_SCHEMA_DESCRIPTION = join_tool_doc(
    "Retrieve the **full form schema / definition** for a **MongoDB form ObjectId** (`GET /forms/{form_object_id}`).",
    "**Use this only after you have the long ObjectId** — not when the user only gave a shortcode.",
    "**Wrong identifier → 400 / not found:** This is **not** shortcode resolution. **Do not** pass a **5- or "
    "6-character shortcode** (crew or session) as `form_object_id` — that calls the wrong resource. To turn a "
    "shortcode like `oZSUD` into `form_id` / `session_id` / `crew_shortcode`, call **`get_form_with_shortcode` "
    "first, then use the **`form_id`** from that response here.",
    PREREQUISITE_GET_FORM_WITH_SHORTCODE,
    FLOW_GET_FORM_TOOLS,
    "The payload is more than raw JSON Schema: it bundles **structure**, **UI behaviour**, and "
    "**per-field guidance** for agents. Use it before or during filling to know what to collect, "
    "how to validate, and what “good” vs “bad” answers look like (when the form author provided them).",
    "**Top-level (examples):** `title`, `introduction`, `welcome_message`, `data_usages_and_privacy`, "
    "`after_submission_message`, plus metadata such as `organization_id`, timestamps, etc.",
    "**`schema`:** JSON Schema — `properties` per field (`type`, `title`, `description`, `pattern`, "
    "`format`, nested objects/arrays, …). Use `schema.required` when present for required fields.",
    "**`uiSchema`:** RJSF-style UI hints — widgets, placeholders, `ui:order`, file accept types, etc. "
    "Helpful for examples and how the form is meant to be filled in the app (not only “pretty colours”).",
    "**`formContext`:** Per-field (and sometimes nested-key) **AI/concierge guidance** — in typical "
    "Parzley forms this includes entries such as `description`, `validation`, `good_example`, "
    "`bad_example`, and `structure`. This is often where nuanced “what to extract / how to phrase it” "
    "rules live; **read it when deciding how to interpret user input and what to push into each field.**",
    "**`uiStyle`:** Visual theming (colours, fonts, spacing). Usually irrelevant to reasoning about "
    "field content; safe to ignore unless you care about presentation.",
    "**Returns:** Full API document: `schema`, `uiSchema`, `formContext`, `uiStyle`, and other metadata fields.",
)


@mcp.tool(description=_GET_SCHEMA_DESCRIPTION)
async def get_schema(
    form_object_id: Annotated[
        str,
        Field(
            description=(
                "MongoDB ObjectId of the form (~24 hex characters), from get_form_with_shortcode → `form_id` "
                "or get_form_data_by_session. **Never** a 5- or 6-character shortcode."
            ),
        ),
    ],
) -> dict:
    """Fetch form schema by ObjectId; full guidance is in the MCP tool description."""
    fid = form_object_id.strip()
    # Shortcodes are 5 or 6 chars; form_id from the API is a Mongo-style ObjectId (24 hex), not a shortcode.
    if len(fid) in (5, 6):
        return {
            "error": (
                "`form_object_id` must be the long MongoDB **form ObjectId** from `get_form_with_shortcode` (or "
                "`get_form_data_by_session`), not a 5- or 6-character **shortcode**. "
                "`get_schema` is `GET /forms/{form_object_id}` — using a shortcode here is the wrong endpoint "
                "and would cause API errors. "
                "**Fix:** call `get_form_with_shortcode` with the user’s shortcode (e.g. oZSUD), then pass the returned "
                "`form_id` to `get_schema` if you still need the full schema."
            )
        }

    try:
        return await _get(f"/forms/{fid}", auth=False)
    except httpx.HTTPStatusError as exc:
        detail: object = exc.response.text
        try:
            detail = exc.response.json()
        except Exception:
            pass
        return {
            "error": (
                f"get_schema failed ({exc.response.status_code}): {detail}. "
                "Confirm `form_object_id` is the long ObjectId from `get_form_with_shortcode`, not a shortcode."
            )
        }
    except Exception as exc:
        return {"error": f"get_schema failed: {exc}"}
