"""
Parzley MCP Server
==================
Exposes Parzley's AI Form Filling Agent API as MCP tools,
enabling Claude.ai and other MCP clients to interact with it.

Run (stdio — for Claude Desktop):
    python parzley_mcp_server.py

Run (HTTP/Streamable — for Claude.ai remote, works through Cloudflare):
    python parzley_mcp_server.py --transport http --port 8001
    → endpoint: http://host:8001/mcp

Run (SSE — legacy, requires Cloudflare proxy OFF):
    python parzley_mcp_server.py --transport sse --port 8001
    → endpoint: http://host:8001/sse
"""

import os
import uuid
import httpx
from fastmcp import FastMCP
import base64
import mimetypes

BASE_URL = "https://api.parzley.com"

mcp = FastMCP(
    name="Parzley",
    instructions=
        """
        You have access to Parzley — an AI-powered form filling platform. 
        IMPORTANT FLOW: 
        1. When a user first connects, greet them with a welcome message and ask them to provide their shortcode (5 or 6 characters). 
           - A 5 char code references an EMPTY form, ready to accept data
           - A 6 char code references a form that has been fully or partially filled out
           - After ANY data is submitted to the form the `chat_with_agents` tool will return the 6 char code for the form
           - ALWAYS use the 6 char if it exists to return the session_id
           - The 6 char code will always link to the same session_id
        2. Call `start_session` with the shortcode they provide. This returns 
           `session_id`, `crew_shortcode`, and `form_data_id` — store these for the entire conversation. 
        3. The `form_id` is included in the `start_session` response for both shortcode types.
           Only call `get_form` if the user explicitly asks about the form structure, fields,
           or requirements (e.g. "how many fields?", "what does this form ask?").
           Only call `get_form_data_by_session` if the user asks what they have already filled in.
        4. On EVERY subsequent user message, you MUST call BOTH `concierge_chat` AND 
           `chat_with_agents` simultaneously (in parallel) using the stored 
           `session_id` and `crew_shortcode`. Never call one without the other. 
        Do NOT call any other tool until `start_session` has succeeded."""
)


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

def _headers(auth: bool = True) -> dict:
    """Build request headers, optionally including the bearer token."""
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    if auth:
        token = os.environ.get("PARZLEY_API_KEY", "")
        if token:
            headers["Authorization"] = f"Bearer {token}"
    return headers


async def _get(path: str, *, auth: bool = True) -> dict:
    """Perform an authenticated (or public) GET request."""
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.get(f"{BASE_URL}{path}", headers=_headers(auth))
        resp.raise_for_status()
        return resp.json()


async def _post(path: str, payload: dict, *, auth: bool = True) -> dict:
    """Perform an authenticated (or public) POST request."""
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            f"{BASE_URL}{path}", json=payload, headers=_headers(auth),
        )
        resp.raise_for_status()
        return resp.json()


# ---------------------------------------------------------------------------
# SESSION START — welcome gate & shortcode resolution
# ---------------------------------------------------------------------------

@mcp.tool()
async def start_session(shortcode: str) -> dict:
    """
    Start a new Parzley form-filling session. This MUST be the first tool called.

    The user provides a shortcode:
      - 5-character shortcode → used directly as the crew_shortcode;
        a new session_id is generated automatically.
      - 6-character shortcode → resolved via the Parzley API to obtain
        both the crew_shortcode and the session_id.

    If the shortcode is invalid (not 5 or 6 characters), an error is returned
    and you should ask the user to try again.

    Args:
        shortcode: The 5 or 6 character shortcode provided by the user.

    Returns:
        A dict with session_id, crew_shortcode, and a welcome message —
        or an error message if the shortcode is invalid.
    """
    shortcode = shortcode.strip()

    if len(shortcode) == 5:
        # Direct crew shortcode — resolve mission to get form_id, then generate a fresh session
        try:
            mission = await _get(f"/missions/by-shortcode/{shortcode}", auth=False)
        except httpx.HTTPStatusError as exc:
            return {"error": f"Could not resolve shortcode '{shortcode}': {exc.response.status_code} {exc.response.text}"}
        except Exception as exc:
            return {"error": f"Failed to resolve shortcode '{shortcode}': {exc}"}

        form_id = mission.get("form_definition_id")
        session_id = str(uuid.uuid4())
        return {
            "session_id": session_id,
            "crew_shortcode": shortcode,
            "form_id": form_id,
            "mission_name": mission.get("mission_name"),
            "form_name": mission.get("form_name"),
            "message": (
                f"Session started! Your crew shortcode is '{shortcode}' "
                f"and your session ID is '{session_id}'. "
                f"Form: '{mission.get('form_name')}' (id: {form_id}). "
                "You can now start filling out your form — just type your answers."
            ),
        }

    if len(shortcode) == 6:
        # Temporary/shared shortcode — resolve via API
        try:
            data = await _get(f"/shortcodes/{shortcode}", auth=False)
            crew_shortcode = data.get("crew_shortcode")
            session_id = data.get("session_id")
            form_data_id = data.get("form_data_id")
            form_id = data.get("form_id")
            if not crew_shortcode or not session_id:
                return {"error": "The API response was missing crew_shortcode or session_id. Please try again."}
            return {
                "session_id": session_id,
                "crew_shortcode": crew_shortcode,
                "form_data_id": form_data_id,
                "form_id": form_id,
                "message": (
                    f"Session started! Resolved shortcode '{shortcode}' → "
                    f"crew '{crew_shortcode}', session '{session_id}', form '{form_id}'. "
                    "You can now start filling out your form — just type your answers."
                ),
            }
        except httpx.HTTPStatusError as exc:
            return {"error": f"Could not resolve shortcode '{shortcode}': {exc.response.status_code} {exc.response.text}"}
        except Exception as exc:
            return {"error": f"Failed to resolve shortcode '{shortcode}': {exc}"}

    # Invalid length
    return {
        "error": (
            f"'{shortcode}' is not a valid shortcode. "
            "Please provide a 5-character crew shortcode or a 6-character temporary shortcode."
        )
    }


@mcp.tool()
async def get_form_data_by_session(session_id: str) -> dict:
    """
    Retrieve the form data filled by the user for a given session.

    Returns all field values that have been collected/submitted during
    the session, including which fields the user has filled out so far.

    Args:
        session_id: The session ID returned by start_session.

    Returns:
        Form data record with id, form_id, user_id, session_id, data (field values),
        created_at, and updated_at.
    """
    return await _get(f"/form-data/by-session/{session_id}", auth=False)


@mcp.tool()
async def get_form(form_id: str) -> dict:
    """
    Retrieve the full form definition for a given form ID.

    Use this to understand exactly what fields the form contains,
    which are required, their types, labels, validation rules,
    and UI hints — before or during a form-filling session.

    The returned schema lets you answer questions like:
      - How many fields does this form have?
      - Which fields are required?
      - What are the allowed values / options for a field?
      - What is the field order?

    Key fields in the response:
      - title / introduction / welcome_message: Human-readable form metadata.
      - schema.properties: Dict of field_name → { type, title, format, enum, minimum, … }
      - schema.required: List of required field names.

    Args:
        form_id: The MongoDB ObjectId string of the form (e.g. obtained from
                 get_form_data_by_session → form_id, or known in advance).

    Returns:
        Full form definition including schema, uiSchema, uiStyle, formContext,
        and all metadata fields.
    """
    return await _get(f"/forms/{form_id}", auth=False)




@mcp.tool()
async def concierge_chat(
    session_id: str,
    crew_shortcode: str,
    message: str | None = None,
    conversation_history: list | None = None,
    is_voice_mode: bool = False,
) -> dict:
    """
    Chat with the Parzley AI form-filling concierge agent.

    This is the PRIMARY tool for guiding a user through filling out a form.
    The concierge agent asks questions, collects answers, and fills the form
    on the user's behalf. Does NOT require authentication.

    ⚠️  MUST be called simultaneously with `chat_with_agents` on EVERY user
    message. Use the `session_id` and `crew_shortcode` returned by `start_session`.

    Args:
        session_id: Session ID returned by start_session.
        crew_shortcode: Crew shortcode returned by start_session.
        message: The user's message or answer to send to the agent.
                 Omit on the first call to start the conversation.
        conversation_history: Full prior conversation as a list of
                              { role, content } dicts. Pass the full history
                              each turn to maintain context.
        is_voice_mode: Set True if the user is interacting via voice/TTS.

    Returns:
        ConciergeAgentResponse with the agent's reply and any form state updates.
    """
    return await _post("/concierge-chat", {
        "session_id": session_id,
        "crew_shortcode": crew_shortcode,
        "message": message,
        "conversation_history": conversation_history or [],
        "is_voice_mode": is_voice_mode,
    }, auth=False)


@mcp.tool()
async def chat_with_agents(
    session_id: str,
    message: str,
    conversation_history: list | None = None,
) -> dict:
    """
    Send a message to the parallel Parzley agent pipeline (parser + QA agents).

    Use this for multi-agent processing of user input — both a parsed form
    update AND quality assurance in a single round-trip. Requires authentication.

    ⚠️  MUST be called simultaneously with `concierge_chat` on EVERY user
    message. Use the `session_id` returned by `start_session`.

    Args:
        session_id: Session ID returned by start_session.
        message: The user's message or answer.
        conversation_history: Prior conversation history as { role, content } dicts.

    Returns:
        Combined agent response with parsed data and QA feedback.
    """
    return await _post("/chat", {
        "session_id": session_id,
        "message": message,
        "conversation_history": conversation_history or [],
    })


@mcp.tool()
async def get_editor_suggestion(session_id: str) -> dict:
    """
    Retrieve the latest editor suggestion for a session.

    After a concierge_chat turn, call this to get the structured document
    output that represents the current state of the form being filled.

    Args:
        session_id: The session ID used in concierge_chat or chat_with_agents.

    Returns:
        { status, text_output, type, session_id, _id, created_at, updated_at }
    """
    return await _get(f"/editor-suggestion/{session_id}", auth=False)


# ---------------------------------------------------------------------------
# CONTENT EXTRACTION & ANALYSIS
# ---------------------------------------------------------------------------

@mcp.tool()
async def extract_content(
    file_base64: str,
    file_name: str,
    session_id: str,
    form_id: str,
) -> dict:
    """
    Extract raw text / vision description from an uploaded file.

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


# ---------------------------------------------------------------------------
# RESPONSE DISPLAY  — UI rendering data
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Parzley MCP Server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse", "http"],
        default="stdio",
        help=(
            "Transport: 'stdio' (Claude Desktop, default), "
            "'http' (streamable-http — works through Cloudflare, endpoint: /mcp), "
            "'sse' (legacy SSE — requires Cloudflare proxy OFF, endpoint: /sse)"
        ),
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8001,
        help="Port for SSE/HTTP transport (default: 8001)",
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind for SSE/HTTP transport (default: 0.0.0.0)",
    )
    args = parser.parse_args()

    if args.transport == "http":
        print(f"Starting Parzley MCP Server (Streamable HTTP) on http://{args.host}:{args.port}/mcp")
        mcp.run(transport="streamable-http", host=args.host, port=args.port)
    elif args.transport == "sse":
        print(f"Starting Parzley MCP Server (SSE) on http://{args.host}:{args.port}/sse")
        mcp.run(transport="sse", host=args.host, port=args.port)
    else:
        mcp.run(transport="stdio")
