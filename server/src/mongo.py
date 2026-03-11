"""
MongoDB connection layer (motor async driver).

Usage:
    from mongo import get_mongo_db, close_mongo

    db = get_mongo_db()          # returns motor AsyncIOMotorDatabase
    coll = db["dj_profiles"]
    await coll.find_one({"name": "DJ Name"})
"""

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from config import MONGO_URI, log

_client: AsyncIOMotorClient | None = None


def get_mongo_db() -> AsyncIOMotorDatabase:
    """Return the default database from the MONGO_URI connection string."""
    global _client
    if _client is None:
        _client = AsyncIOMotorClient(MONGO_URI)
        log.info("MongoDB client created — %s", MONGO_URI.split("@")[-1] if "@" in MONGO_URI else MONGO_URI)
    return _client.get_default_database()


async def init_mongo():
    """Ping the server to verify connectivity on startup."""
    db = get_mongo_db()
    await db.command("ping")
    log.info("MongoDB connected — database: %s", db.name)


async def close_mongo():
    """Close the MongoDB client."""
    global _client
    if _client:
        _client.close()
        _client = None
        log.info("MongoDB client closed")
