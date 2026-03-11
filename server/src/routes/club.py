"""
Club routes — manage a user's club data (Discord link, etc.).
VRChat group data lives in the same clubs collection but is written by vrchat.py.
"""

import asyncio

from fastapi import APIRouter, HTTPException

from config import VRCHAT_USERNAME
from db import clubs, _now
from models.schemas import ClubUpdate
from services.vrchat_api import vrchat_get

router = APIRouter()

_CLUB_DEFAULTS = {
    "discord_id": "",
    "discord_link": "",
    "vrchat_group_id": "",
    "vrchat_group_name": "",
    "vrchat_short_code": "",
    "vrchat_owner_id": "",
    "vrchat_member_count": 0,
    "vrchat_icon_url": "",
    "vrchat_banner_url": "",
}


@router.get("/user/{discord_id}/club")
async def get_club(discord_id: str):
    """Return the club record for a Discord user, or empty defaults if none exists."""
    doc = await clubs().find_one({"discord_id": discord_id})
    if not doc:
        return {**_CLUB_DEFAULTS, "discord_id": discord_id}

    short_code = doc.get("vrchat_short_code", "")
    group_id = doc.get("vrchat_group_id", "")

    # Backfill: if short_code is missing the discriminator (no "."), fetch from VRChat API
    if group_id and short_code and "." not in short_code and VRCHAT_USERNAME:
        try:
            loop = asyncio.get_event_loop()
            data = await loop.run_in_executor(None, vrchat_get, f"/groups/{group_id}")
            if data and data.get("shortCode") and data.get("discriminator"):
                short_code = f"{data['shortCode']}.{data['discriminator']}"
                await clubs().update_one(
                    {"discord_id": discord_id},
                    {"$set": {"vrchat_short_code": short_code, "updated_at": _now()}},
                )
        except Exception:
            pass  # keep old value on failure

    return {
        "discord_id": discord_id,
        "discord_link": doc.get("discord_link", ""),
        "vrchat_group_id": group_id,
        "vrchat_group_name": doc.get("vrchat_group_name", ""),
        "vrchat_short_code": short_code,
        "vrchat_owner_id": doc.get("vrchat_owner_id", ""),
        "vrchat_member_count": doc.get("vrchat_member_count", 0),
        "vrchat_icon_url": doc.get("vrchat_icon_url", ""),
        "vrchat_banner_url": doc.get("vrchat_banner_url", ""),
    }


@router.put("/user/{discord_id}/club")
async def update_club(discord_id: str, req: ClubUpdate):
    """Create or update the club's Discord link for a Discord user."""
    await clubs().update_one(
        {"discord_id": discord_id},
        {"$set": {"discord_link": req.discord_link, "updated_at": _now()}},
        upsert=True,
    )
    return {"status": "saved"}
