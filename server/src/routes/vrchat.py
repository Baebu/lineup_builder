"""
VRChat routes — bio verification, group linking.
"""

import asyncio
import urllib.parse

from fastapi import APIRouter, HTTPException

from config import VRCHAT_USERNAME
from db import clubs, _now
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

    return {
        "vrchat_user_id": user_id,
        "vrchat_display_name": user_detail.get("displayName", ""),
    }


@router.post("/vrchat/verify-group")
async def vrchat_verify_group(req: VRChatGroupVerifyRequest):
    """Verify a VRChat group by ID and confirm ownership via the verified VRChat user ID."""
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

    # Confirm ownership: group.ownerId must match the bio-verified VRChat user ID
    owner_id = data.get("ownerId", "")
    if owner_id != req.vrchat_user_id:
        raise HTTPException(
            status_code=403,
            detail="You are not the owner of that VRChat group.",
        )

    short_code = data.get("shortCode", "") + (
        "." + data["discriminator"] if data.get("discriminator") else ""
    )

    # Upsert the verified link in the clubs collection
    await clubs().update_one(
        {"discord_id": req.discord_id},
        {"$set": {
            "vrchat_group_id": data.get("id", group_id),
            "vrchat_group_name": data.get("name", ""),
            "vrchat_short_code": short_code,
            "vrchat_owner_id": data.get("ownerId", ""),
            "vrchat_member_count": data.get("memberCount", 0),
            "vrchat_icon_url": data.get("iconUrl", ""),
            "vrchat_banner_url": data.get("bannerUrl", ""),
            "updated_at": _now(),
        }},
        upsert=True,
    )

    return {
        "group_id":     data.get("id", group_id),
        "group_name":   data.get("name", ""),
        "short_code":   short_code,
        "owner_id":     data.get("ownerId", ""),
        "member_count": data.get("memberCount", 0),
        "banner_url":   data.get("bannerUrl", ""),
        "icon_url":     data.get("iconUrl", ""),
    }


@router.get("/user/{discord_id}/vrchat-group")
async def get_vrchat_group(discord_id: str):
    """Get the stored VRChat group link for a Discord user."""
    doc = await clubs().find_one({
        "discord_id": discord_id,
        "vrchat_group_id": {"$nin": [None, ""]},
    })
    if not doc:
        return {}
    return {
        "group_id":     doc.get("vrchat_group_id", ""),
        "group_name":   doc.get("vrchat_group_name", ""),
        "short_code":   doc.get("vrchat_short_code", ""),
        "owner_id":     doc.get("vrchat_owner_id", ""),
        "member_count": doc.get("vrchat_member_count", 0),
        "icon_url":     doc.get("vrchat_icon_url", ""),
        "banner_url":   doc.get("vrchat_banner_url", ""),
    }


@router.get("/vrchat/user/{vrchat_user_id}/groups")
async def get_vrchat_user_groups(vrchat_user_id: str):
    """Return VRChat groups owned by the given user.

    Fetches all groups the user is a member of via GET /users/{id}/groups, then
    filters to those where ownerId matches the user — there is no dedicated
    'owned groups' endpoint in the VRChat API.
    """
    if not VRCHAT_USERNAME:
        raise HTTPException(status_code=503, detail="VRChat API not configured on the server")

    loop = asyncio.get_event_loop()
    groups = await loop.run_in_executor(None, vrchat_get, f"/users/{vrchat_user_id}/groups")
    if groups is None:
        raise HTTPException(status_code=502, detail="Failed to fetch VRChat groups")

    # Filter to groups the user owns — ownerId must match their verified VRChat user ID
    return [
        {
            "groupId": g.get("groupId", ""),
            "name": g.get("name", ""),
            "shortCode": g.get("shortCode", "") + ("." + g["discriminator"] if g.get("discriminator") else ""),
            "memberCount": g.get("memberCount", 0),
        }
        for g in groups
        if g.get("groupId") and g.get("ownerId") == vrchat_user_id
    ]
