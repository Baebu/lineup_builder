"""
VRChat routes — bio verification, group linking.
"""

import asyncio
import json
import urllib.parse

from fastapi import APIRouter, HTTPException

from config import VRCHAT_USERNAME
from db import get_db
from models.schemas import VRChatGroupVerifyRequest, VRChatVerifyBioRequest
from services.vrchat_api import VRC_GROUP_RE, vrchat_get

router = APIRouter()


@router.post("/vrchat/verify-bio")
async def vrchat_verify_bio(req: VRChatVerifyBioRequest):
    """Search for a VRChat user, check their bio for a verification code,
    and return their owned groups if verified."""
    if not VRCHAT_USERNAME:
        raise HTTPException(status_code=503, detail="VRChat API not configured on the server")

    username = req.vrchat_username.strip()
    code = req.verification_code.strip()
    if not username:
        raise HTTPException(status_code=400, detail="VRChat username is required")
    if not code:
        raise HTTPException(status_code=400, detail="Verification code is required")

    loop = asyncio.get_event_loop()

    # Search for the user
    search_path = f"/users?search={urllib.parse.quote(username)}&n=5"
    results = await loop.run_in_executor(None, vrchat_get, search_path)
    if not results:
        raise HTTPException(status_code=404, detail="No VRChat users found matching that name.")

    # Find exact match (case-insensitive)
    user = None
    for u in results:
        if u.get("displayName", "").lower() == username.lower():
            user = u
            break
    if not user:
        user = results[0]

    user_id = user.get("id", "")
    if not user_id:
        raise HTTPException(status_code=404, detail="Could not resolve VRChat user")

    # Fetch full user profile (bio is on the detail endpoint)
    user_detail = await loop.run_in_executor(None, vrchat_get, f"/users/{user_id}")
    if not user_detail:
        raise HTTPException(status_code=502, detail="Failed to fetch VRChat user profile")

    bio = user_detail.get("bio", "") or ""
    if code not in bio:
        raise HTTPException(
            status_code=403,
            detail=f"Verification code not found in {user.get('displayName', username)}'s bio. "
                   "Please add the code to your VRChat bio and try again.",
        )

    # Bio verified — fetch owned groups
    groups = await loop.run_in_executor(None, vrchat_get, f"/users/{user_id}/groups")
    if groups is None:
        raise HTTPException(status_code=502, detail="Failed to fetch VRChat groups")

    owned = []
    for g in groups:
        if g.get("ownerId") == user_id:
            owned.append({
                "group_id": g.get("id", ""),
                "group_name": g.get("name", ""),
                "short_code": g.get("shortCode", ""),
                "member_count": g.get("memberCount", 0),
                "banner_url": g.get("bannerUrl", ""),
                "icon_url": g.get("iconUrl", ""),
            })

    return {
        "vrchat_user_id": user_id,
        "vrchat_display_name": user_detail.get("displayName", ""),
        "owned_groups": owned,
    }


@router.post("/vrchat/verify-group")
async def vrchat_verify_group(req: VRChatGroupVerifyRequest):
    """Verify a VRChat group by ID and link it to a Discord user."""
    group_id = req.group_id.strip()
    if not VRC_GROUP_RE.match(group_id):
        raise HTTPException(status_code=400, detail="Invalid VRChat group ID")

    if not VRCHAT_USERNAME:
        raise HTTPException(
            status_code=503,
            detail="VRChat API not configured on the server",
        )

    loop = asyncio.get_event_loop()
    data = await loop.run_in_executor(None, vrchat_get, f"/groups/{group_id}")
    if not data:
        raise HTTPException(status_code=404, detail="VRChat group not found")

    # Store the verified link
    db = await get_db()
    link_data = {
        "group_id": data.get("id", group_id),
        "group_name": data.get("name", ""),
        "short_code": data.get("shortCode", ""),
        "owner_id": data.get("ownerId", ""),
        "member_count": data.get("memberCount", 0),
        "banner_url": data.get("bannerUrl", ""),
        "icon_url": data.get("iconUrl", ""),
    }
    await db.execute(
        """INSERT INTO user_data (discord_id, key, value, updated_at)
           VALUES (?, 'vrchat_group', ?, datetime('now'))
           ON CONFLICT(discord_id, key) DO UPDATE
           SET value = excluded.value, updated_at = excluded.updated_at""",
        (req.discord_id, json.dumps(link_data)),
    )
    await db.commit()
    return link_data


@router.get("/user/{discord_id}/vrchat-group")
async def get_vrchat_group(discord_id: str):
    """Get the stored VRChat group link for a Discord user."""
    db = await get_db()
    rows = await db.execute_fetchall(
        "SELECT value FROM user_data WHERE discord_id = ? AND key = 'vrchat_group'",
        (discord_id,),
    )
    if not rows:
        return {}
    return json.loads(rows[0][0])
