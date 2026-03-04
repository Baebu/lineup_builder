"""Pure-Python data model for a lineup event.

This module defines plain dataclasses that capture the *complete* state of a
lineup — titles, timestamps, slots, open-decks config, and DJ metadata — with
**zero** dependency on Tkinter or any GUI framework.

The model is the single source of truth.  UI widgets read from / write to
instance attributes, and the ``EventBus`` broadcasts changes so other
subsystems (output generation, auto-save, etc.) can react without coupling.

Typical flow
------------
1. User types in a ``CTkEntry`` → UI handler calls ``model.set_title("…")``.
2. The setter publishes ``"model_changed"`` on the bus.
3. ``OutputGenerator`` (subscribed) rebuilds the preview text.
4. The output panel (subscribed) writes the new text to the textbox.
"""

from __future__ import annotations

import datetime
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .event_bus import EventBus


# ── Value objects ─────────────────────────────────────────────────────────

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
class OpenDecksConfig:
    """Open-decks section configuration."""
    enabled: bool = False
    count: int = 4
    duration: int = 30


@dataclass
class EventSnapshot:
    """An immutable snapshot of the full event state.

    ``OutputGenerator`` works exclusively with this — it never touches
    Tkinter widgets, ``StringVar``s, or the live model.
    """
    title: str = ""
    vol: str = ""
    timestamp: str = ""            # "YYYY-MM-DD HH:MM"
    genres: list[str] = field(default_factory=list)
    slots: list[SlotData] = field(default_factory=list)
    names_only: bool = False
    output_format: str = "discord"  # "discord" | "local" | "quest" | "pc"
    open_decks: OpenDecksConfig = field(default_factory=OpenDecksConfig)
    saved_djs: list[DJInfo] = field(default_factory=list)

    # ── Derived helpers ───────────────────────────────────────────────

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


# ── Live mutable model ────────────────────────────────────────────────────

class LineupModel:
    """The runtime model that backs the editor UI.

    Every mutating setter publishes ``"model_changed"`` on the bus so
    subscribers (output panel, auto-save timer, etc.) can react.

    The model is deliberately *not* a dataclass itself because it manages
    change-notification logic and provides ``snapshot()`` for consumers
    that need a frozen view.
    """

    def __init__(self, bus: EventBus) -> None:
        self._bus = bus

        self.title: str = ""
        self.vol: str = ""
        self.timestamp: str = ""
        self.master_duration: int = 60
        self.genres: list[str] = []
        self.slots: list[SlotData] = []
        self.names_only: bool = False
        self.output_format: str = "discord"
        self.open_decks: OpenDecksConfig = OpenDecksConfig()
        self.saved_djs: list[DJInfo] = []

    # ── Snapshot ──────────────────────────────────────────────────────

    def snapshot(self) -> EventSnapshot:
        """Return a frozen copy suitable for ``OutputGenerator``."""
        return EventSnapshot(
            title=self.title,
            vol=self.vol,
            timestamp=self.timestamp,
            genres=list(self.genres),
            slots=[SlotData(s.name, s.genre, s.duration) for s in self.slots],
            names_only=self.names_only,
            output_format=self.output_format,
            open_decks=OpenDecksConfig(
                enabled=self.open_decks.enabled,
                count=self.open_decks.count,
                duration=self.open_decks.duration,
            ),
            saved_djs=[DJInfo(d.name, d.stream, d.exact_link) for d in self.saved_djs],
        )

    # ── Bulk load (e.g. loading a saved event) ────────────────────────

    def load_from_dict(self, data: dict) -> None:
        """Populate the model from a plain dict (event save format)."""
        self.title = data.get("title", "")
        self.vol = data.get("vol", "")
        self.timestamp = data.get("timestamp", "")
        self.master_duration = int(data.get("master_duration", 60))
        self.genres = list(data.get("genres", []))
        self.names_only = bool(data.get("names_only", False))
        self.open_decks = OpenDecksConfig(
            enabled=bool(data.get("include_od", False)),
            count=int(data.get("od_count", 4)),
            duration=int(data.get("od_duration", 30)),
        )
        self.slots = [
            SlotData(
                name=s.get("name", ""),
                genre=s.get("genre", ""),
                duration=int(s.get("duration", 60)),
            )
            for s in data.get("slots", [])
        ]
        self._notify()

    def to_dict(self) -> dict:
        """Serialize to the same plain-dict format used for persistence."""
        return {
            "title": self.title,
            "vol": self.vol,
            "timestamp": self.timestamp,
            "master_duration": str(self.master_duration),
            "genres": list(self.genres),
            "names_only": self.names_only,
            "include_od": self.open_decks.enabled,
            "od_count": str(self.open_decks.count),
            "od_duration": str(self.open_decks.duration),
            "slots": [
                {"name": s.name, "genre": s.genre, "duration": str(s.duration)}
                for s in self.slots
            ],
        }

    # ── Change notification ───────────────────────────────────────────

    def notify(self) -> None:
        """Publicly trigger a model-changed broadcast.

        Useful when the UI has mutated a ``SlotData`` in-place and needs
        to tell subscribers about it.
        """
        self._notify()

    def _notify(self) -> None:
        self._bus.publish("model_changed")
