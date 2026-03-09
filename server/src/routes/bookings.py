"""
Booking routes — create, list, respond, notifications.
"""

import asyncio

import discord
from fastapi import APIRouter, HTTPException

from config import log
from db import get_db
from models.schemas import BookingCreateRequest, BookingRespondRequest
from services.discord_bot import bot, bot_ready

router = APIRouter()


@router.post("/booking")
async def create_booking(req: BookingCreateRequest):
    db = await get_db()
    rows = await db.execute_fetchall(
        "SELECT id FROM dj_profiles WHERE name = ? COLLATE NOCASE", (req.dj_name,)
    )
    if not rows:
        raise HTTPException(status_code=404, detail="DJ not found")
    dj_id = rows[0][0]

    cursor = await db.execute(
        """INSERT INTO bookings (dj_id, group_name, event_title, event_date,
               start_time, duration, message, discord_channel_id)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (dj_id, req.group_name, req.event_title, req.event_date,
         req.start_time, req.duration, req.message, req.discord_channel_id),
    )
    await db.commit()
    booking_id = cursor.lastrowid

    # Notify DJ via Discord DM if bot is ready
    if bot_ready.is_set():
        asyncio.create_task(_notify_dj_booking(dj_id, req, booking_id))

    return {"id": booking_id, "status": "pending"}


async def _notify_dj_booking(dj_id: int, req: BookingCreateRequest, booking_id: int):
    """Send a Discord DM to the DJ about a new booking request."""
    try:
        db = await get_db()
        rows = await db.execute_fetchall(
            "SELECT name FROM dj_profiles WHERE id = ?", (dj_id,)
        )
        if not rows:
            return
        dj_name = rows[0][0]

        # Try to find the DJ as a Discord user across guilds
        target_member = None
        for guild in bot.guilds:
            for member in guild.members:
                if member.display_name.lower() == dj_name.lower() or (
                    member.nick and member.nick.lower() == dj_name.lower()
                ):
                    target_member = member
                    break
            if target_member:
                break

        if target_member:
            embed = discord.Embed(
                title="New Booking Request",
                description=(
                    f"**Group:** {req.group_name}\n"
                    f"**Event:** {req.event_title}\n"
                    f"**Date:** {req.event_date}\n"
                    f"**Time:** {req.start_time}\n"
                    f"**Duration:** {req.duration} min\n"
                ),
                color=0x5865F2,
            )
            if req.message:
                embed.add_field(name="Message", value=req.message, inline=False)
            embed.set_footer(text=f"Booking #{booking_id} — respond in the Lineup Builder app")
            await target_member.send(embed=embed)
    except Exception:
        log.exception("Failed to DM DJ about booking %s", booking_id)


@router.get("/bookings/dj/{dj_name}")
async def list_dj_bookings(dj_name: str):
    """List all bookings for a specific DJ."""
    db = await get_db()
    rows = await db.execute_fetchall(
        "SELECT id FROM dj_profiles WHERE name = ? COLLATE NOCASE", (dj_name,)
    )
    if not rows:
        raise HTTPException(status_code=404, detail="DJ not found")
    dj_id = rows[0][0]

    bookings = await db.execute_fetchall(
        """SELECT id, group_name, event_title, event_date, start_time,
                  duration, message, status, created_at
           FROM bookings WHERE dj_id = ? ORDER BY created_at DESC""",
        (dj_id,),
    )
    return [
        {
            "id": b[0], "group_name": b[1], "event_title": b[2],
            "event_date": b[3], "start_time": b[4], "duration": b[5],
            "message": b[6], "status": b[7], "created_at": b[8],
        }
        for b in bookings
    ]


@router.put("/booking/{booking_id}/respond")
async def respond_to_booking(booking_id: int, req: BookingRespondRequest):
    if req.status not in ("accepted", "declined"):
        raise HTTPException(status_code=400, detail="Status must be 'accepted' or 'declined'")

    db = await get_db()
    rows = await db.execute_fetchall(
        "SELECT id, dj_id, group_name, event_title, discord_channel_id, status FROM bookings WHERE id = ?",
        (booking_id,),
    )
    if not rows:
        raise HTTPException(status_code=404, detail="Booking not found")

    booking = rows[0]
    if booking[5] != "pending":
        raise HTTPException(status_code=400, detail="Booking already responded to")

    await db.execute(
        "UPDATE bookings SET status = ?, updated_at = datetime('now') WHERE id = ?",
        (req.status, booking_id),
    )
    await db.commit()

    # Notify the group's Discord channel if set
    if bot_ready.is_set() and booking[4]:
        asyncio.create_task(
            _notify_group_booking_response(booking_id, booking, req.status)
        )

    return {"status": req.status}


async def _notify_group_booking_response(booking_id: int, booking, status: str):
    """Post a message to the group's channel about the DJ's response."""
    try:
        channel_id = booking[4]
        db = await get_db()
        dj_rows = await db.execute_fetchall(
            "SELECT name FROM dj_profiles WHERE id = ?", (booking[1],)
        )
        dj_name = dj_rows[0][0] if dj_rows else "Unknown DJ"

        emoji = "\u2705" if status == "accepted" else "\u274c"
        channel = bot.get_channel(channel_id)
        if channel is None:
            channel = await bot.fetch_channel(channel_id)
        await channel.send(
            f"{emoji} **{dj_name}** has **{status}** the booking for "
            f"**{booking[3]}** on {booking[2]}."
        )
    except Exception:
        log.exception("Failed to notify group about booking %s response", booking_id)


@router.get("/bookings/group/{group_name}")
async def list_group_bookings(group_name: str):
    """List all bookings created by a specific group."""
    db = await get_db()
    bookings = await db.execute_fetchall(
        """SELECT b.id, p.name as dj_name, b.event_title, b.event_date,
                  b.start_time, b.duration, b.message, b.status, b.created_at
           FROM bookings b JOIN dj_profiles p ON b.dj_id = p.id
           WHERE b.group_name = ? COLLATE NOCASE
           ORDER BY b.created_at DESC""",
        (group_name,),
    )
    return [
        {
            "id": b[0], "dj_name": b[1], "event_title": b[2],
            "event_date": b[3], "start_time": b[4], "duration": b[5],
            "message": b[6], "status": b[7], "created_at": b[8],
        }
        for b in bookings
    ]
