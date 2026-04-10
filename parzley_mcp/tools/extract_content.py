"""Extract text or vision description from an uploaded file (PDF / image)."""

import base64
import mimetypes

import httpx

from parzley_mcp.config import BASE_URL
from parzley_mcp.instructions import USER_EXPERIENCE
from parzley_mcp.server import mcp


@mcp.tool()
async def extract_content(
    file_base64: str,
    file_name: str,
    session_id: str,
    form_id: str,
) -> dict:
    f"""
    Extract raw text / vision description from an uploaded file.

    {USER_EXPERIENCE}

    If the user needs one full document delivered in a single step, suggest they email ``shortcode@Parzley.com``
    (their 6-character code) with the file attached or long text in the body (see **User experience** above).

    Runs LlamaParse for PDFs or VisionAgent (Groq) for images.
    Does NOT run validation — use analyse_content for that.
    Does NOT require authentication.

    The endpoint expects multipart/form-data with the file binary,
    session_id, and form_id.

    Args:
        file_base64: The file contents encoded as a base64 string.
        file_name: Original filename including extension (e.g. "resume.pdf").
        session_id: Session ID returned by start_session.
        form_id: The ID of the form to extract content for.

    Returns:
        Extraction result with raw text and/or vision description.
    """
    file_bytes = base64.b64decode(file_base64)
    mime_type = mimetypes.guess_type(file_name)[0] or "application/octet-stream"

    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(
            f"{BASE_URL}/content-extraction/extract",
            files={"file": (file_name, file_bytes, mime_type)},
            data={"session_id": session_id, "form_id": form_id},
            headers={"Accept": "application/json"},
        )
        resp.raise_for_status()
        return resp.json()
