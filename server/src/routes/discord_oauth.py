"""
Discord OAuth2 routes — login URL generation and callback handler.

These routes are PUBLIC (no API key required) because:
  - /api/discord/login-url is called by the browser
  - /api/discord/callback is the OAuth redirect target
"""

import secrets
import urllib.parse

import httpx
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse

from config import DISCORD_CLIENT_ID, DISCORD_CLIENT_SECRET, DISCORD_REDIRECT_URI, log

router = APIRouter(prefix="/api/discord")

DISCORD_AUTH_URL = "https://discord.com/api/oauth2/authorize"
DISCORD_TOKEN_URL = "https://discord.com/api/oauth2/token"
DISCORD_USER_URL = "https://discord.com/api/users/@me"

# In-memory state store (CSRF protection). Maps state → True.
_pending_states: dict[str, bool] = {}


@router.get("/login-url")
async def get_login_url():
    """Generate a Discord OAuth2 authorization URL."""
    if not DISCORD_CLIENT_ID:
        raise HTTPException(status_code=503, detail="Discord OAuth not configured (missing client ID)")

    state = secrets.token_urlsafe(32)
    _pending_states[state] = True

    # Limit stored states to prevent unbounded growth
    if len(_pending_states) > 500:
        oldest = list(_pending_states.keys())[: len(_pending_states) - 500]
        for k in oldest:
            _pending_states.pop(k, None)

    params = {
        "client_id": DISCORD_CLIENT_ID,
        "redirect_uri": DISCORD_REDIRECT_URI,
        "response_type": "code",
        "scope": "identify",
        "state": state,
    }
    url = f"{DISCORD_AUTH_URL}?{urllib.parse.urlencode(params)}"
    return {"url": url}


@router.get("/callback", response_class=HTMLResponse)
async def oauth_callback(code: str = "", state: str = "", error: str = ""):
    """Handle Discord OAuth2 redirect. Exchanges code for token,
    fetches user profile, and sends data back to the opener via postMessage."""

    if error:
        return _error_page(f"Discord denied access: {error}")

    if not code or not state:
        return _error_page("Missing authorization code or state parameter.")

    if state not in _pending_states:
        return _error_page("Invalid or expired state parameter. Please try again.")

    _pending_states.pop(state, None)

    # Exchange code for access token
    try:
        async with httpx.AsyncClient() as client:
            token_resp = await client.post(
                DISCORD_TOKEN_URL,
                data={
                    "client_id": DISCORD_CLIENT_ID,
                    "client_secret": DISCORD_CLIENT_SECRET,
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": DISCORD_REDIRECT_URI,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            if token_resp.status_code != 200:
                log.error("Discord token exchange failed: %s %s", token_resp.status_code, token_resp.text)
                return _error_page("Failed to exchange authorization code.")

            token_data = token_resp.json()
            access_token = token_data.get("access_token")
            if not access_token:
                return _error_page("No access token received from Discord.")

            # Fetch user profile
            user_resp = await client.get(
                DISCORD_USER_URL,
                headers={"Authorization": f"Bearer {access_token}"},
            )
            if user_resp.status_code != 200:
                log.error("Discord user fetch failed: %s %s", user_resp.status_code, user_resp.text)
                return _error_page("Failed to fetch Discord user profile.")

            user = user_resp.json()

    except httpx.HTTPError as exc:
        log.exception("Discord OAuth HTTP error: %s", exc)
        return _error_page("Network error communicating with Discord.")

    discord_id = user.get("id", "")
    username = user.get("global_name") or user.get("username", "")
    avatar = user.get("avatar", "")

    log.info("Discord OAuth success: %s (%s)", username, discord_id)

    # Return HTML that posts user data back to the opener window and closes
    return HTMLResponse(f"""<!DOCTYPE html>
<html><head><title>Signing in…</title></head>
<body>
<p>Signing in… this window will close automatically.</p>
<script>
  if (window.opener) {{
    window.opener.postMessage({{
      type: "discord_auth",
      discord_id: {_js_str(discord_id)},
      username: {_js_str(username)},
      avatar: {_js_str(avatar)}
    }}, "*");
  }}
  window.close();
</script>
</body></html>""")


def _error_page(message: str) -> HTMLResponse:
    """Return a simple error page that closes the popup."""
    safe = message.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return HTMLResponse(f"""<!DOCTYPE html>
<html><head><title>Sign-in Error</title></head>
<body>
<p style="color:red;">{safe}</p>
<p>You can close this window and try again.</p>
<script>setTimeout(() => window.close(), 5000);</script>
</body></html>""", status_code=400)


def _js_str(value: str) -> str:
    """Safely encode a string for inline JS."""
    return (
        '"' + value
        .replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
        .replace("\r", "\\r")
        .replace("<", "\\x3c")
        .replace(">", "\\x3e")
        + '"'
    )
