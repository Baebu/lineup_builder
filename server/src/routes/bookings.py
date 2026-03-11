"""
Booking routes — create, list, respond, notifications.
"""

import asyncio

import discord
from fastapi import APIRouter, HTTPException
from pymongo.collation import Collation

from config import log
from db import bookings, dj_profiles, next_id, _now
from models.schemas import BookingCreateRequest, BookingRespondRequest
from services.discord_bot import bot, bot_ready

router = APIRouter()

_CI = Collation(locale="en", strength=2)


@router.post("/booking")
async def create_booking(req: BookingCreateRequest):
    dj = await dj_profiles().find_one({"name": req.dj_name}, collation=_CI)
    if not dj:
        raise HTTPException(status_code=404, detail="DJ not found")
    dj_id = dj["id"]

    booking_id = await next_id("bookings")
    await bookings().insert_one({
        "id": booking_id,
        "dj_id": dj_id,
        "group_name": req.group_name,
        "event_title": req.event_title,
        "event_date": req.event_date,
        "start_time": req.start_time,
        "duration": req.duration,
        "message": req.message,
        "discord_channel_id": req.discord_channel_id,
        "status": "pending",
        "created_at": _now(),
        "updated_at": _now(),
    })

    # Notify DJ via Discord DM if bot is ready
    if bot_ready.is_set():
        asyncio.create_task(_notify_dj_booking(dj_id, req, booking_id))

    return {"id": booking_id, "status": "pending"}


async def _notify_dj_booking(dj_id: int, req: BookingCreateRequest, booking_id: int):
    """Send a Discord DM to the DJ about a new booking request."""
    try:
        dj = await dj_profiles().find_one({"id": dj_id})
        if not dj:
            return
        dj_name = dj["name"]

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
    dj = await dj_profiles().find_one({"name": dj_name}, collation=_CI)
    if not dj:
        raise HTTPException(status_code=404, detail="DJ not found")
    dj_id = dj["id"]

    results = []
    async for b in bookings().find({"dj_id": dj_id}).sort("created_at", -1):
        results.append({
            "id": b["id"], "group_name": b.get("group_name", ""),
            "event_title": b.get("event_title", ""), "event_date": b.get("event_date", ""),
            "start_time": b.get("start_time", ""), "duration": b.get("duration", 60),
            "message": b.get("message", ""), "status": b.get("status", "pending"),
            "created_at": b.get("created_at", ""),
        })
    return results


@router.put("/booking/{booking_id}/respond")
async def respond_to_booking(booking_id: int, req: BookingRespondRequest):
    if req.status not in ("accepted", "declined"):
        raise HTTPException(status_code=400, detail="Status must be 'accepted' or 'declined'")

    b = await bookings().find_one({"id": booking_id})
    if not b:
        raise HTTPException(status_code=404, detail="Booking not found")

    if b.get("status") != "pending":
        raise HTTPException(status_code=400, detail="Booking already responded to")

    await bookings().update_one(
        {"id": booking_id},
        {"$set": {"status": req.status, "updated_at": _now()}},
    )

    # Notify the group's Discord channel if set
    if bot_ready.is_set() and b.get("discord_channel_id"):
        asyncio.create_task(
            _notify_group_booking_response(booking_id, b, req.status)
        )

    return {"status": req.status}


async def _notify_group_booking_response(booking_id: int, booking: dict, status: str):
    """Post a message to the group's channel about the DJ's response."""
    try:
        channel_id = booking["discord_channel_id"]
        dj = await dj_profiles().find_one({"id": booking["dj_id"]})
        dj_name = dj["name"] if dj else "Unknown DJ"

        emoji = "\u2705" if status == "accepted" else "\u274c"
        channel = bot.get_channel(channel_id)
        if channel is None:
            channel = await bot.fetch_channel(channel_id)
        await channel.send(
            f"{emoji} **{dj_name}** has **{status}** the booking for "
            f"**{booking.get('event_title', '')}** on {booking.get('group_name', '')}."
        )
    except Exception:
        log.exception("Failed to notify group about booking %s response", booking_id)


@router.get("/bookings/group/{group_name:path}")
async def list_group_bookings(group_name: str):
    """List all bookings created by a specific group."""
    results = []
    async for b in bookings().find(
        {"group_name": group_name},
        collation=_CI,
    ).sort("created_at", -1):
        dj = await dj_profiles().find_one({"id": b["dj_id"]})
        dj_name = dj["name"] if dj else "Unknown"
        results.append({
            "id": b["id"], "dj_name": dj_name,
            "event_title": b.get("event_title", ""), "event_date": b.get("event_date", ""),
            "start_time": b.get("start_time", ""), "duration": b.get("duration", 60),
            "message": b.get("message", ""), "status": b.get("status", "pending"),
            "created_at": b.get("created_at", ""),
        })
    return results
