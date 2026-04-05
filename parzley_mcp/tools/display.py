"""
Response display tool — push rendered output data after a session completes.
"""

from parzley_mcp.server import mcp
from parzley_mcp.http_client import _post


@mcp.tool()
async def submit_response_display(shortcode: str, data: dict) -> dict:
    """
    Submit response display data for a given shortcode.

    Use this to push rendered output data to the response display system,
    typically after a session completes.
    Does NOT require authentication.

    Args:
        shortcode: The shortcode of the mission/agent to submit display data for.
        data: The structured display data to submit.

    Returns:
        Submission confirmation.
    """
    return await _post(f"/response-display/submit/{shortcode}", data, auth=False)

