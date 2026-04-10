"""Analyse an uploaded file and map content to form fields."""

import base64
import mimetypes
from typing import Annotated

import httpx
from pydantic import Field

from parzley_mcp.config import BASE_URL
from parzley_mcp.instructions import PREREQUISITE_GET_FORM_WITH_SHORTCODE, USER_EXPERIENCE
from parzley_mcp.mcp_tool_doc import join_tool_doc
from parzley_mcp.server import mcp

_ANALYSE_CONTENT_DESCRIPTION = join_tool_doc(
    "Analyze document content against a user query in a simple, direct way.",
    PREREQUISITE_GET_FORM_WITH_SHORTCODE,
    USER_EXPERIENCE,
    "For a single huge document the user wants handled as one piece, prefer suggesting email to shortcode@Parzley.com; "
    "otherwise process in reasonable pieces and keep the user informed.",
    "Use this after extract_content to intelligently match extracted data to form fields. "
    "Multipart upload with session_id and user_query. Does NOT require authentication.",
    "**Returns:** Analysis result with suggested field mappings.",
)


@mcp.tool(description=_ANALYSE_CONTENT_DESCRIPTION)
async def analyse_content(
    file_base64: Annotated[str, Field(description="File contents as base64.")],
    file_name: Annotated[str, Field(description="Original filename with extension.")],
    session_id: Annotated[str, Field(description="Session ID from get_form_with_shortcode.")],
    user_query: Annotated[str, Field(description="What to extract or how to map content to the form.")],
    form_id: Annotated[str | None, Field(description="Optional Mongo form ObjectId to analyse against.")] = None,
    extraction_field: Annotated[str | None, Field(description="Optional single field to target.")] = None,
) -> dict:
    """Analyse upload against query; full guidance is in the MCP tool description."""
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
