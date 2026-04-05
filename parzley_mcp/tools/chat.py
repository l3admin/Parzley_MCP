"""
Chat tool — fires concierge + background agents simultaneously.
"""

import asyncio
from parzley_mcp.server import mcp
from parzley_mcp.http_client import _post


@mcp.tool()
async def send_message(
    session_id: str,
    crew_shortcode: str,
    message: str,
    form_data: dict | None = None,
    conversation_history: list | None = None,
    is_voice_mode: bool = False,
) -> dict:
    """
    Send a user message to Parzley — fires concierge_chat AND chat_with_agents
    simultaneously in a single call.

    This is the ONLY tool you need to call on every user message after
    start_session. It runs both API calls in parallel and returns their
    combined responses.

    You MUST call BOTH `concierge_chat` AND `chat_with_agents` simultaneously
    by using this single tool — never call them separately.

    Args:
        session_id: Session ID returned by start_session.
        crew_shortcode: Crew shortcode returned by start_session.
        message: The user's message or answer.
        form_data: Current form data dict (field → value). Pass the latest
                   known state so the agents have full context.
        conversation_history: Full prior conversation as { role, content } dicts.
        is_voice_mode: Set True if the user is interacting via voice/TTS.

    Returns:
        {
          "concierge": <ConciergeAgentResponse>,   ← use this for the reply to the user
          "agents":    <ParserAndQAResponse>        ← background form-data updates
        }
    """
    concierge_payload = {
        "session_id": session_id,
        "crew_shortcode": crew_shortcode,
        "message": message,
        "conversation_history": conversation_history or [],
        "is_voice_mode": is_voice_mode,
    }
    agents_payload = {
        "session_id": session_id,
        "crew_shortcode": crew_shortcode,
        "form_data": form_data or {},
        "message": message,
        "is_background_mode": True,
        "conversation_history": conversation_history or [],
    }

    concierge_result, agents_result = await asyncio.gather(
        _post("/concierge-chat", concierge_payload, auth=False),
        _post("/chat", agents_payload, auth=False),
        return_exceptions=True,
    )

    return {
        "concierge": (
            concierge_result
            if not isinstance(concierge_result, Exception)
            else {"error": str(concierge_result)}
        ),
        "agents": (
            agents_result
            if not isinstance(agents_result, Exception)
            else {"error": str(agents_result)}
        ),
    }

