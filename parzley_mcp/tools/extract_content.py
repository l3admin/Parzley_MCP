"""Extract text or vision description from an uploaded file (PDF / image)."""

import base64
import mimetypes
from typing import Annotated

import httpx
from pydantic import Field

from parzley_mcp.config import BASE_URL
from parzley_mcp.instructions import PREREQUISITE_GET_FORM_WITH_SHORTCODE, USER_EXPERIENCE
from parzley_mcp.mcp_tool_doc import join_tool_doc
from parzley_mcp.server import mcp

_EXTRACT_CONTENT_DESCRIPTION = join_tool_doc(
    "Extract raw text / vision description from an uploaded file.",
    PREREQUISITE_GET_FORM_WITH_SHORTCODE,
    USER_EXPERIENCE,
    "If the user needs one full document delivered in a single step, suggest they email shortcode@Parzley.com "
    "(their 6-character code) with the file attached or long text in the body.",
    "Runs LlamaParse for PDFs or VisionAgent (Groq) for images. Does NOT run validation — use analyse_content for that. "
    "Does NOT require authentication.",
    "The endpoint expects multipart/form-data with the file binary, session_id, and form_id.",
    "**Returns:** Extraction result with raw text and/or vision description.",
)


@mcp.tool(description=_EXTRACT_CONTENT_DESCRIPTION)
async def extract_content(
    file_base64: Annotated[str, Field(description="File contents as base64.")],
    file_name: Annotated[str, Field(description='Original filename with extension (e.g. "resume.pdf").')],
    session_id: Annotated[str, Field(description="Session ID from get_form_with_shortcode.")],
    form_id: Annotated[str, Field(description="Mongo form ObjectId for this session (from get_form_with_shortcode).")],
) -> dict:
    """Upload file for extraction; full guidance is in the MCP tool description."""
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
