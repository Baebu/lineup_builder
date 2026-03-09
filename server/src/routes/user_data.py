"""
User data routes — cloud save, keyed by Discord user ID.
"""

import json

from fastapi import APIRouter, HTTPException

from db import get_db
from models.schemas import UserDataPut

router = APIRouter()


@router.get("/user/{discord_id}/data/{key}")
async def get_user_data(discord_id: str, key: str):
    """Fetch a single data blob for a Discord user."""
    if key not in ("library", "events", "settings"):
        raise HTTPException(status_code=400, detail="Invalid key")
    db = await get_db()
    rows = await db.execute_fetchall(
        "SELECT value FROM user_data WHERE discord_id = ? AND key = ?",
        (discord_id, key),
    )
    if not rows:
        return {"discord_id": discord_id, "key": key, "value": {}}
    return {"discord_id": discord_id, "key": key, "value": json.loads(rows[0][0])}


@router.put("/user/{discord_id}/data/{key}")
async def put_user_data(discord_id: str, key: str, req: UserDataPut):
    """Create or update a data blob for a Discord user."""
    if key not in ("library", "events", "settings"):
        raise HTTPException(status_code=400, detail="Invalid key")
    db = await get_db()
    await db.execute(
        """INSERT INTO user_data (discord_id, key, value, updated_at)
           VALUES (?, ?, ?, datetime('now'))
           ON CONFLICT(discord_id, key) DO UPDATE
           SET value = excluded.value, updated_at = excluded.updated_at""",
        (discord_id, key, json.dumps(req.value if isinstance(req.value, (dict, list)) else {})),
    )
    await db.commit()
    return {"status": "saved"}


@router.get("/user/{discord_id}/data")
async def get_all_user_data(discord_id: str):
    """Fetch all data blobs for a Discord user."""
    db = await get_db()
    rows = await db.execute_fetchall(
        "SELECT key, value FROM user_data WHERE discord_id = ?",
        (discord_id,),
    )
    result = {}
    for r in rows:
        result[r[0]] = json.loads(r[1])
    return {"discord_id": discord_id, "data": result}
