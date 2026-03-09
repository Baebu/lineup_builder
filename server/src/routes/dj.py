"""
DJ profile routes — register, login, profile CRUD, discord-auth.
"""

import json

import bcrypt
from fastapi import APIRouter, HTTPException

from db import get_db
from models.schemas import (
    DJDiscordAuthRequest,
    DJLoginRequest,
    DJProfileUpdate,
    DJRegisterRequest,
)

router = APIRouter()


@router.post("/dj/register")
async def dj_register(req: DJRegisterRequest):
    if not req.name or not req.password:
        raise HTTPException(status_code=400, detail="Name and password are required")
    if len(req.password) < 4:
        raise HTTPException(status_code=400, detail="Password must be at least 4 characters")

    hashed = bcrypt.hashpw(req.password.encode(), bcrypt.gensalt()).decode()
    db = await get_db()
    try:
        await db.execute(
            "INSERT INTO dj_profiles (name, password) VALUES (?, ?)",
            (req.name, hashed),
        )
        await db.commit()
    except Exception:
        raise HTTPException(status_code=409, detail="DJ name already taken")

    row = await db.execute_fetchall(
        "SELECT id, name FROM dj_profiles WHERE name = ? COLLATE NOCASE", (req.name,)
    )
    return {"id": row[0][0], "name": row[0][1]}


@router.post("/dj/login")
async def dj_login(req: DJLoginRequest):
    db = await get_db()
    rows = await db.execute_fetchall(
        "SELECT id, name, password FROM dj_profiles WHERE name = ? COLLATE NOCASE",
        (req.name,),
    )
    if not rows:
        raise HTTPException(status_code=401, detail="Invalid name or password")

    row = rows[0]
    if not bcrypt.checkpw(req.password.encode(), row[2].encode()):
        raise HTTPException(status_code=401, detail="Invalid name or password")

    return {"id": row[0], "name": row[1]}


@router.get("/dj/profile/{name}")
async def dj_get_profile(name: str):
    db = await get_db()
    rows = await db.execute_fetchall(
        "SELECT id, name, links, logo, genres, availability FROM dj_profiles WHERE name = ? COLLATE NOCASE",
        (name,),
    )
    if not rows:
        raise HTTPException(status_code=404, detail="DJ not found")
    r = rows[0]
    return {
        "id": r[0],
        "name": r[1],
        "links": json.loads(r[2]),
        "logo": r[3],
        "genres": json.loads(r[4]),
        "availability": json.loads(r[5]),
    }


@router.put("/dj/profile")
async def dj_update_profile(req: DJProfileUpdate):
    db = await get_db()
    rows = await db.execute_fetchall(
        "SELECT id FROM dj_profiles WHERE name = ? COLLATE NOCASE", (req.name,)
    )
    if not rows:
        raise HTTPException(status_code=404, detail="DJ not found")

    await db.execute(
        """UPDATE dj_profiles
           SET links = ?, logo = ?, genres = ?, availability = ?, updated_at = datetime('now')
           WHERE id = ?""",
        (json.dumps(req.links), req.logo, json.dumps(req.genres), json.dumps(req.availability), rows[0][0]),
    )
    await db.commit()
    return {"status": "updated"}


@router.get("/dj/list")
async def dj_list():
    """List all DJs (public info only, no passwords)."""
    db = await get_db()
    rows = await db.execute_fetchall(
        "SELECT id, name, links, logo, genres, availability FROM dj_profiles ORDER BY name COLLATE NOCASE"
    )
    return [
        {
            "id": r[0],
            "name": r[1],
            "links": json.loads(r[2]),
            "logo": r[3],
            "genres": json.loads(r[4]),
            "availability": json.loads(r[5]),
        }
        for r in rows
    ]


@router.post("/dj/discord-auth")
async def dj_discord_auth(req: DJDiscordAuthRequest):
    """Register or sign in a DJ via Discord OAuth identity."""
    if not req.discord_id or not req.name:
        raise HTTPException(status_code=400, detail="discord_id and name are required")

    db = await get_db()
    # Look up by discord_id first
    rows = await db.execute_fetchall(
        "SELECT id, name FROM dj_profiles WHERE discord_id = ?", (req.discord_id,)
    )
    if rows:
        return {"id": rows[0][0], "name": rows[0][1]}

    # Check if a name-only profile already exists (legacy) — link it
    rows = await db.execute_fetchall(
        "SELECT id, name FROM dj_profiles WHERE name = ? COLLATE NOCASE", (req.name,)
    )
    if rows:
        await db.execute(
            "UPDATE dj_profiles SET discord_id = ?, updated_at = datetime('now') WHERE id = ?",
            (req.discord_id, rows[0][0]),
        )
        await db.commit()
        return {"id": rows[0][0], "name": rows[0][1]}

    # Create a new profile
    await db.execute(
        "INSERT INTO dj_profiles (name, discord_id) VALUES (?, ?)",
        (req.name, req.discord_id),
    )
    await db.commit()
    row = await db.execute_fetchall(
        "SELECT id, name FROM dj_profiles WHERE discord_id = ?", (req.discord_id,)
    )
    return {"id": row[0][0], "name": row[0][1]}
