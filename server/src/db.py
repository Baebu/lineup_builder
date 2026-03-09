"""
Database layer for DJ profiles and bookings (SQLite via aiosqlite).
"""

import os

import aiosqlite

DB_PATH = os.environ.get("DB_PATH", "lineup.db")

_db: aiosqlite.Connection | None = None


async def get_db() -> aiosqlite.Connection:
    global _db
    if _db is None:
        _db = await aiosqlite.connect(DB_PATH)
        _db.row_factory = aiosqlite.Row
        await _db.execute("PRAGMA journal_mode=WAL")
        await _db.execute("PRAGMA foreign_keys=ON")
    return _db


async def init_db():
    """Create tables if they don't exist."""
    db = await get_db()
    await db.executescript("""
        CREATE TABLE IF NOT EXISTS dj_profiles (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT    NOT NULL UNIQUE COLLATE NOCASE,
            password    TEXT    NOT NULL DEFAULT '',
            discord_id  TEXT    NOT NULL DEFAULT '',
            links       TEXT    NOT NULL DEFAULT '{}',
            logo        TEXT    NOT NULL DEFAULT '',
            genres      TEXT    NOT NULL DEFAULT '[]',
            availability TEXT   NOT NULL DEFAULT '[]',
            created_at  TEXT    NOT NULL DEFAULT (datetime('now')),
            updated_at  TEXT    NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS bookings (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            dj_id       INTEGER NOT NULL REFERENCES dj_profiles(id),
            group_name  TEXT    NOT NULL DEFAULT '',
            event_title TEXT    NOT NULL DEFAULT '',
            event_date  TEXT    NOT NULL DEFAULT '',
            start_time  TEXT    NOT NULL DEFAULT '',
            duration    INTEGER NOT NULL DEFAULT 60,
            message     TEXT    NOT NULL DEFAULT '',
            status      TEXT    NOT NULL DEFAULT 'pending',
            discord_channel_id INTEGER,
            created_at  TEXT    NOT NULL DEFAULT (datetime('now')),
            updated_at  TEXT    NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS user_data (
            discord_id  TEXT    NOT NULL,
            key         TEXT    NOT NULL,
            value       TEXT    NOT NULL DEFAULT '{}',
            updated_at  TEXT    NOT NULL DEFAULT (datetime('now')),
            PRIMARY KEY (discord_id, key)
        );

        CREATE INDEX IF NOT EXISTS idx_bookings_dj_id ON bookings(dj_id);
        CREATE INDEX IF NOT EXISTS idx_bookings_status ON bookings(status);
    """)

    # ── Migrations ────────────────────────────────────────────────────────
    # Add genres column to existing dj_profiles tables (no-op if already present)
    try:
        await db.execute(
            "ALTER TABLE dj_profiles ADD COLUMN genres TEXT NOT NULL DEFAULT '[]'"
        )
        await db.commit()
    except Exception:
        pass  # column already exists

    await db.commit()


async def close_db():
    global _db
    if _db:
        await _db.close()
        _db = None
