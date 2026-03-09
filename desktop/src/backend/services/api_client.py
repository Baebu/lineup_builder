"""
REST API client for the Lineup Builder server.

Pure Python — no GUI imports.  Uses only stdlib (urllib) so
no extra dependencies are needed in the desktop app.
"""

import json
import logging
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

log = logging.getLogger("api-client")


class APIError(Exception):
    """Raised when the server returns a non-2xx status."""

    def __init__(self, status: int, detail: str):
        self.status = status
        self.detail = detail
        super().__init__(f"[{status}] {detail}")


class APIClient:
    """Synchronous REST client for the Lineup Builder server."""

    def __init__(self, base_url: str = "", api_key: str = ""):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key

    # ── Low-level ─────────────────────────────────────────────────────────

    def _request(
        self,
        method: str,
        path: str,
        body: dict | None = None,
        *,
        timeout: int = 15,
    ) -> Any:
        url = f"{self.base_url}{path}"
        headers = {"X-API-Key": self.api_key, "Content-Type": "application/json"}

        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(url, data=data, headers=headers, method=method)

        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as exc:
            try:
                detail = json.loads(exc.read()).get("detail", exc.reason)
            except Exception:
                detail = exc.reason
            raise APIError(exc.code, detail) from exc
        except urllib.error.URLError as exc:
            raise APIError(0, f"Connection failed: {exc.reason}") from exc

    def _get(self, path: str, **kw) -> Any:
        return self._request("GET", path, **kw)

    def _post(self, path: str, body: dict, **kw) -> Any:
        return self._request("POST", path, body, **kw)

    def _put(self, path: str, body: dict, **kw) -> Any:
        return self._request("PUT", path, body, **kw)

    # ── DJ Profile ────────────────────────────────────────────────────────

    def dj_register(self, name: str, password: str) -> dict:
        """Register a new DJ account. Returns {"id", "name"}."""
        return self._post("/dj/register", {"name": name, "password": password})

    def dj_login(self, name: str, password: str) -> dict:
        """Log in. Returns {"id", "name"}."""
        return self._post("/dj/login", {"name": name, "password": password})

    def dj_discord_auth(self, discord_id: str, name: str) -> dict:
        """Register or sign in a DJ via Discord identity. Returns {"id", "name"}."""
        return self._post("/dj/discord-auth", {"discord_id": discord_id, "name": name})

    def dj_get_profile(self, name: str) -> dict:
        """Fetch a DJ profile (public info). Returns {id, name, links, logo, availability}."""
        encoded = urllib.parse.quote(name, safe="")
        return self._get(f"/dj/profile/{encoded}")

    def dj_update_profile(
        self,
        name: str,
        *,
        links: dict | None = None,
        logo: str = "",
        genres: list | None = None,
        availability: list | None = None,
    ) -> dict:
        """Update a DJ's links, logo, genres, and availability."""
        return self._put("/dj/profile", {
            "name": name,
            "links": links or {},
            "logo": logo,
            "genres": genres or [],
            "availability": availability or [],
        })

    def dj_list(self) -> list[dict]:
        """List all registered DJs (public info)."""
        return self._get("/dj/list")

    # ── Bookings ──────────────────────────────────────────────────────────

    def create_booking(
        self,
        *,
        dj_name: str,
        group_name: str = "",
        event_title: str = "",
        event_date: str = "",
        start_time: str = "",
        duration: int = 60,
        message: str = "",
        discord_channel_id: int | None = None,
    ) -> dict:
        """Create a booking request for a DJ. Returns {"id", "status": "pending"}."""
        body: dict = {
            "dj_name": dj_name,
            "group_name": group_name,
            "event_title": event_title,
            "event_date": event_date,
            "start_time": start_time,
            "duration": duration,
            "message": message,
        }
        if discord_channel_id is not None:
            body["discord_channel_id"] = discord_channel_id
        return self._post("/booking", body)

    def list_dj_bookings(self, dj_name: str) -> list[dict]:
        """List all bookings for a DJ."""
        encoded = urllib.parse.quote(dj_name, safe="")
        return self._get(f"/bookings/dj/{encoded}")

    def respond_to_booking(self, booking_id: int, status: str) -> dict:
        """Accept or decline a booking. status = 'accepted' | 'declined'."""
        return self._put(f"/booking/{booking_id}/respond", {"status": status})

    def list_group_bookings(self, group_name: str) -> list[dict]:
        """List all bookings created by a specific group."""
        encoded = urllib.parse.quote(group_name, safe="")
        return self._get(f"/bookings/group/{encoded}")

    # ── User cloud data ───────────────────────────────────────────────────

    def get_user_data(self, discord_id: str, key: str) -> dict | list:
        """Fetch a single data blob (library/events/settings) for a Discord user."""
        resp = self._get(f"/user/{discord_id}/data/{key}")
        return resp.get("value", {})

    def put_user_data(self, discord_id: str, key: str, value: dict | list) -> dict:
        """Save a data blob for a Discord user."""
        return self._put(f"/user/{discord_id}/data/{key}", {"value": value})

    def get_all_user_data(self, discord_id: str) -> dict:
        """Fetch all data blobs for a Discord user. Returns {"library": ..., "events": ..., ...}."""
        resp = self._get(f"/user/{discord_id}/data")
        return resp.get("data", {})

    # ── VRChat ────────────────────────────────────────────────────────────

    def verify_vrchat_bio(self, vrchat_username: str, verification_code: str) -> dict:
        """Check a VRChat user's bio for verification code and return owned groups."""
        return self._post("/vrchat/verify-bio", {
            "vrchat_username": vrchat_username,
            "verification_code": verification_code,
        })

    def verify_vrchat_group(self, group_id: str, discord_id: str) -> dict:
        """Verify a VRChat group by ID and link it to a Discord user."""
        return self._post("/vrchat/verify-group", {
            "group_id": group_id,
            "discord_id": discord_id,
        })

    def get_vrchat_group(self, discord_id: str) -> dict:
        """Get the stored VRChat group link for a Discord user."""
        return self._get(f"/user/{discord_id}/vrchat-group")
