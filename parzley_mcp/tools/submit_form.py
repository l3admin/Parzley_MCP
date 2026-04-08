"""
Final form submission — trigger lock and downstream workflows.
"""

from parzley_mcp.server import mcp
from parzley_mcp.http_client import _post


@mcp.tool(name="Submit Form Data")
async def submit_form_data(shortcode: str, data: dict | None = None) -> dict:
    """
    Final submission: locks the form, persists Parzley-held data, and runs downstream
    workflows. Irreversible — the form cannot be reopened or unsubmitted.

    Pass ``data`` only if the API needs extra display metadata; otherwise omit it or
    pass null — form field values are already stored server-side.

    Args:
        shortcode: The session shortcode (typically the 6-character code).
        data: Optional JSON object for the request body; use null/omit when only a
            trigger is needed.

    Returns:
        API confirmation.
    """
    return await _post(f"/response-display/submit/{shortcode}", data, auth=False)
