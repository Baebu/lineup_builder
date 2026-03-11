"""
Lineup Builder — Discord Bot Server

A FastAPI server that keeps the Discord bot online 24/7 and exposes
REST endpoints for the desktop app to post lineups, list channels,
and manage scheduled posts.

Environment variables (set in Railway dashboard):
    DISCORD_BOT_TOKEN   — Discord bot token (required)
    API_KEY             — Secret key to authenticate requests from the desktop app (required)
    VRCHAT_USERNAME    — VRChat account username for API auth (optional)
    VRCHAT_PASSWORD    — VRChat account password (optional)
    VRCHAT_TOTP_SECRET — VRChat 2FA TOTP secret (optional, if 2FA enabled)
    PORT                — Port to listen on (Railway sets this automatically)
"""

import asyncio
import os
import time
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request, Security
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import APIKeyHeader

from config import API_KEY, BOT_TOKEN, VRCHAT_PASSWORD, VRCHAT_USERNAME, log
from db import init_db
from mongo import close_mongo, init_mongo
from routes import bookings, club, discord, dj, user_data, vrchat
from routes import discord_oauth
from routes import images as images_route
from routes.discord import scheduled_posts, sent_posts, _record_sent
from services.discord_bot import bot, bot_ready, send_embed
from services.vrchat_api import (
    VRC_LOGIN_COOLDOWN,
    set_auth_cookie,
    vrchat_get,
    vrchat_login,
    vrchat_verify_session,
    _vrc_saved_cookie,
)

# Import _vrc_last_call for cooldown check
from services.vrchat_api import _vrc_last_call


# ── Background loops ─────────────────────────────────────────────────────

async def _scheduler_loop():
    """Check for due scheduled posts every 5 seconds."""
    from datetime import datetime, timezone

    while True:
        await asyncio.sleep(5)
        if not bot_ready.is_set():
            continue

        now = datetime.now(timezone.utc)
        fired: list[str] = []

        for post_id, entry in list(scheduled_posts.items()):
            post_dt = entry.get("post_at_utc")
            if post_dt and now >= post_dt:
                log.info("Firing scheduled post %s", post_id)
                try:
                    message = await send_embed(int(entry["channel_id"]), entry["embed_data"],
                                     entry.get("image_url"))
                    _record_sent(message, entry["embed_data"], entry.get("image_url", ""))
                except Exception:
                    log.exception("Failed to fire scheduled post %s", post_id)
                fired.append(post_id)

        for pid in fired:
            scheduled_posts.pop(pid, None)


async def _vrchat_keepalive_loop():
    """Ping VRChat API every 30 min to keep the session alive."""
    while True:
        await asyncio.sleep(30 * 60)
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, vrchat_get, "/auth/user")
            if result is None:
                log.warning("VRChat keep-alive ping failed — session may have expired")
            else:
                log.info("VRChat keep-alive OK")
        except Exception as exc:
            log.warning("VRChat keep-alive error: %s", exc)


# ── App lifecycle ─────────────────────────────────────────────────────────

_scheduler_task: asyncio.Task | None = None
_vrchat_keepalive_task: asyncio.Task | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _scheduler_task, _vrchat_keepalive_task
    # Start bot in background
    if BOT_TOKEN:
        loop = asyncio.get_event_loop()
        loop.create_task(bot.start(BOT_TOKEN))
        log.info("Bot starting…")
        # Wait up to 30s for bot to be ready
        try:
            await asyncio.wait_for(bot_ready.wait(), timeout=30)
        except asyncio.TimeoutError:
            log.warning("Bot did not become ready within 30 s")
    # Init databases
    await init_db()
    await init_mongo()
    # Start scheduler
    _scheduler_task = asyncio.get_event_loop().create_task(_scheduler_loop())
    # Log in to VRChat on boot — reuse saved session if still valid
    if VRCHAT_USERNAME and VRCHAT_PASSWORD:
        loop = asyncio.get_event_loop()
        if _vrc_saved_cookie:
            valid = await loop.run_in_executor(None, vrchat_verify_session, _vrc_saved_cookie)
            if valid:
                log.info("VRChat session restored from saved cookie — no re-login needed")
                _vrchat_keepalive_task = loop.create_task(_vrchat_keepalive_loop())
            else:
                log.info("Saved VRChat cookie expired — performing fresh login")
                auth = await loop.run_in_executor(None, vrchat_login)
                if auth:
                    set_auth_cookie(auth)
                    log.info("VRChat session established on startup")
                    _vrchat_keepalive_task = loop.create_task(_vrchat_keepalive_loop())
                else:
                    log.error("VRChat login failed on startup — API calls will retry later")
        else:
            auth = await loop.run_in_executor(None, vrchat_login)
            if auth:
                set_auth_cookie(auth)
                log.info("VRChat session established on startup")
                _vrchat_keepalive_task = loop.create_task(_vrchat_keepalive_loop())
            else:
                log.error("VRChat login failed on startup — API calls will retry later")
    yield
    # Shutdown
    if _scheduler_task:
        _scheduler_task.cancel()
    if _vrchat_keepalive_task:
        _vrchat_keepalive_task.cancel()
    if bot.is_ready():
        await bot.close()
    await close_mongo()


app = FastAPI(title="Lineup Builder Bot Server", lifespan=lifespan)

# CORS — allow web app origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    body = await request.body()
    log.error(
        "Validation error on %s %s — body=%s errors=%s",
        request.method, request.url.path, body[:500], exc.errors(),
    )
    return JSONResponse(status_code=422, content={"detail": exc.errors()})


# ── Auth ──────────────────────────────────────────────────────────────────

_api_key_header = APIKeyHeader(name="X-API-Key")


async def verify_api_key(key: str = Security(_api_key_header)):
    if not API_KEY or key != API_KEY:
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail="Invalid API key")
    return key


# ── Public routes ─────────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {"name": "Lineup Builder API", "status": "ok"}


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "bot_ready": bot_ready.is_set(),
        "bot_user": str(bot.user) if bot.is_ready() else None,
        "guilds": len(bot.guilds) if bot.is_ready() else 0,
        "scheduled_posts": len(scheduled_posts),
    }


@app.post("/admin/rebuild-db", dependencies=[Depends(verify_api_key)])
async def admin_rebuild_db():
    """Drop and recreate all MongoDB collections. Requires API key."""
    from db import rebuild_db
    actions = await rebuild_db()
    return {"status": "rebuilt", "actions": actions}


# ── Register routers ─────────────────────────────────────────────────────

# OAuth routes are public (no API key)
app.include_router(discord_oauth.router)

# Image storage routes are public — browser clients upload directly
app.include_router(images_route.router)

# DJ profile routes are public — called by the browser web app (no API key available)
app.include_router(dj.router)
app.include_router(club.router)

# Discord bot read-only routes are public — browser fetches guilds/channels/roles
app.include_router(discord.public_router)

# Discord mutation routes (post embed, schedule, resend) — also public for web app
app.include_router(discord.router)
app.include_router(bookings.router)
app.include_router(user_data.router)
app.include_router(vrchat.router)


# ── Entry point ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
