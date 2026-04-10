"""Fetch the full form definition from the API (schema, UI hints, and per-field AI guidance)."""

from parzley_mcp.instructions import FLOW_GET_FORM_TOOLS
from parzley_mcp.server import mcp
from parzley_mcp.http_client import _get


@mcp.tool()
async def get_form_definition(form_id: str) -> dict:
    f"""
    Retrieve the **full form definition** for a given form ID (`GET /forms/{{form_id}}`).

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
        form_id: The MongoDB ObjectId string of the form (e.g. obtained from
                 start_session → form_id, or known in advance).

    Returns:
        Full API document: `schema`, `uiSchema`, `formContext`, `uiStyle`, and other metadata fields.
    """
    return await _get(f"/forms/{form_id}", auth=False)
