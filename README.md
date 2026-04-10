# Parzley MCP Server

Exposes the [Parzley](https://api.parzley.com) AI Form Filling Agent API
as an MCP server — enabling Claude Desktop, Claude.ai, and any MCP-compatible
client to interact with Parzley natively via natural language.

**Requires Python 3.13+** (see `pyproject.toml`).

---

## Quick start

### 1. Install the package

From the repository root (use a virtual environment):

```bash
pip install .
```

Or with [uv](https://docs.astral.sh/uv/):

```bash
uv sync
```

Dependencies: `fastmcp`, `httpx` (declared in `pyproject.toml`).

If you change **`pyproject.toml`** dependencies, run **`uv lock`** and commit the updated **`uv.lock`**. Hosts that run **`uv sync --locked`** (e.g. Railway Railpack) will fail until the lockfile matches.

---

## Connecting to Claude Desktop (local / stdio)

The server entry point is **`main.py`** (not the legacy commented `parzley_mcp_server.py`).

Add the following to your Claude Desktop config file:

- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "parzley": {
      "command": "python",
      "args": ["C:/path/to/Parzley_MCP/main.py"]
    }
  }
}
```

> **Note:** Use the full path to your clone of this repo. `command` must be a **Python 3.13+** interpreter (`where python` / `which python3`). On Windows, forward slashes in `args` are fine.

Restart Claude Desktop completely (quit fully, then reopen). The Parzley tools will
appear as a 🔧 hammer icon in the chat input bar.

---

## Connecting to Claude.ai (remote)

**Streamable HTTP** (recommended; works through Cloudflare) — endpoint **`/mcp`**:

```bash
python main.py --transport http --port 8001
```

Then in Claude.ai → **Settings → Integrations → Add MCP Server**:

- **URL**: `https://your-domain.com:8001/mcp`

**SSE** (legacy; some setups need Cloudflare proxy adjustments) — endpoint **`/sse`**:

```bash
python main.py --transport sse --port 8001
```

- **URL**: `https://your-domain.com:8001/sse`

---

### Railway (or any PaaS)

Deploy is **not** configured in-repo — set this in your host’s UI (example for [Railway](https://railway.app/)):

1. **Builder:** **Nixpacks** (or Railpack), **not** Dockerfile unless you add your own `Dockerfile`.
2. **Install:** Let Nixpacks auto-detect `pyproject.toml`, or use a custom install step such as `python -m pip install .` from the repo root.
3. **Start command:** `python main.py --transport http --host 0.0.0.0`
4. **Port:** The platform sets **`PORT`** (e.g. 8080). **`main.py`** reads **`PORT`** from the environment so you do not need `--port` in the start command.

MCP URL: `https://<your-app>/mcp` (HTTPS on the host; no port in the URL for a default HTTPS setup).

If deploy still says **“Build image”** or Docker, switch the service **off** Dockerfile builder in settings — this repo does not ship a `Dockerfile`.

---

## Available tools (9 total)

| Tool | Description |
|---|---|
| `start_session` | Resolve a shortcode and start a new form-filling session. Must be called first. |
| `parzley_message_turn` | Single MCP call that runs `concierge_chat` and `chat_with_agents` in parallel — use on every user message after `start_session`. |
| `register_respondent` | Link name + email to the session. **Optional** in chat — **strongly recommended** so the user can open and manage their answers in the **Parzley web app** (browser access is tied to that email). Call after the first successful `parzley_message_turn` when the user agrees. |
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

| Length | Role | Behaviour |
|---|---|---|
| **5 chars** | Crew / empty template | Identifies the **empty** form for that crew; `start_session` starts work against that template. Sending data via `parzley_message_turn` creates a **6-character** session. |
| **6 chars** | Session + saved data | Identifies a specific form instance and answers. Resolved via the API to `crew_shortcode` and `session_id` for resume. |

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

## Smoke test (optional)

After install:

```bash
python -m unittest tests.test_smoke -v
```

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
| `ModuleNotFoundError` | Run `pip install .` from the project root (Python 3.13+) |
| Server crashes on start | Run `python main.py` in a terminal to see the error |
| **502** on Railway / reverse proxy | Confirm **`main.py`** is running, **`PORT`** matches the platform, and the start command is correct (see **Railway** above). |
| File upload fails | Ensure the file is properly base64-encoded and `file_name` has the correct extension |
