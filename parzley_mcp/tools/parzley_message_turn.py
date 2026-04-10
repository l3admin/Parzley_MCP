"""
Send one user turn to Parzley — concierge + parser/QA agents in parallel.

This is the primary tool for ongoing conversation after `start_session`.
"""

import asyncio

from parzley_mcp.instructions import (
    FLOW_NEW_SESSION_FIVE_CHAR,
    FLOW_PARZLEY_MESSAGE_TURN,
    FLOW_RESUME_SIX_CHAR,
    OTHER_TOOLS,
    PARZLEY_CONCEPTS,
    PREREQUISITE_START_SESSION,
    PROACTIVE_COMMUNICATION,
    REGISTRATION,
    USER_EXPERIENCE,
)
from parzley_mcp.server import mcp
from parzley_mcp.http_client import _post

_SESSION_ID_KEYS = frozenset({"session_id"})
_SHORTCODE_KEYS = frozenset(
    {"shortcode", "temporary_shortcode", "temp_shortcode", "session_shortcode"}
)


def _collect_str_by_keys(obj: object, keys: frozenset[str], out: list[str]) -> None:
    keys_lower = {k.lower() for k in keys}
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k.lower() in keys_lower and isinstance(v, str):
                s = v.strip()
                if s:
                    out.append(s)
            _collect_str_by_keys(v, keys, out)
    elif isinstance(obj, list):
        for item in obj:
            _collect_str_by_keys(item, keys, out)


def _first_session_hints(branch: object) -> tuple[str | None, str | None]:
    """Pull session_id and 6-character shortcode from one API branch if present."""
    if not isinstance(branch, dict) or branch.get("error"):
        return None, None
    sids: list[str] = []
    codes: list[str] = []
    _collect_str_by_keys(branch, _SESSION_ID_KEYS, sids)
    _collect_str_by_keys(branch, _SHORTCODE_KEYS, codes)
    sid = sids[0] if sids else None
    shortcode = next((c for c in codes if len(c) == 6), codes[0] if codes else None)
    if shortcode is not None and len(shortcode) != 6:
        shortcode = None
    return sid, shortcode


def _merge_session_hints(
    concierge_result: object, agents_result: object
) -> dict[str, str]:
    """
    Surfaces canonical IDs from Parzley responses for registration and tooling.

    Prefer concierge over agents when both include a session_id.
    """
    hints: dict[str, str] = {}
    c_sid, c_code = _first_session_hints(concierge_result)
    a_sid, a_code = _first_session_hints(agents_result)
    if c_sid:
        hints["session_id_from_api"] = c_sid
    elif a_sid:
        hints["session_id_from_api"] = a_sid
    if c_code:
        hints["session_shortcode"] = c_code
    elif a_code:
        hints["session_shortcode"] = a_code
    return hints


@mcp.tool()
async def parzley_message_turn(
    session_id: str,
    crew_shortcode: str,
    message: str,
    form_data: dict | None = None,
    conversation_history: list | None = None,
    is_voice_mode: bool = False,
) -> dict:
    f"""
    Send a user message to Parzley — fires concierge_chat AND chat_with_agents
    simultaneously in a single call. The concierge is the admin-configured agent
    for the crew’s form; it runs the user-facing dialogue (use its reply for the user).

    This is the ONLY tool you need to call on every user message after
    start_session. It runs both API calls in parallel and returns their
    combined responses.

    This tool is the only MCP surface for those behaviors — do not assume separate
    tools exist for the underlying `/concierge-chat` and `/chat` HTTP endpoints.

    {PREREQUISITE_START_SESSION}

    {PARZLEY_CONCEPTS}

    {PROACTIVE_COMMUNICATION}

    {USER_EXPERIENCE}

    {REGISTRATION}

    {FLOW_NEW_SESSION_FIVE_CHAR}

    {FLOW_RESUME_SIX_CHAR}

    {FLOW_PARZLEY_MESSAGE_TURN}

    {OTHER_TOOLS}

    Args:
        session_id: Session ID returned by start_session.
        crew_shortcode: Crew shortcode returned by start_session.
        message: The user's message or answer. For very long pastes, split at paragraph boundaries (~two
            paragraphs per chunk is a good target), send with successive calls, and tell the user — or
            suggest email to ``shortcode@Parzley.com`` for one attachment/body paste (per **User experience** above).
        form_data: Current form data dict (field → value). Pass the latest
                   known state so the agents have full context.
        conversation_history: Full prior conversation as {{ role, content }} dicts.
        is_voice_mode: Set True if the user is interacting via voice/TTS.

    Returns:
        {{
          "concierge": <ConciergeAgentResponse>,   ← use this for the reply to the user
          "agents":    <ParserAndQAResponse>,       ← background form-data updates
          "session_id_from_api": optional — if present, prefer this for ``register_respondent`` ``session_id``,
          "session_shortcode": optional — 6-character session code; pass to ``register_respondent`` as ``shortcode``
        }}
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

    c_ok = concierge_result if not isinstance(concierge_result, Exception) else {"error": str(concierge_result)}
    a_ok = agents_result if not isinstance(agents_result, Exception) else {"error": str(agents_result)}
    out: dict = {
        "concierge": c_ok,
        "agents": a_ok,
    }
    hints = _merge_session_hints(c_ok, a_ok)
    out.update(hints)
    return out
