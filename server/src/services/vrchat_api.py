"""
VRChat API client — authentication, rate limiting, and API calls.
"""

import base64
import json
import re
import threading
import time
import urllib.error
import urllib.request

from config import (
    VRCHAT_PASSWORD,
    VRCHAT_TOTP_SECRET,
    VRCHAT_USERNAME,
    VRC_STATE_FILE,
    log,
)

try:
    import pyotp
except ImportError:
    pyotp = None

# ── Constants ─────────────────────────────────────────────────────────────

VRC_GROUP_RE = re.compile(r"(grp_[0-9a-f\-]{36})", re.IGNORECASE)
_VRC_API = "https://api.vrchat.cloud/api/1"
_VRC_UA = (
    "LineupBuilder/1.2 (https://github.com/Baebu/lineup_builder) "
    "VRChat DJ event lineup tool"
)

# Rate limiter — minimum 2s between VRChat API calls
_vrc_rate_lock = threading.Lock()
_VRC_MIN_INTERVAL = 2.0  # seconds between API calls
_VRC_429_BACKOFF = 60.0  # seconds to wait after a 429
VRC_LOGIN_COOLDOWN = 300.0  # skip login on boot if last call was < 5 min ago

# Mutable auth state for VRChat session
_vrc_auth_cookie: str = ""
_vrc_auth_lock = threading.Lock()


# ── Rate-limit state persistence ──────────────────────────────────────────

def _vrc_load_state() -> tuple[float, float, str]:
    """Load last_call, backoff_until, and auth_cookie from disk."""
    try:
        data = json.loads(VRC_STATE_FILE.read_text())
        return (
            float(data.get("last_call", 0.0)),
            float(data.get("backoff_until", 0.0)),
            data.get("auth_cookie", ""),
        )
    except (FileNotFoundError, json.JSONDecodeError, ValueError):
        return 0.0, 0.0, ""


_vrc_last_call, _vrc_backoff_until, _vrc_saved_cookie = _vrc_load_state()

# Pre-load saved cookie so the first request doesn't require a re-login
if _vrc_saved_cookie:
    _vrc_auth_cookie = _vrc_saved_cookie


def _vrc_save_state():
    """Persist last_call, backoff_until, and auth_cookie to disk."""
    try:
        VRC_STATE_FILE.write_text(json.dumps({
            "last_call": _vrc_last_call,
            "backoff_until": _vrc_backoff_until,
            "auth_cookie": _vrc_auth_cookie,
        }))
    except OSError as exc:
        log.warning("Failed to save VRChat rate state: %s", exc)


def _vrc_wait():
    """Block until rate limit allows another VRChat API call."""
    global _vrc_last_call
    with _vrc_rate_lock:
        now = time.time()
        # Honour 429 backoff
        if now < _vrc_backoff_until:
            wait = _vrc_backoff_until - now
            log.info("VRChat rate-limited — waiting %.0fs", wait)
            time.sleep(wait)
            now = time.time()
        # Enforce minimum interval
        elapsed = now - _vrc_last_call
        if elapsed < _VRC_MIN_INTERVAL:
            time.sleep(_VRC_MIN_INTERVAL - elapsed)
        _vrc_last_call = time.time()
        _vrc_save_state()


def _vrc_set_backoff(retry_after: float | None = None):
    """Set a backoff period after receiving a 429."""
    global _vrc_backoff_until
    wait = retry_after if retry_after else _VRC_429_BACKOFF
    _vrc_backoff_until = time.time() + wait
    log.warning("VRChat 429 — backing off for %.0fs", wait)
    _vrc_save_state()


# ── Auth ──────────────────────────────────────────────────────────────────

def vrchat_login() -> str:
    """Authenticate with VRChat and return the auth cookie."""
    if not VRCHAT_USERNAME or not VRCHAT_PASSWORD:
        return ""

    # Step 1: Basic auth login
    creds = base64.b64encode(
        f"{VRCHAT_USERNAME}:{VRCHAT_PASSWORD}".encode()
    ).decode()
    req = urllib.request.Request(
        f"{_VRC_API}/auth/user",
        headers={
            "User-Agent": _VRC_UA,
            "Authorization": f"Basic {creds}",
        },
    )
    _vrc_wait()
    try:
        resp = urllib.request.urlopen(req, timeout=15)
        data = json.loads(resp.read())
        # Extract auth cookie from response headers
        cookies = resp.headers.get_all("Set-Cookie") or []
        auth_token = ""
        for c in cookies:
            if c.startswith("auth="):
                auth_token = c.split(";")[0].split("=", 1)[1]
                break

        if not auth_token:
            log.error("VRChat login: no auth cookie in response")
            return ""

        # Step 2: Check if 2FA is required
        requires_2fa = data.get("requiresTwoFactorAuth", [])
        if requires_2fa and "totp" in requires_2fa:
            if not pyotp:
                log.error("VRChat 2FA required but pyotp not installed")
                return ""
            if not VRCHAT_TOTP_SECRET:
                log.error("VRChat 2FA required but VRCHAT_TOTP_SECRET not set")
                return ""

            totp = pyotp.TOTP(VRCHAT_TOTP_SECRET)
            code = totp.now()

            verify_data = json.dumps({"code": code}).encode()
            verify_req = urllib.request.Request(
                f"{_VRC_API}/auth/twofactorauth/totp/verify",
                data=verify_data,
                headers={
                    "User-Agent": _VRC_UA,
                    "Content-Type": "application/json",
                    "Cookie": f"auth={auth_token}",
                },
                method="POST",
            )
            _vrc_wait()
            verify_resp = urllib.request.urlopen(verify_req, timeout=15)
            verify_json = json.loads(verify_resp.read())
            if not verify_json.get("verified"):
                log.error("VRChat 2FA verification failed")
                return ""

            # Update cookie from 2FA response if present
            for c in (verify_resp.headers.get_all("Set-Cookie") or []):
                if c.startswith("auth="):
                    auth_token = c.split(";")[0].split("=", 1)[1]
                    break

        log.info("VRChat login successful")
        return auth_token

    except urllib.error.HTTPError as exc:
        body = exc.read().decode(errors="replace")
        if exc.code == 429:
            retry_after = None
            try:
                retry_after = float(exc.headers.get("Retry-After", ""))
            except (TypeError, ValueError):
                pass
            _vrc_set_backoff(retry_after)
        log.error("VRChat login failed (%s): %s", exc.code, body[:200])
        return ""
    except Exception as exc:
        log.error("VRChat login error: %s", exc)
        return ""


def _ensure_vrchat_auth() -> str:
    """Return a valid VRChat auth cookie, logging in if needed."""
    global _vrc_auth_cookie
    with _vrc_auth_lock:
        if _vrc_auth_cookie:
            return _vrc_auth_cookie
        _vrc_auth_cookie = vrchat_login()
        return _vrc_auth_cookie


def set_auth_cookie(cookie: str):
    """Set the auth cookie and persist it to disk."""
    global _vrc_auth_cookie
    with _vrc_auth_lock:
        _vrc_auth_cookie = cookie
    _vrc_save_state()


def _invalidate_vrchat_auth():
    """Clear cached auth so the next request triggers a fresh login."""
    global _vrc_auth_cookie
    with _vrc_auth_lock:
        _vrc_auth_cookie = ""
    _vrc_save_state()


def vrchat_verify_session(cookie: str) -> bool:
    """Check if a previously-saved auth cookie is still valid."""
    if not cookie:
        return False
    req = urllib.request.Request(
        f"{_VRC_API}/auth/user",
        headers={
            "User-Agent": _VRC_UA,
            "Cookie": f"auth={cookie}",
        },
    )
    _vrc_wait()
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            # A valid session returns a user object (has 'id' field)
            return bool(data.get("id") or data.get("displayName"))
    except urllib.error.HTTPError as exc:
        if exc.code == 401:
            return False
        log.warning("VRChat session verify unexpected error %s", exc.code)
        return False
    except Exception as exc:
        log.warning("VRChat session verify failed: %s", exc)
        return False


# ── API calls ─────────────────────────────────────────────────────────────

def vrchat_get(path: str) -> dict | list | None:
    """Make an authenticated GET to VRChat API. Returns parsed JSON or None."""
    auth = _ensure_vrchat_auth()
    if not auth:
        return None
    req = urllib.request.Request(
        f"{_VRC_API}{path}",
        headers={
            "User-Agent": _VRC_UA,
            "Cookie": f"auth={auth}",
        },
    )
    _vrc_wait()
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        if exc.code == 429:
            retry_after = None
            try:
                retry_after = float(exc.headers.get("Retry-After", ""))
            except (TypeError, ValueError):
                pass
            _vrc_set_backoff(retry_after)
            log.warning("VRChat API rate-limited (%s)", path)
            return None
        if exc.code == 401:
            # Auth expired — retry once with fresh login
            _invalidate_vrchat_auth()
            retry_auth = _ensure_vrchat_auth()
            if not retry_auth:
                return None
            req.remove_header("Cookie")
            req.add_header("Cookie", f"auth={retry_auth}")
            _vrc_wait()
            try:
                with urllib.request.urlopen(req, timeout=10) as resp:
                    return json.loads(resp.read())
            except Exception as exc2:
                log.warning("VRChat API retry failed (%s): %s", path, exc2)
                return None
        log.warning("VRChat API call failed (%s): %s", path, exc)
        return None
    except (urllib.error.URLError, json.JSONDecodeError) as exc:
        log.warning("VRChat API call failed (%s): %s", path, exc)
        return None
