FROM python:3.13-slim

WORKDIR /app

COPY pyproject.toml README.md ./
COPY main.py ./
COPY parzley_mcp ./parzley_mcp

RUN pip install --no-cache-dir .

# Railway sets PORT at runtime (public networking often uses 8080). Default matches that; override locally if needed.
ENV PORT=8080
EXPOSE 8080

# Streamable HTTP (recommended for Claude.ai behind Cloudflare) — endpoint /mcp
CMD ["sh", "-c", "exec python main.py --transport http --host 0.0.0.0 --port ${PORT}"]
