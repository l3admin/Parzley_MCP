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

## Available tools (7 total)

| Tool | Description |
|---|---|
| `start_session` | Resolve a shortcode and start a new form-filling session. Must be called first. |
| `concierge_chat` | Chat with the AI concierge agent to guide the user through filling the form. Call on every user message. |
| `chat_with_agents` | Send a message to the parallel parser + QA agent pipeline. Call alongside `concierge_chat` on every user message. |
| `get_editor_suggestion` | Retrieve the current structured document output for a session. |
| `extract_content` | Upload a file (PDF or image) to extract raw text / vision description via LlamaParse or VisionAgent (Groq). |
| `analyse_content` | Upload a file and analyse its content against a user query to map data to form fields. |
| `submit_response_display` | Push rendered output/display data for a shortcode after a session completes. |

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
  On EVERY user message (in parallel):
  ┌─────────────────────────────────┐
  │  concierge_chat(session_id, …)  │  ← collects answers, drives the form
  │  chat_with_agents(session_id, …)│  ← parser + QA agents
  └─────────────────────────────────┘
        │
        ▼
  get_editor_suggestion(session_id)
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
4. Call `concierge_chat` + `chat_with_agents` in parallel on every message
5. Guide you through the form question by question
6. Call `get_editor_suggestion` to retrieve the final structured output

---

## Notes

- **Timeouts**: File upload tools (`extract_content`, `analyse_content`) use a
  120-second timeout. All other tools use 60 seconds.
- **Parallel calls**: `concierge_chat` and `chat_with_agents` **must** be called
  simultaneously on every user message — never one without the other.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| Tools don't appear in Claude | Check the config file path, quit and fully reopen Claude Desktop |
| `ModuleNotFoundError` | Run `uv add fastmcp httpx` inside the project directory |
| Server crashes on start | Run `python parzley_mcp_server.py` directly in terminal to see the error |
| File upload fails | Ensure the file is properly base64-encoded and `file_name` has the correct extension |
