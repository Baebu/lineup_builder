"""
Discord-related routes — bot status, channels, posting, scheduling.
"""

import uuid
from datetime import datetime, timezone

import discord
from fastapi import APIRouter, Depends, HTTPException

from config import log
from models.schemas import EmbedRequest, MessageRequest, ResendRequest, ScheduleRequest, UpdateScheduleRequest
from services.discord_bot import bot, bot_ready, send_embed

router = APIRouter()

# Public router — read-only bot queries called from the browser (no API key needed)
public_router = APIRouter()

# ── In-memory stores ─────────────────────────────────────────────────────

scheduled_posts: dict[str, dict] = {}  # id → entry
MAX_SENT = 50
sent_posts: list[dict] = []  # newest-first, capped at MAX_SENT


def _record_sent(message: discord.Message, embed_data: dict, image_url: str = "") -> dict:
    """Append a sent-message record to sent_posts. Also called by server.py scheduler."""
    post_id = uuid.uuid4().hex[:12]
    entry: dict = {
        "id": post_id,
        "channel_id": message.channel.id,
        "channel_name": getattr(message.channel, "name", ""),
        "guild_name": message.guild.name if message.guild else "",
        "message_id": str(message.id),
        "sent_at": datetime.now(timezone.utc).isoformat(),
        "embed_data": embed_data,
        "image_url": image_url,
        "title": embed_data.get("title", ""),
    }
    sent_posts.insert(0, entry)
    if len(sent_posts) > MAX_SENT:
        sent_posts.pop()
    return entry

# ── Read-only routes (public) ─────────────────────────────────────────────


@public_router.get("/bot/status")
async def bot_status():
    return {
        "connected": bot_ready.is_set(),
        "user": str(bot.user) if bot.is_ready() else None,
        "guilds": [
            {"id": g.id, "name": g.name}
            for g in bot.guilds
        ] if bot.is_ready() else [],
    }


@public_router.get("/guilds")
async def list_guilds():
    if not bot_ready.is_set():
        raise HTTPException(status_code=503, detail="Bot is not connected")

    return [
        {"id": str(g.id), "name": g.name}
        for g in sorted(bot.guilds, key=lambda g: g.name.lower())
    ]


@public_router.get("/guilds/{guild_id}/roles")
async def list_guild_roles(guild_id: int):
    if not bot_ready.is_set():
        raise HTTPException(status_code=503, detail="Bot is not connected")

    guild = bot.get_guild(guild_id)
    if guild is None:
        raise HTTPException(status_code=404, detail="Guild not found")

    # Exclude @everyone and managed bot roles; sort by position descending
    roles = [
        {"id": str(r.id), "name": r.name, "color": str(r.color)}
        for r in sorted(guild.roles, key=lambda r: r.position, reverse=True)
        if not r.is_default() and not r.managed
    ]
    return roles


@public_router.get("/guilds/{guild_id}/channels")
async def list_guild_channels(guild_id: int):
    if not bot_ready.is_set():
        raise HTTPException(status_code=503, detail="Bot is not connected")

    guild = bot.get_guild(guild_id)
    if guild is None:
        raise HTTPException(status_code=404, detail="Guild not found")

    return [
        {"channel_id": str(ch.id), "channel_name": ch.name}
        for ch in sorted(guild.text_channels, key=lambda c: c.name.lower())
    ]


@public_router.get("/channels")
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


@public_router.get("/schedule")
async def list_scheduled_posts_public():
    result = []
    for entry in scheduled_posts.values():
        result.append({
            "id": entry["id"],
            "post_at_utc": entry["post_at_utc"].isoformat(),
            "channel_id": entry["channel_id"],
            "embed_data": entry["embed_data"],
            "image_url": entry.get("image_url", ""),
            "title": entry["embed_data"].get("title", ""),
            "created_at": entry.get("created_at", ""),
        })
    result.sort(key=lambda e: e["post_at_utc"])
    return result


@public_router.get("/sent")
async def list_sent_posts():
    return list(sent_posts)


@router.post("/post/embed")
async def post_embed(req: EmbedRequest):
    if not bot_ready.is_set():
        raise HTTPException(status_code=503, detail="Bot is not connected")
    if not req.slots:
        raise HTTPException(status_code=400, detail="Lineup is empty")

    embed_data = req.model_dump(exclude={"channel_id", "image_url"})
    try:
        message = await send_embed(int(req.channel_id), embed_data, req.image_url)
    except discord.NotFound:
        raise HTTPException(status_code=404, detail="Channel not found")
    except discord.Forbidden:
        raise HTTPException(status_code=403, detail="Bot lacks permission to post")
    except Exception as exc:
        log.exception("Failed to post embed")
        raise HTTPException(status_code=500, detail=str(exc))

    record = _record_sent(message, embed_data, req.image_url)
    return {"status": "posted", "id": record["id"]}


@router.post("/post/message")
async def post_message(req: MessageRequest):
    if not bot_ready.is_set():
        raise HTTPException(status_code=503, detail="Bot is not connected")

    try:
        channel = bot.get_channel(int(req.channel_id))
        if channel is None:
            channel = await bot.fetch_channel(int(req.channel_id))
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


@router.delete("/schedule/{post_id}")
async def cancel_scheduled_post(post_id: str):
    if post_id not in scheduled_posts:
        raise HTTPException(status_code=404, detail="Scheduled post not found")
    scheduled_posts.pop(post_id)
    log.info("Cancelled scheduled post %s", post_id)
    return {"status": "cancelled"}


@router.put("/schedule/{post_id}")
async def update_scheduled_post(post_id: str, req: UpdateScheduleRequest):
    entry = scheduled_posts.get(post_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Scheduled post not found")

    if req.post_at_utc is not None:
        try:
            post_at = datetime.fromisoformat(req.post_at_utc)
            if post_at.tzinfo is None:
                post_at = post_at.replace(tzinfo=timezone.utc)
            if post_at <= datetime.now(timezone.utc):
                raise HTTPException(status_code=400, detail="Schedule time must be in the future")
            entry["post_at_utc"] = post_at
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid datetime format. Use ISO 8601.")

    if req.channel_id is not None:
        entry["channel_id"] = req.channel_id
    if req.image_url is not None:
        entry["image_url"] = req.image_url
    if req.content is not None:
        entry["embed_data"]["content"] = req.content
    if req.title is not None:
        entry["embed_data"]["title"] = req.title
    if req.vol is not None:
        entry["embed_data"]["vol"] = req.vol
    if req.timestamp is not None:
        entry["embed_data"]["timestamp"] = req.timestamp
    if req.genres is not None:
        entry["embed_data"]["genres"] = req.genres
    if req.slots is not None:
        entry["embed_data"]["slots"] = [s.model_dump() for s in req.slots]
    if req.names_only is not None:
        entry["embed_data"]["names_only"] = req.names_only
    if req.social_links is not None:
        entry["embed_data"]["social_links"] = req.social_links

    log.info("Updated scheduled post %s", post_id)
    return {"id": post_id, "post_at_utc": entry["post_at_utc"].isoformat()}


@router.post("/sent/{post_id}/resend")
async def resend_sent_post(post_id: str, req: ResendRequest):
    entry = next((p for p in sent_posts if p["id"] == post_id), None)
    if not entry:
        raise HTTPException(status_code=404, detail="Sent post not found")

    if not bot_ready.is_set():
        raise HTTPException(status_code=503, detail="Bot is not connected")

    target_channel = req.channel_id or entry["channel_id"]
    embed_data = entry["embed_data"]
    image_url = entry.get("image_url", "")

    try:
        message = await send_embed(int(target_channel), embed_data, image_url)
    except discord.NotFound:
        raise HTTPException(status_code=404, detail="Channel not found")
    except discord.Forbidden:
        raise HTTPException(status_code=403, detail="Bot lacks permission to post")
    except Exception as exc:
        log.exception("Failed to resend post %s", post_id)
        raise HTTPException(status_code=500, detail=str(exc))

    record = _record_sent(message, embed_data, image_url)
    return {"status": "resent", "id": record["id"]}


@router.delete("/sent/{post_id}")
async def delete_sent_post(post_id: str):
    idx = next((i for i, p in enumerate(sent_posts) if p["id"] == post_id), None)
    if idx is None:
        raise HTTPException(status_code=404, detail="Sent post not found")
    sent_posts.pop(idx)
    return {"status": "deleted"}
