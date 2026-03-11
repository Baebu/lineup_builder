"""
User data routes — cloud save, keyed by Discord user ID.
"""

from fastapi import APIRouter, HTTPException

from db import user_data, _now
from models.schemas import UserDataPut

router = APIRouter()


@router.get("/user/{discord_id}/data/{key}")
async def get_user_data(discord_id: str, key: str):
    """Fetch a single data blob for a Discord user."""
    if key not in ("library", "events", "settings"):
        raise HTTPException(status_code=400, detail="Invalid key")
    doc = await user_data().find_one({"discord_id": discord_id, "key": key})
    if not doc:
        return {"discord_id": discord_id, "key": key, "value": {}}
    return {"discord_id": discord_id, "key": key, "value": doc.get("value", {})}


@router.put("/user/{discord_id}/data/{key}")
async def put_user_data(discord_id: str, key: str, req: UserDataPut):
    """Create or update a data blob for a Discord user."""
    if key not in ("library", "events", "settings"):
        raise HTTPException(status_code=400, detail="Invalid key")
    value = req.value if isinstance(req.value, (dict, list)) else {}
    await user_data().update_one(
        {"discord_id": discord_id, "key": key},
        {"$set": {"value": value, "updated_at": _now()}},
        upsert=True,
    )
    return {"status": "saved"}


@router.get("/user/{discord_id}/data")
async def get_all_user_data(discord_id: str):
    """Fetch all data blobs for a Discord user."""
    result = {}
    async for doc in user_data().find({"discord_id": discord_id}):
        result[doc["key"]] = doc.get("value", {})
    return {"discord_id": discord_id, "data": result}
