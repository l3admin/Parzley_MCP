"""
Send one user turn to Parzley — concierge + parser/QA agents in parallel.

This is the primary tool for ongoing conversation after `get_form_with_shortcode`.
"""

import asyncio
from typing import Annotated

from pydantic import Field

from parzley_mcp.instructions import (
    FLOW_NEW_SESSION_FIVE_CHAR,
    FLOW_PARZLEY_MESSAGE_TURN,
    FLOW_RESUME_SIX_CHAR,
    OTHER_TOOLS,
    PARZLEY_CONCEPTS,
    PREREQUISITE_GET_FORM_WITH_SHORTCODE,
    PROACTIVE_COMMUNICATION,
    REGISTRATION,
    USER_EXPERIENCE,
)
from parzley_mcp.mcp_tool_doc import join_tool_doc
from parzley_mcp.server import mcp
from parzley_mcp.http_client import _post

_PARZLEY_MESSAGE_TURN_DESCRIPTION = join_tool_doc(
    "Send a user message to Parzley — fires concierge_chat AND chat_with_agents simultaneously in a single call. "
    "The concierge is the admin-configured agent for the crew’s form; it runs the user-facing dialogue "
    "(use its reply for the user).",
    "This is the ONLY tool you need to call on every user message after get_form_with_shortcode. "
    "It runs both API calls in parallel and returns their combined responses.",
    "This tool is the only MCP surface for those behaviors — do not assume separate tools exist for the "
    "underlying `/concierge-chat` and `/chat` HTTP endpoints.",
    PREREQUISITE_GET_FORM_WITH_SHORTCODE,
    PARZLEY_CONCEPTS,
    PROACTIVE_COMMUNICATION,
    USER_EXPERIENCE,
    REGISTRATION,
    FLOW_NEW_SESSION_FIVE_CHAR,
    FLOW_RESUME_SIX_CHAR,
    FLOW_PARZLEY_MESSAGE_TURN,
    OTHER_TOOLS,
    "**Returns:** concierge (user-facing reply), agents (background updates), optional session_id_from_api and "
    "session_shortcode for register_respondent.",
)

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


@mcp.tool(description=_PARZLEY_MESSAGE_TURN_DESCRIPTION)
async def parzley_message_turn(
    session_id: Annotated[
        str,
        Field(description="Session ID from get_form_with_shortcode (or session_id_from_api from a prior turn when present)."),
    ],
    crew_shortcode: Annotated[
        str,
        Field(description="5-character crew shortcode from get_form_with_shortcode (not the 6-char session code)."),
    ],
    message: Annotated[
        str,
        Field(
            description=(
                "User message or answer. For very long pastes, split at paragraph boundaries (~two paragraphs per chunk), "
                "send with successive calls — or suggest email to shortcode@Parzley.com for one attachment."
            ),
        ),
    ],
    form_data: Annotated[
        dict | None,
        Field(description="Current form field values; pass latest known state for agents."),
    ] = None,
    conversation_history: Annotated[
        list | None,
        Field(description="Prior conversation as list of role/content dicts, if the host does not keep server-side history."),
    ] = None,
    is_voice_mode: Annotated[
        bool,
        Field(description="Set True when the user is on voice/TTS."),
    ] = False,
) -> dict:
    """Concierge + agents in parallel; full guidance is in the MCP tool description."""
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
