"""Pure-Python value objects for lineup events.

These dataclasses capture the complete state of a lineup — slots, DJ metadata,
and a frozen snapshot for output generation — with **zero** dependency on any
GUI framework.
"""

from __future__ import annotations

import datetime
from dataclasses import dataclass, field


@dataclass
class SlotData:
    """One performer slot — pure data, no widgets."""
    name: str = ""
    genre: str = ""
    duration: int = 60


@dataclass
class DJInfo:
    """Saved DJ metadata from the library."""
    name: str = ""
    stream: str = ""
    exact_link: bool = False


@dataclass
class EventSnapshot:
    """An immutable snapshot of the full event state.

    ``OutputGenerator`` works exclusively with this — it never touches
    GUI widgets or the live model.
    """
    title: str = ""
    vol: str = ""
    timestamp: str = ""            # "YYYY-MM-DD HH:MM"
    genres: list[str] = field(default_factory=list)
    slots: list[SlotData] = field(default_factory=list)
    names_only: bool = False
    output_format: str = "discord"  # "discord" | "local" | "quest" | "pc"
    saved_djs: list[DJInfo] = field(default_factory=list)

    @property
    def start_datetime(self) -> datetime.datetime:
        """Parse ``self.timestamp`` into a ``datetime``, falling back to *now*."""
        try:
            return datetime.datetime.strptime(self.timestamp, "%Y-%m-%d %H:%M")
        except (ValueError, TypeError):
            return datetime.datetime.now()

    @property
    def full_title(self) -> str:
        if self.vol.isdigit():
            return f"{self.title} VOL.{self.vol}"
        return self.title
