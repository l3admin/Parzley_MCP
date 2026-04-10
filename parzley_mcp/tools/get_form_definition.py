"""Fetch the full form definition from the API (schema, UI hints, and per-field AI guidance)."""

import httpx

from parzley_mcp.instructions import FLOW_GET_FORM_TOOLS, PREREQUISITE_START_SESSION
from parzley_mcp.server import mcp
from parzley_mcp.http_client import _get


@mcp.tool()
async def get_form_definition(form_id: str) -> dict:
    f"""
    Retrieve the **full form definition** for a **form ObjectId** (`GET /forms/{{form_id}}`).

    **Wrong identifier → 400 / not found:** This is **not** shortcode resolution. **Do not** pass a **5- or
    6-character shortcode** (crew or session) as `form_id` — that calls the wrong resource. To turn a shortcode
    like `oZSUD` into `form_id` / `session_id` / `crew_shortcode`, call **`start_session`** first, then use the
    **`form_id`** from that response here.

    {PREREQUISITE_START_SESSION}

    {FLOW_GET_FORM_TOOLS}

    The payload is more than raw JSON Schema: it bundles **structure**, **UI behaviour**, and
    **per-field guidance** for agents. Use it before or during filling to know what to collect,
    how to validate, and what “good” vs “bad” answers look like (when the form author provided them).

    **Top-level (examples):** `title`, `introduction`, `welcome_message`, `data_usages_and_privacy`,
    `after_submission_message`, plus metadata such as `organization_id`, timestamps, etc.

    **`schema`:** JSON Schema — `properties` per field (`type`, `title`, `description`, `pattern`,
    `format`, nested objects/arrays, …). Use `schema.required` when present for required fields.

    **`uiSchema`:** RJSF-style UI hints — widgets, placeholders, `ui:order`, file accept types, etc.
    Helpful for examples and how the form is meant to be filled in the app (not only “pretty colours”).

    **`formContext`:** Per-field (and sometimes nested-key) **AI/concierge guidance** — in typical
    Parzley forms this includes entries such as `description`, `validation`, `good_example`,
    `bad_example`, and `structure`. This is often where nuanced “what to extract / how to phrase it”
    rules live; **read it when deciding how to interpret user input and what to push into each field.**

    **`uiStyle`:** Visual theming (colours, fonts, spacing). Usually irrelevant to reasoning about
    field content; safe to ignore unless you care about presentation.

    Args:
        form_id: **MongoDB ObjectId** of the form (~24 hex characters), from **`start_session`** → `form_id`
                 or **`get_form_data_by_session`**. Never a shortcode.

    Returns:
        Full API document: `schema`, `uiSchema`, `formContext`, `uiStyle`, and other metadata fields.
    """
    fid = form_id.strip()
    # Shortcodes are 5 or 6 chars; form_id from the API is a Mongo-style ObjectId (24 hex), not a shortcode.
    if len(fid) in (5, 6):
        return {
            "error": (
                "`form_id` must be the long MongoDB **form ObjectId** from `start_session` (or "
                "`get_form_data_by_session`), not a 5- or 6-character **shortcode**. "
                "`get_form_definition` is `GET /forms/{form_id}` — using a shortcode here is the wrong endpoint "
                "and would cause API errors. "
                "**Fix:** call `start_session` with the user’s shortcode (e.g. oZSUD), then pass the returned "
                "`form_id` to `get_form_definition` if you still need the full schema."
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
                f"get_form_definition failed ({exc.response.status_code}): {detail}. "
                "Confirm `form_id` is the long ObjectId from `start_session`, not a shortcode."
            )
        }
    except Exception as exc:
        return {"error": f"get_form_definition failed: {exc}"}
