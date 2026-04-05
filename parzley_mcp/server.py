"""
FastMCP application instance with system-level instructions.
"""

from fastmcp import FastMCP

mcp = FastMCP(
    name="Parzley",
    instructions="""
        You have access to Parzley — an AI-powered form filling platform.
        IMPORTANT FLOW:
        1. When a user first connects, greet them with a welcome message and ask them to
           provide their shortcode (5 or 6 characters).
           - A 5 char code references an EMPTY form, ready to accept data
           - A 6 char code references a form that has been fully or partially filled out
           - After ANY data is submitted to the form the `send_message` tool will return
             the 6 char code for the form
           - ALWAYS use the 6 char if it exists to return the session_id
           - The 6 char code will always link to the same session_id
        2. Call `start_session` with the shortcode they provide. This returns
           `session_id`, `crew_shortcode`, and `form_id` — store these for the entire
           conversation.
        3. The `form_id` is included in the `start_session` response for both shortcode
           types. Only call `get_form` if the user explicitly asks about the form
           structure, fields, or requirements (e.g. "how many fields?", "what does this
           form ask?"). Only call `get_form_data_by_session` if the user asks what they
           have already filled in.
        4. On EVERY subsequent user message, call `send_message` — it automatically
           fires both the concierge agent and the background parser/QA agents in
           parallel. Use `concierge` from the response as the reply to show the user.
        Do NOT call any other tool until `start_session` has succeeded.
    """,
)

