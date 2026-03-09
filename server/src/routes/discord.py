"""
Discord-related routes — bot status, channels, posting, scheduling.
"""

import uuid
from datetime import datetime, timezone

import discord
from fastapi import APIRouter, Depends, HTTPException

from config import log
from models.schemas import EmbedRequest, MessageRequest, ScheduleRequest
from services.discord_bot import bot, bot_ready, send_embed

router = APIRouter()

# ── Scheduled posts store (in-memory) ────────────────────────────────────

scheduled_posts: dict[str, dict] = {}  # id → entry

# ── Routes ────────────────────────────────────────────────────────────────


@router.get("/bot/status")
async def bot_status():
    return {
        "connected": bot_ready.is_set(),
        "user": str(bot.user) if bot.is_ready() else None,
        "guilds": [
            {"id": g.id, "name": g.name}
            for g in bot.guilds
        ] if bot.is_ready() else [],
    }


@router.get("/channels")
async def list_channels():
    if not bot_ready.is_set():
        raise HTTPException(status_code=503, detail="Bot is not connected")

    result = []
    for guild in bot.guilds:
        for ch in guild.text_channels:
            result.append({
                "guild_name": guild.name,
                "channel_name": ch.name,
                "channel_id": ch.id,
            })
    result.sort(key=lambda c: (c["guild_name"].lower(), c["channel_name"].lower()))
    return result


@router.post("/post/embed")
async def post_embed(req: EmbedRequest):
    if not bot_ready.is_set():
        raise HTTPException(status_code=503, detail="Bot is not connected")
    if not req.slots:
        raise HTTPException(status_code=400, detail="Lineup is empty")

    embed_data = req.model_dump(exclude={"channel_id", "image_url"})
    try:
        await send_embed(req.channel_id, embed_data, req.image_url)
    except discord.NotFound:
        raise HTTPException(status_code=404, detail="Channel not found")
    except discord.Forbidden:
        raise HTTPException(status_code=403, detail="Bot lacks permission to post")
    except Exception as exc:
        log.exception("Failed to post embed")
        raise HTTPException(status_code=500, detail=str(exc))

    return {"status": "posted"}


@router.post("/post/message")
async def post_message(req: MessageRequest):
    if not bot_ready.is_set():
        raise HTTPException(status_code=503, detail="Bot is not connected")

    try:
        channel = bot.get_channel(req.channel_id)
        if channel is None:
            channel = await bot.fetch_channel(req.channel_id)
        for i in range(0, len(req.content), 2000):
            await channel.send(req.content[i : i + 2000])
    except discord.NotFound:
        raise HTTPException(status_code=404, detail="Channel not found")
    except discord.Forbidden:
        raise HTTPException(status_code=403, detail="Bot lacks permission")
    except Exception as exc:
        log.exception("Failed to send message")
        raise HTTPException(status_code=500, detail=str(exc))

    return {"status": "sent"}


# ── Scheduled posts ──────────────────────────────────────────────────────


@router.post("/schedule")
async def create_scheduled_post(req: ScheduleRequest):
    try:
        post_at = datetime.fromisoformat(req.post_at_utc)
        if post_at.tzinfo is None:
            post_at = post_at.replace(tzinfo=timezone.utc)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid datetime format. Use ISO 8601.")

    if post_at <= datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Schedule time must be in the future")

    post_id = uuid.uuid4().hex[:12]
    embed_data = req.model_dump(exclude={"channel_id", "image_url", "post_at_utc"})

    scheduled_posts[post_id] = {
        "id": post_id,
        "post_at_utc": post_at,
        "channel_id": req.channel_id,
        "embed_data": embed_data,
        "image_url": req.image_url,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    log.info("Scheduled post %s for %s", post_id, post_at.isoformat())
    return {"id": post_id, "post_at_utc": post_at.isoformat()}


@router.get("/schedule")
async def list_scheduled_posts():
    result = []
    for entry in scheduled_posts.values():
        result.append({
            "id": entry["id"],
            "post_at_utc": entry["post_at_utc"].isoformat(),
            "channel_id": entry["channel_id"],
            "title": entry["embed_data"].get("title", ""),
            "created_at": entry.get("created_at", ""),
        })
    result.sort(key=lambda e: e["post_at_utc"])
    return result


@router.delete("/schedule/{post_id}")
async def cancel_scheduled_post(post_id: str):
    if post_id not in scheduled_posts:
        raise HTTPException(status_code=404, detail="Scheduled post not found")
    scheduled_posts.pop(post_id)
    log.info("Cancelled scheduled post %s", post_id)
    return {"status": "cancelled"}
