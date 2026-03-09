"""
Discord bot instance, embed builder, and send helpers.
"""

import asyncio
from datetime import datetime, timedelta, timezone

import discord

from config import log

# ── Discord bot ───────────────────────────────────────────────────────────

intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)
bot_ready = asyncio.Event()


@bot.event
async def on_ready():
    bot_ready.set()
    log.info("Discord bot connected as %s", bot.user)


# ── Helpers ───────────────────────────────────────────────────────────────

def _parse_start(timestamp: str) -> datetime:
    try:
        return datetime.strptime(timestamp, "%Y-%m-%d %H:%M")
    except (ValueError, TypeError):
        return datetime.now()


def _build_embed(data: dict) -> discord.Embed:
    """Build a Discord embed from an EmbedRequest-like dict."""
    title = data.get("title", "")
    vol = data.get("vol", "")
    full_title = f"{title} VOL.{vol}" if vol.isdigit() else title

    start = _parse_start(data.get("timestamp", ""))
    unix = int(start.timestamp())

    embed = discord.Embed(
        title=full_title or "Lineup",
        description=f"<t:{unix}:F> (<t:{unix}:R>)",
        color=0x5865F2,
        timestamp=datetime.fromtimestamp(unix, tz=timezone.utc),
    )

    genres = data.get("genres", [])
    if genres:
        embed.add_field(name="Genres", value=" // ".join(genres), inline=False)

    slots = data.get("slots", [])
    names_only = data.get("names_only", False)
    ptr = start
    lineup_lines: list[str] = []
    for slot in slots:
        name = slot.get("name", "") or "TBA" if isinstance(slot, dict) else (slot.name or "TBA")
        genre = slot.get("genre", "") if isinstance(slot, dict) else slot.genre
        duration = slot.get("duration", 60) if isinstance(slot, dict) else slot.duration
        if names_only:
            lineup_lines.append(f"**{name}**")
        else:
            ts = int(ptr.timestamp())
            genre_str = f"  •  {genre}" if genre else ""
            lineup_lines.append(f"<t:{ts}:t>  **{name}**{genre_str}")
        ptr += timedelta(minutes=duration)

    lineup_text = "\n".join(lineup_lines)
    chunks = [lineup_text[i : i + 1024] for i in range(0, len(lineup_text), 1024)]
    for i, chunk in enumerate(chunks):
        embed.add_field(
            name="Lineup" if i == 0 else "\u200b",
            value=chunk,
            inline=False,
        )

    link_order = ["TIMELINE", "VRCPOP", "X", "IG", "DISCORD", "VRC GROUP"]
    social_links = data.get("social_links", {})
    if social_links:
        parts = [
            f"[{label}]({social_links[label]})"
            for label in link_order
            if social_links.get(label, "").strip()
        ]
        if parts:
            embed.add_field(name="Links", value=" | ".join(parts), inline=False)

    embed.set_footer(text="GitHub | Baebu/lineup_builder")

    image_url = data.get("image_url", "")
    if image_url and image_url.startswith(("http://", "https://")):
        embed.set_image(url=image_url)

    return embed


async def send_embed(channel_id: int, embed_data: dict, image_url: str | None = None):
    """Resolve channel and send the embed."""
    channel = bot.get_channel(channel_id)
    if channel is None:
        channel = await bot.fetch_channel(channel_id)
    embed = _build_embed({**embed_data, "image_url": image_url or ""})
    await channel.send(embed=embed)
