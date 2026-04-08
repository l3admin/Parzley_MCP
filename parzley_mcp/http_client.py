"""
HTTP helpers for making authenticated and public requests to the Parzley API.
"""

import httpx
from parzley_mcp.config import BASE_URL


def _headers(auth: bool = True) -> dict:
    """Build request headers, optionally including the bearer token."""
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    # if auth:
    #     token = os.environ.get("PARZLEY_API_KEY", "")
    #     if token:
    #         headers["Authorization"] = f"Bearer {token}"
    return headers


async def _get(path: str, *, auth: bool = True) -> dict:
    """Perform an authenticated (or public) GET request."""
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.get(f"{BASE_URL}{path}", headers=_headers(auth))
        resp.raise_for_status()
        return resp.json()


async def _post(path: str, payload: dict | None, *, auth: bool = True) -> dict:
    """Perform an authenticated (or public) POST request.

    ``payload=None`` sends a JSON body of ``null`` (e.g. when a field is optional on the API).
    """
    async with httpx.AsyncClient(timeout=60) as client:
        if payload is None:
            resp = await client.post(
                f"{BASE_URL}{path}",
                content=b"null",
                headers=_headers(auth),
            )
        else:
            resp = await client.post(
                f"{BASE_URL}{path}",
                json=payload,
                headers=_headers(auth),
            )
        resp.raise_for_status()
        return resp.json()

