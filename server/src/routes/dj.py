"""
DJ profile routes — register, login, profile CRUD, discord-auth.
"""

import bcrypt
from fastapi import APIRouter, HTTPException
from pymongo.collation import Collation

from db import dj_profiles, next_id, _now
from models.schemas import (
    DJDiscordAuthRequest,
    DJLoginRequest,
    DJProfileUpdate,
    DJRegisterRequest,
)

router = APIRouter()

_CI = Collation(locale="en", strength=2)  # case-insensitive


@router.post("/dj/register")
async def dj_register(req: DJRegisterRequest):
    if not req.name or not req.password:
        raise HTTPException(status_code=400, detail="Name and password are required")
    if len(req.password) < 4:
        raise HTTPException(status_code=400, detail="Password must be at least 4 characters")

    hashed = bcrypt.hashpw(req.password.encode(), bcrypt.gensalt()).decode()
    dj_id = await next_id("dj_profiles")
    try:
        await dj_profiles().insert_one({
            "id": dj_id,
            "name": req.name,
            "password": hashed,
            "discord_id": "",
            "links": {},
            "logo": "",
            "genres": [],
            "availability": [],
            "bio": "",
            "display_name": "",
            "created_at": _now(),
            "updated_at": _now(),
        })
    except Exception:
        raise HTTPException(status_code=409, detail="DJ name already taken")

    return {"id": dj_id, "name": req.name}


@router.post("/dj/login")
async def dj_login(req: DJLoginRequest):
    doc = await dj_profiles().find_one({"name": req.name}, collation=_CI)
    if not doc:
        raise HTTPException(status_code=401, detail="Invalid name or password")

    if not bcrypt.checkpw(req.password.encode(), doc["password"].encode()):
        raise HTTPException(status_code=401, detail="Invalid name or password")

    return {"id": doc["id"], "name": doc["name"]}


@router.get("/dj/profile/{name}")
async def dj_get_profile(name: str):
    doc = await dj_profiles().find_one({"name": name}, collation=_CI)
    if not doc:
        raise HTTPException(status_code=404, detail="DJ not found")
    return {
        "id": doc["id"],
        "name": doc["name"],
        "links": doc.get("links", {}),
        "logo": doc.get("logo", ""),
        "genres": doc.get("genres", []),
        "availability": doc.get("availability", []),
        "bio": doc.get("bio", ""),
        "display_name": doc.get("display_name", ""),
    }


@router.put("/dj/profile")
async def dj_update_profile(req: DJProfileUpdate):
    doc = await dj_profiles().find_one({"name": req.name}, collation=_CI)
    if not doc:
        raise HTTPException(status_code=404, detail="DJ not found")

    await dj_profiles().update_one(
        {"id": doc["id"]},
        {"$set": {
            "links": req.links,
            "logo": req.logo,
            "bio": req.bio,
            "display_name": req.display_name,
            "genres": req.genres,
            "availability": req.availability,
            "updated_at": _now(),
        }},
    )
    return {"status": "updated"}


@router.get("/dj/list")
async def dj_list():
    """List all DJs (public info only, no passwords)."""
    results = []
    async for doc in dj_profiles().find({}, {"password": 0, "_id": 0}).collation(_CI).sort("name", 1):
        results.append({
            "id": doc.get("id"),
            "name": doc.get("name"),
            "links": doc.get("links", {}),
            "logo": doc.get("logo", ""),
            "genres": doc.get("genres", []),
            "availability": doc.get("availability", []),
        })
    return results


@router.post("/dj/discord-auth")
async def dj_discord_auth(req: DJDiscordAuthRequest):
    """Register or sign in a DJ via Discord OAuth identity."""
    if not req.discord_id or not req.name:
        raise HTTPException(status_code=400, detail="discord_id and name are required")

    # Look up by discord_id first
    doc = await dj_profiles().find_one({"discord_id": req.discord_id})
    if doc:
        return {"id": doc["id"], "name": doc["name"]}

    # Check if a name-only profile already exists (legacy) — link it
    doc = await dj_profiles().find_one({"name": req.name}, collation=_CI)
    if doc:
        await dj_profiles().update_one(
            {"id": doc["id"]},
            {"$set": {"discord_id": req.discord_id, "updated_at": _now()}},
        )
        return {"id": doc["id"], "name": doc["name"]}

    # Create a new profile
    dj_id = await next_id("dj_profiles")
    await dj_profiles().insert_one({
        "id": dj_id,
        "name": req.name,
        "password": "",
        "discord_id": req.discord_id,
        "links": {},
        "logo": "",
        "genres": [],
        "availability": [],
        "bio": "",
        "display_name": "",
        "created_at": _now(),
        "updated_at": _now(),
    })
    return {"id": dj_id, "name": req.name}
