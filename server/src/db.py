"""
Database layer — MongoDB via motor (async).

Collections:
  dj_profiles  — DJ registration, profiles, login
  bookings     — booking requests between clubs and DJs
  user_data    — cloud-saved user blobs (library, events, settings)
  clubs        — club Discord links + VRChat group verification
  counters     — auto-increment ID sequences
"""

from datetime import datetime, timezone

from mongo import get_mongo_db


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ── Collections ───────────────────────────────────────────────────────────

def dj_profiles():
    return get_mongo_db()["dj_profiles"]


def bookings():
    return get_mongo_db()["bookings"]


def user_data():
    return get_mongo_db()["user_data"]


def clubs():
    return get_mongo_db()["clubs"]


def counters():
    return get_mongo_db()["counters"]


# ── Auto-increment helper ────────────────────────────────────────────────

async def next_id(collection_name: str) -> int:
    """Return the next auto-increment integer ID for a collection."""
    doc = await counters().find_one_and_update(
        {"_id": collection_name},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=True,
    )
    return doc["seq"]


# ── Init (indexes) ────────────────────────────────────────────────────────

async def init_db():
    """Create indexes. Collections are created implicitly by MongoDB."""
    from pymongo import ASCENDING
    from pymongo.collation import Collation

    ci = Collation(locale="en", strength=2)  # case-insensitive

    await dj_profiles().create_index("discord_id")
    await dj_profiles().create_index(
        [("name", ASCENDING)], unique=True, collation=ci
    )
    await bookings().create_index("dj_id")
    await bookings().create_index("status")
    await bookings().create_index("group_name")
    await user_data().create_index([("discord_id", ASCENDING), ("key", ASCENDING)], unique=True)
    await clubs().create_index("discord_id", unique=True)


async def close_db():
    """No-op — motor client is closed via close_mongo()."""
    pass


async def rebuild_db():
    """Drop and recreate all collections. Returns list of actions taken."""
    db = get_mongo_db()
    actions = []
    for name in ["dj_profiles", "bookings", "user_data", "clubs", "counters"]:
        try:
            await db.drop_collection(name)
            actions.append(f"dropped {name}")
        except Exception as e:
            actions.append(f"failed to drop {name}: {e}")
    await init_db()
    actions.append("recreated indexes")
    return actions
