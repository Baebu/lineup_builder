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
from fastapi.responses import JSONResponse
from fastapi.security import APIKeyHeader

from config import API_KEY, BOT_TOKEN, VRCHAT_PASSWORD, VRCHAT_USERNAME, log
from db import close_db, init_db
from routes import bookings, discord, dj, user_data, vrchat
from routes.discord import scheduled_posts
from services.discord_bot import bot, bot_ready, send_embed
from services.vrchat_api import (
    VRC_LOGIN_COOLDOWN,
    set_auth_cookie,
    vrchat_get,
    vrchat_login,
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
                    await send_embed(entry["channel_id"], entry["embed_data"],
                                     entry.get("image_url"))
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
    # Init database
    await init_db()
    # Start scheduler
    _scheduler_task = asyncio.get_event_loop().create_task(_scheduler_loop())
    # Log in to VRChat on boot (skip if last API call was recent)
    if VRCHAT_USERNAME and VRCHAT_PASSWORD:
        _since_last = time.time() - _vrc_last_call
        if _vrc_last_call and _since_last < VRC_LOGIN_COOLDOWN:
            log.info(
                "VRChat login skipped — last API call was %.0fs ago (cooldown %ds)",
                _since_last, VRC_LOGIN_COOLDOWN,
            )
        else:
            loop = asyncio.get_event_loop()
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
    await close_db()


app = FastAPI(title="Lineup Builder Bot Server", lifespan=lifespan)


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


# ── Register routers ─────────────────────────────────────────────────────

app.include_router(discord.router, dependencies=[Depends(verify_api_key)])
app.include_router(dj.router, dependencies=[Depends(verify_api_key)])
app.include_router(bookings.router, dependencies=[Depends(verify_api_key)])
app.include_router(user_data.router, dependencies=[Depends(verify_api_key)])
app.include_router(vrchat.router, dependencies=[Depends(verify_api_key)])


# ── Entry point ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
