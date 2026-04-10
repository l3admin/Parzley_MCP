"""Analyse an uploaded file and map content to form fields."""

import base64
import mimetypes

import httpx

from parzley_mcp.config import BASE_URL
from parzley_mcp.instructions import PREREQUISITE_START_SESSION, USER_EXPERIENCE
from parzley_mcp.server import mcp


@mcp.tool()
async def analyse_content(
    file_base64: str,
    file_name: str,
    session_id: str,
    user_query: str,
    form_id: str | None = None,
    extraction_field: str | None = None,
) -> dict:
    f"""
    Analyze document content against a user query in a simple, direct way.

    {PREREQUISITE_START_SESSION}

    {USER_EXPERIENCE}

    For a single huge document the user wants handled as one piece, prefer suggesting email to
    ``shortcode@Parzley.com`` (attachment or pasted body) (see **User experience** above); otherwise process in
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
