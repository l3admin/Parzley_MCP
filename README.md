# Parzley MCP Server

Exposes the [Parzley](https://api.parzley.com) AI Form Filling Agent API
as an MCP server — enabling Claude Desktop, Claude.ai, and any MCP-compatible
client to interact with Parzley natively via natural language.

---

## Quick start

### 1. Install dependencies

```bash
uv add fastmcp httpx
```

---

## Connecting to Claude Desktop (local / stdio)

Add the following to your Claude Desktop config file:

- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "parzley": {
      "command": "/opt/homebrew/bin/python3.11",
      "args": ["/Users/diganto/Downloads/mcp files/parzley_mcp_server.py"]
    }
  }
}
```

> **Note:** Replace `command` with your actual Python binary path (`which python3`).

Restart Claude Desktop completely (`Cmd+Q` then reopen). The Parzley tools will
appear as a 🔧 hammer icon in the chat input bar.

---

## Connecting to Claude.ai (remote / SSE)

Run the server in SSE mode:

```bash
python parzley_mcp_server.py --transport sse --port 8001
```

Then in Claude.ai → **Settings → Integrations → Add MCP Server**:
- **URL**: `https://your-domain.com:8001/sse`

### Docker (recommended for production)

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY parzley_mcp_server.py ./
RUN pip install fastmcp httpx
EXPOSE 8001
CMD ["python", "parzley_mcp_server.py", "--transport", "sse", "--port", "8001"]
```

```bash
docker build -t parzley-mcp .
docker run -p 8001:8001 parzley-mcp
```

---

## Available tools (9 total)

| Tool | Description |
|---|---|
| `start_session` | Resolve a shortcode and start a new form-filling session. Must be called first. |
| `parzley_message_turn` | Single MCP call that runs `concierge_chat` and `chat_with_agents` in parallel — use on every user message after `start_session`. |
| `register_respondent` | Optional: register name and email for the session (after the first `parzley_message_turn` when the user agrees). |
| `get_form_definition` | Fetch the full form definition (`schema`, `uiSchema`, `formContext`, etc.) for a `form_id`. |
| `get_form_data_by_session` | Fetch field values already saved for a `session_id`. |
| `get_form_data_feedback` | Feedback on form data quality, gaps, and validation for the session (errors and shortfalls vs concierge “what to ask next”). |
| `submit_form_data` | Final submission (locks the form); use the 6-character session `shortcode`. |
| `extract_content` | Upload a file (PDF or image) to extract raw text / vision description via LlamaParse or VisionAgent (Groq). |
| `analyse_content` | Upload a file and analyse its content against a user query to map data to form fields. |

---

## Session flow

```
User provides shortcode
        │
        ▼
  start_session(shortcode)
  ── returns session_id + crew_shortcode
        │
        ▼
  On EVERY user message:
        parzley_message_turn(session_id, …)  ← MCP tool; runs concierge_chat + chat_with_agents in parallel
        │
        ▼
  get_form_data_feedback(session_id)
  ── returns structured document output
```

### Shortcode types

| Length | Type | Behaviour |
|---|---|---|
| **5 chars** | Crew shortcode | Used directly; a new `session_id` is generated automatically |
| **6 chars** | Temporary / shared shortcode | Resolved via `GET /shortcodes/{shortcode}` to get both `crew_shortcode` and `session_id` |

---

## File upload tools

Both `extract_content` and `analyse_content` accept files as **base64-encoded strings**
and send them to Parzley as `multipart/form-data` with the raw binary.

**`extract_content`** — required fields:

| Field | Type | Description |
|---|---|---|
| `file_base64` | string | Base64-encoded file contents |
| `file_name` | string | Original filename with extension (e.g. `resume.pdf`) |
| `session_id` | string | Session ID from `start_session` |
| `form_id` | string | Form ID to extract content for |

**`analyse_content`** — required + optional fields:

| Field | Type | Required | Description |
|---|---|---|---|
| `file_base64` | string | ✅ | Base64-encoded file contents |
| `file_name` | string | ✅ | Original filename with extension |
| `session_id` | string | ✅ | Session ID from `start_session` |
| `user_query` | string | ✅ | Query describing what to extract / analyse |
| `form_id` | string | ❌ | Form ID to analyse content against |
| `extraction_field` | string | ❌ | Specific field to target for extraction |

---

## Typical Claude conversation

Once connected, try:

> *"I'd like to fill a form"*

Claude will:
1. Ask for your shortcode
2. Call `start_session` with the shortcode you provide
3. Store `session_id` and `crew_shortcode` for the session
4. Call `parzley_message_turn` on every message (it runs the concierge + agent APIs in parallel)
5. Guide you through the form question by question
6. Call `get_form_data_feedback` when you need structured feedback on data quality / gaps

---

## Notes

- **Timeouts**: File upload tools (`extract_content`, `analyse_content`) use a
  120-second timeout. All other tools use 60 seconds.
- **Parallel calls**: The `parzley_message_turn` tool invokes both HTTP endpoints together; do not call them separately from MCP.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| Tools don't appear in Claude | Check the config file path, quit and fully reopen Claude Desktop |
| `ModuleNotFoundError` | Run `uv add fastmcp httpx` inside the project directory |
| Server crashes on start | Run `python parzley_mcp_server.py` directly in terminal to see the error |
| File upload fails | Ensure the file is properly base64-encoded and `file_name` has the correct extension |
