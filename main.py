"""
Parzley MCP Server — entry point.

Run (stdio — for Claude Desktop):
    python main.py

Run (HTTP/Streamable — for Claude.ai remote, works through Cloudflare):
    python main.py --transport http --port 8001
    → endpoint: http://host:8001/mcp

Run (SSE — legacy, requires Cloudflare proxy OFF):
    python main.py --transport sse --port 8001
    → endpoint: http://host:8001/sse
"""

import argparse
import os

# Import the FastMCP instance — this also triggers all tool registrations
from parzley_mcp.server import mcp
import parzley_mcp.tools  # noqa: F401 — registers all @mcp.tool() decorators


def _default_listen_port() -> int:
    """Railway, Render, Fly, etc. set PORT; use it when present."""
    raw = os.environ.get("PORT")
    if raw:
        try:
            return int(raw)
        except ValueError:
            pass
    return 8001


def main() -> None:
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
        default=_default_listen_port(),
        help="Port for SSE/HTTP transport (default: $PORT if set, else 8001)",
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


if __name__ == "__main__":
    main()

