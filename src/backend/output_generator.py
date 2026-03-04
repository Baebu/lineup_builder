"""Standalone text generator — **no Tkinter dependency**.

This module takes an ``EventSnapshot`` (a frozen, pure-Python data object)
and returns fully-formatted output strings for every supported format:

* **Discord** — ``#`` headers, ``<t:UNIX:t>`` timestamps, ``**bold**`` names.
* **Plain text (local)** — ``HH:MM`` times with local timezone abbreviation.
* **Quest / PC** — VRCDN stream links only.

Because the generator is a pure function of data, it is trivially unit-testable
without ever instantiating a Tkinter root window.

Example
-------
    from src.backend.lineup_model import EventSnapshot, SlotData
    from src.backend.output_generator import OutputGenerator

    snap = EventSnapshot(
        title="Friday Night Beats", vol="3",
        timestamp="2025-06-01 20:00",
        genres=["House", "Techno"],
        slots=[SlotData("DJ Alpha", "House", 60)],
        output_format="discord",
    )
    print(OutputGenerator.generate(snap))
"""

from __future__ import annotations

import datetime
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .lineup_model import EventSnapshot


class OutputGenerator:
    """Pure-function text builder.  Every public method is ``@staticmethod``."""

    # ── Public entry point ────────────────────────────────────────────────

    @staticmethod
    def generate(snap: "EventSnapshot") -> str:
        """Return the formatted output string for *snap*'s ``output_format``."""
        fmt = snap.output_format
        if fmt in ("quest", "pc"):
            return OutputGenerator._generate_stream_links(snap, fmt)
        if fmt == "local":
            return OutputGenerator._generate_plain(snap)
        return OutputGenerator._generate_discord(snap)

    # ── Slot start-time labels (HH:MM) ────────────────────────────────────

    @staticmethod
    def compute_slot_times(snap: "EventSnapshot") -> list[str]:
        """Return a list of ``HH:MM`` strings — one per slot — for UI labels.

        This lets the UI update its time labels without parsing the output text.
        """
        start = snap.start_datetime
        result: list[str] = []
        ptr = start
        for slot in snap.slots:
            result.append(ptr.strftime("%H:%M"))
            ptr += datetime.timedelta(minutes=slot.duration)
        return result

    # ── VRCDN link conversion ─────────────────────────────────────────────

    @staticmethod
    def vrcdn_convert(link: str, fmt: str) -> str:
        """Return a VRCDN link reformatted for *fmt* (``'quest'`` or ``'pc'``).

        Non-VRCDN links are returned unchanged.
        """
        if not link:
            return link
        m = re.match(
            r"(?:https://stream\.vrcdn\.live/live/|rtspt://stream\.vrcdn\.live/live/)"
            r"(.+?)(?:\.live\.ts)?$",
            link,
        )
        if not m:
            return link
        key = m.group(1)
        if fmt == "quest":
            return f"https://stream.vrcdn.live/live/{key}.live.ts"
        return f"rtspt://stream.vrcdn.live/live/{key}"

    # ── Private builders ──────────────────────────────────────────────────

    @staticmethod
    def _generate_discord(snap: "EventSnapshot") -> str:
        lines: list[str] = []

        # Title
        if snap.title:
            lines.append(f"# {snap.full_title}")

        # Timestamp
        start = snap.start_datetime
        unix = int(start.timestamp())
        lines.append(f"# <t:{unix}:F> (<t:{unix}:R>)")

        # Genres
        if snap.genres:
            lines.append(f"## {' // '.join(snap.genres)}")

        # Lineup header
        lines.append("### LINEUP")

        ptr = start
        for idx, slot in enumerate(snap.slots, start=1):
            name = slot.name or str(idx)
            if snap.names_only:
                lines.append(name)
            else:
                genre_str = f" ({slot.genre})" if slot.genre else ""
                ts = int(ptr.timestamp())
                lines.append(f"<t:{ts}:t> | **{name}**{genre_str}")
            ptr += datetime.timedelta(minutes=slot.duration)

        # Open Decks
        if snap.open_decks.enabled:
            lines.append("\n### OPEN DECKS")
            for i in range(snap.open_decks.count):
                ts = int(ptr.timestamp())
                lines.append(f"<t:{ts}:t> | Slot {i + 1}: [Available]")
                ptr += datetime.timedelta(minutes=snap.open_decks.duration)

        return "\n".join(lines)

    @staticmethod
    def _generate_plain(snap: "EventSnapshot") -> str:
        lines: list[str] = []

        # Title
        if snap.title:
            lines.append(snap.full_title)

        # Timestamp + timezone
        start = snap.start_datetime
        local_tz = datetime.datetime.now().astimezone().tzname()
        if sum(1 for c in local_tz if c.isupper()) >= 3:
            local_tz = "".join(c for c in local_tz if c.isupper())
        lines.append(f"{start.strftime('%Y-%m-%d @ %H:%M')} ({local_tz})")

        # Genres
        if snap.genres:
            lines.append(" // ".join(snap.genres))

        # Lineup header
        lines.append("LINEUP")

        ptr = start
        for idx, slot in enumerate(snap.slots, start=1):
            name = slot.name or str(idx)
            if snap.names_only:
                lines.append(name)
            else:
                genre_str = f" ({slot.genre})" if slot.genre else ""
                lines.append(f"{ptr.strftime('%H:%M')} | {name}{genre_str}")
            ptr += datetime.timedelta(minutes=slot.duration)

        # Open Decks
        if snap.open_decks.enabled:
            lines.append("\nOPEN DECKS")
            for i in range(snap.open_decks.count):
                lines.append(f"{ptr.strftime('%H:%M')} | Slot {i + 1}: [Available]")
                ptr += datetime.timedelta(minutes=snap.open_decks.duration)

        return "\n".join(lines)

    @staticmethod
    def _generate_stream_links(snap: "EventSnapshot", fmt: str) -> str:
        """Build Quest / PC stream-link-only output."""
        links: list[str] = []
        dj_lookup = {d.name: d for d in snap.saved_djs}

        for slot in snap.slots:
            name = slot.name.strip()
            if not name:
                continue
            dj = dj_lookup.get(name)
            if dj and dj.stream:
                link = dj.stream if dj.exact_link else OutputGenerator.vrcdn_convert(dj.stream, fmt)
                links.append(link)

        if not links:
            return ""
        return "\n".join(f"```\n{link}\n```" for link in links)
