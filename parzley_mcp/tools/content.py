"""
Content extraction and analysis tools — PDF parsing and vision analysis.
"""

import base64
import mimetypes

import httpx

from parzley_mcp.config import BASE_URL
from parzley_mcp.server import mcp


@mcp.tool()
async def extract_content(
    file_base64: str,
    file_name: str,
    session_id: str,
    form_id: str,
) -> dict:
    """
    Extract raw text / vision description from an uploaded file.

    If the user needs one full document delivered in a single step, suggest they email ``shortcode@Parzley.com``
    (their 6-character code) with the file attached or long text in the body — see server instructions.

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


@mcp.tool()
async def analyse_content(
    file_base64: str,
    file_name: str,
    session_id: str,
    user_query: str,
    form_id: str | None = None,
    extraction_field: str | None = None,
) -> dict:
    """
    Analyze document content against a user query in a simple, direct way.

    For a single huge document the user wants handled as one piece, prefer suggesting email to
    ``shortcode@Parzley.com`` (attachment or pasted body) per server instructions; otherwise process in
    reasonable pieces and keep the user informed.

    Use this after extract_content to intelligently match extracted data
    to the fields of a specific form. Accepts a file upload via
    multipart/form-data along with a session_id and user_query.
    Does NOT require authentication.

    Args:
        file_base64: The file contents encoded as a base64 string.
        file_name: Original filename including extension (e.g. "resume.pdf").
        session_id: Session ID returned by start_session.
        user_query: The user's query describing what to analyse / extract.
        form_id: Optional — the form ID to analyse content against.
        extraction_field: Optional — a specific field to target for extraction.

    Returns:
        Analysis result with suggested field mappings.
    """
    file_bytes = base64.b64decode(file_base64)
    mime_type = mimetypes.guess_type(file_name)[0] or "application/octet-stream"

    form_data: dict[str, str] = {
        "session_id": session_id,
        "user_query": user_query,
    }
    if form_id is not None:
        form_data["form_id"] = form_id
    if extraction_field is not None:
        form_data["extraction_field"] = extraction_field

    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(
            f"{BASE_URL}/content-analysis/analyse",
            files={"file": (file_name, file_bytes, mime_type)},
            data=form_data,
            headers={"Accept": "application/json"},
        )
        resp.raise_for_status()
        return resp.json()

