"""
Reusable Parzley agent instruction blocks.

Compose ``SERVER_INSTRUCTIONS`` for FastMCP and import individual constants into
tool docstrings (next step) to avoid duplication.
"""

from __future__ import annotations

from textwrap import dedent


def _block(text: str) -> str:
    """Normalize indented triple-quoted strings for readable source layout."""
    return dedent(text).strip()


# --- Intro & domain concepts -------------------------------------------------

INTRO = _block(
    """
    You have access to Parzley — an AI-powered data collection (form filling) platform.
    """
)

PARZLEY_CONCEPTS = _block(
    """
    PARZLEY CONCEPTS (crews, shortcodes & IDs):

    - **Crew:** Represented by the **5-character shortcode**. It pairs a **concierge agent** (manages
      the interaction between the user and Parzley) with the **form schema** (defines what data is
      collected). Pass **`crew_shortcode`** from `start_session` into `parzley_message_turn`; use the
      **`concierge`** field in the response as the user-facing reply.

    - **5-character shortcode:** Identifies the crew’s *form template* (empty form). Use it when the
      user starts fresh. `start_session` creates a new `session_id` for that crew/form.

    - **6-character shortcode:** Identifies a *specific* form-filling session and its saved answers
      (work in progress or complete). It always resolves to the same `session_id` and `crew_shortcode`.
      When the user gives you this code, that session **already has respondent registration** (name,
      email, etc.) — do **not** ask for those details again or call `register_respondent` again unless an
      API error shows registration is missing.

    - **API field `mission_name`:** Some `start_session` responses include this key (legacy Parzley
      name). Treat it as an optional display label for the crew/form setup; prefer explaining things
      to users in terms of the form and shortcodes.

    - **Internal IDs** (`session_id`, `crew_shortcode`, `form_id`): Returned by tools for your
      calls only. Users only know 5- or 6-character shortcodes.
    """
)

# --- URL / email / proactive messaging -----------------------------------------

PROACTIVE_COMMUNICATION = _block(
    """
    PROACTIVE COMMUNICATION (outbound — do these without waiting for the user to ask):

    - **As soon as a 6-character shortcode exists** (returned from Parzley in a tool response, or
      supplied by the user for a resume), you **MUST** tell the user **both** the **web URL** and the
      **email address** below, using their **actual** 6-character code. Do not skip this; do not wait
      for them to ask. Explain briefly:
      - **View / access their data:** use the **URL** (Parzley app).
      - **Update their data:** use the **URL** or the **email** channel (either works).
      Formats (replace `shortcode` with their **6-character session** code only — see **App URL shape** below):
      - **Web / app:** `https://app.parzley.com/shortcode` (e.g. `https://app.parzley.com/_00-2n`).
      - **Email:** `shortcode@Parzley.com` (e.g. `_00-2n@Parzley.com`).

    - **App URL shape (read carefully — common model error):** The path after `app.parzley.com/` must be
      **exactly one** segment: the **6-character session shortcode** returned for their form session.
      **Do not** put the **5-character crew** shortcode in the URL. **Do not** use two segments such as
      `crew_shortcode/session_shortcode` or `fivechars/sixchars`.
      - **Wrong:** `https://app.parzley.com/oZSUD/_00-2n` (crew + slash + session — **invalid**).
      - **Right:** `https://app.parzley.com/_00-2n` (session code only).
      You still pass **`crew_shortcode`** to **`parzley_message_turn`** as an API argument; that is separate from
      what you show the user in the **browser link**.

    - **After `register_respondent` succeeds:** In the **same** user-facing reply (or your very next
      message if the tool result arrives separately), you **MUST** include the full **URL + email** again
      with their 6-character code, plus access vs update — even if you already shared them earlier.
      Users often miss earlier turns; registration is when they most need how to connect to Parzley.
    """
)

USER_EXPERIENCE = _block(
    """
    USER EXPERIENCE (waiting, long input, and stepping away):

    - **Mandatory — URL + email whenever the 6-character code is known:** Repeat the obligation above:
      the moment that code is created or known in the session, **always** give the user the full **URL**
      and **email** (with their code substituted), plus the short distinction — **access** via URL;
      **update** via URL **or** email. Claude and other hosts sometimes underweight earlier sections, so
      treat this block as non-optional whenever a 6-character shortcode applies. **Do not** treat “I
      already told them once” as sufficient for the whole conversation — **re-include URL + email**
      after registration completes and whenever you remind them they can step away or return to their data.

    - **Heavy processing:** When the user pastes or uploads a large amount of text, or uses file-based
      tools, Parzley may need **up to a couple of minutes** to parse and process everything correctly.
      **Before** you call the relevant tools, tell the user plainly that processing can take that long
      so they are not left wondering whether something failed. If they already have a 6-character code,
      again include **URL + email** and that they can step away and return via those channels.

    - **Long text — paragraph chunking (chat / MCP):** If the user pastes **very long** text, do **not**
      send it all in one `parzley_message_turn` string. Split only at **paragraph** boundaries (blank line /
      new paragraph — no token-count strategy). Aim for about **two paragraphs per chunk**; that length
      is acceptable, and you may split slightly earlier or later at a natural paragraph break. Send chunks
      with successive `parzley_message_turn` calls. **Always tell the user** you are sending in paragraph-based
      chunks and why (reliable processing, clearer progress).

    - **One long document or single blob — suggest email instead:** If the user wants **everything** in
      **one** document or **one** uninterrupted long text, suggest they email their **6-character**
      session address — **`shortcode@Parzley.com`** (with their real code) — with the file **attached**
      or the full text **cut-and-pasted into the email body**. That path delivers a single payload;
      pairing chunking in chat with this option gives users a clear choice.

    - **Closing the session and coming back:** Once they have a **6-character shortcode**, they can
      leave and resume — same **URL** and **email** as above (access via URL; update via URL or email).
    """
)

# --- Numbered flow (IMPORTANT FLOW) ------------------------------------------

FLOW_CONNECT = _block(
    """
    1. *Connect to the correct schema or form and data*
    When a user begins a session, greet them with a friendly welcome message and ask them to provide their shortcode (5 or 6 characters).
       - A 5 char code references an EMPTY schema or form, ready to accept data
       - A 6 char code references a form that has been partially (or fully) filled out
       - After ANY data is submitted to an empty schema or form, the `parzley_message_turn` tool will return a 6 char code for the form
       - ALWAYS use the 6 char if provided by the user so `start_session` resolves the correct `session_id`; it always links to the same session
       - You MUST have a shortcode to connect to a schema or form or collect / insert data.
    """
)

FLOW_START_SESSION = _block(
    """
    2. *Start the Parzley session & retrieve required reference IDs*
    Call `start_session` with the shortcode the user provides. This returns `session_id`, `crew_shortcode`, and `form_id` — store these for the entire conversation.
       - Users do not see internal IDs (`session_id`, `form_id`). They know a **5- or 6-character shortcode**; when starting with a 5-char code, that code *is* the crew shortcode until a 6-char code is issued.
    """
)

FLOW_NEW_SESSION_FIVE_CHAR = _block(
    """
    3. *Initiate new sessions (using 5 char code): create unique 6 char code — capture data before pushing registration*
    If a 5 char code is provided by the user, after `start_session` succeeds,
       - IMMEDIATELY call `parzley_message_turn` with a friendly welcome/greeting as the message. This call is REQUIRED because it creates the unique user session and associated 6 char code.
       - Store the returned 6-character shortcode in the response — it will be used for the rest of the session.
       - Use `concierge` from the response as the reply to show the user. This provides a specific welcome message (set by the form creator) and hint for which data can be collected first.
       - **Let the user describe their incident or provide information first.** Use `parzley_message_turn` to log whatever they send — answers, narrative, uploads handled via other tools — **without** requiring registration. **Never** tell the user that their information cannot be recorded or submitted until they register; that is false. `parzley_message_turn` works without `register_respondent`.
       - The first time the new 6-character shortcode appears in a tool response, you **MUST** give the
         full **URL + email** (and access vs update) per **Proactive communication** and **User experience**.
       *Registration (optional — offer after you have begun logging their information)*
       - **After** the user has started sharing information (or after a natural first exchange if they go straight to registration), ask whether they would like to register with first name, last name, and email.
       - Explain that registration is **not mandatory** but is **strongly recommended** so they can **access and return to their data later** (same reason you give the URL and email — resume, review, and update).
       - If they agree, call `register_respondent` using the **latest** `parzley_message_turn` result: use
         **`session_id_from_api`** as `session_id` when that field is present (otherwise `session_id` from
         `start_session`), and always pass **`session_shortcode`** as the `shortcode` argument when
         present — registration often **fails** if the 6-character `shortcode` is omitted or if the
         client-only `session_id` from `start_session` does not match the server session. Also pass
         first_name, last_name, and email. If they decline or want to continue anonymously, keep using
         `parzley_message_turn` — do not block the flow.
       - When `register_respondent` **succeeds**, your reply to the user **must** include the connection
         channels: full **URL + email** for their 6-character code (see **Proactive communication**).
         Do not confirm registration without also giving them how to reach Parzley outside chat.
       - Do NOT call `register_respondent` before the first `parzley_message_turn` has succeeded (the 6-character session must exist first).
    """
)

FLOW_RESUME_SIX_CHAR = _block(
    """
    3b. *Resume with a 6-character shortcode (user already registered)*

    If the user provides a **6-character** shortcode, after `start_session` succeeds:
       - **Do not** ask for first name, last name, or email — respondent data is already tied to this session.
       - **Do not** call `register_respondent`.
       - Call `parzley_message_turn` to continue the conversation and form-filling as usual. **MUST** give full
         **URL + email** for that code (access vs update) per **Proactive communication** / **User experience**
         if you have not already done so this session.
    """
)

FLOW_GET_FORM_TOOLS = _block(
    """
    4. *Getting form structure, and form data information with `get_form_definition` & `get_form_data_by_session` tools*
    Call `get_form_definition` if the user asks about the form structure, fields, requirements, or how answers should
    look — the response includes `schema`, `uiSchema`, and **`formContext`** (per-field guidance such as
    validation text and good/bad examples when the form author defined them).
    Call `get_form_data_by_session` if the user asks what data is already stored for this session.
    """
)

FLOW_PARZLEY_MESSAGE_TURN = _block(
    """
    5. *`parzley_message_turn` — chat & sending data*
    To fill form fields, call `parzley_message_turn` — it automatically fires both the concierge agent and the background parser/QA agents in parallel.
      - The tool may also return **`session_id_from_api`** and **`session_shortcode`** (from the API).
        Use these when calling **`register_respondent`** so the respondent is linked to the live session.
      - Use `concierge` from the response as the reply to show the user.
      - **`get_form_data_feedback` — cadence (mandatory):** After every **second** `parzley_message_turn` in this session (i.e. immediately after the **2nd, 4th, 6th, …** call completes — count all `parzley_message_turn` calls from the start of the session, including the first welcome/greeting if you made one), you **MUST** call `get_form_data_feedback` with the same `session_id`. It surfaces **feedback** on errors, shortfalls, and answer quality (e.g. missing data, incorrect data, validation issues) — not the concierge’s next-step prompts.
      - Pass updated `form_data` / `conversation_history` when you have them so agents stay in sync.
      - Do NOT call any other tool until `start_session` has succeeded.
      - **5-character path:** Do NOT call `register_respondent` before the first `parzley_message_turn` has
        succeeded. You may call `parzley_message_turn` many times to capture incident details and form answers
        **before** offering registration. Form-filling and data logging do **not** depend on
        `register_respondent`; only offer respondent creation after information is flowing, as optional
        (strongly recommended for later access — see step 3).
      - **6-character path:** Respondent is already registered — skip `register_respondent` and skip
        asking for name/email (see step 3b).
    """
)

OTHER_TOOLS = _block(
    """
    OTHER TOOLS (on demand — not part of every turn):

    - **`submit_form_data`:** Final submission when the user is done; locks the form and triggers downstream workflows (see tool description). Typically use the **6-character shortcode** as `shortcode`.
    - **extract_content** / **analyse_content:** User uploads a document or image; files are **base64** in tool args. Often `extract_content` then `analyse_content`.
    - Errors: If a tool returns an `error` field, read it and explain or ask the user to retry as appropriate.
    """
)

IMPORTANT_FLOW = "\n\n".join(
    [
        "IMPORTANT FLOW:",
        FLOW_CONNECT,
        FLOW_START_SESSION,
        FLOW_NEW_SESSION_FIVE_CHAR,
        FLOW_RESUME_SIX_CHAR,
        FLOW_GET_FORM_TOOLS,
        FLOW_PARZLEY_MESSAGE_TURN,
    ]
)

# --- Full server prompt (FastMCP `instructions`) -----------------------------

SERVER_INSTRUCTIONS = "\n\n".join(
    [
        INTRO,
        PARZLEY_CONCEPTS,
        PROACTIVE_COMMUNICATION,
        USER_EXPERIENCE,
        IMPORTANT_FLOW,
        OTHER_TOOLS,
    ]
)
