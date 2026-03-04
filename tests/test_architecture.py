"""Unit tests for the pure-Python architecture layer.

These tests exercise ``EventBus``, ``LineupModel``, ``EventSnapshot``, and
``OutputGenerator`` — **no Tkinter root window required**.

Run with::

    pytest tests/ -v
"""

from __future__ import annotations

import datetime
import re

import pytest

from src.backend.event_bus import EventBus
from src.backend.lineup_model import (
    DJInfo,
    EventSnapshot,
    LineupModel,
    OpenDecksConfig,
    SlotData,
)
from src.backend.output_generator import OutputGenerator


# ══════════════════════════════════════════════════════════════════════════
#  EventBus
# ══════════════════════════════════════════════════════════════════════════

class TestEventBus:
    def test_subscribe_and_publish(self):
        bus = EventBus()
        received = []
        bus.subscribe("test_event", lambda event, **kw: received.append((event, kw)))
        bus.publish("test_event", data=42)
        assert received == [("test_event", {"data": 42})]

    def test_multiple_subscribers(self):
        bus = EventBus()
        a, b = [], []
        bus.subscribe("ev", lambda e, **kw: a.append(1))
        bus.subscribe("ev", lambda e, **kw: b.append(1))
        bus.publish("ev")
        assert len(a) == 1 and len(b) == 1

    def test_unsubscribe(self):
        bus = EventBus()
        calls = []
        cb = lambda e, **kw: calls.append(1)
        bus.subscribe("ev", cb)
        bus.unsubscribe("ev", cb)
        bus.publish("ev")
        assert calls == []

    def test_unsubscribe_noop_if_not_registered(self):
        bus = EventBus()
        bus.unsubscribe("nonexistent", lambda e, **kw: None)  # should not raise

    def test_duplicate_subscribe_ignored(self):
        bus = EventBus()
        calls = []
        cb = lambda e, **kw: calls.append(1)
        bus.subscribe("ev", cb)
        bus.subscribe("ev", cb)  # duplicate
        bus.publish("ev")
        assert calls == [1]  # only one call

    def test_clear(self):
        bus = EventBus()
        calls = []
        bus.subscribe("ev", lambda e, **kw: calls.append(1))
        bus.clear()
        bus.publish("ev")
        assert calls == []

    def test_different_events_isolated(self):
        bus = EventBus()
        a_calls, b_calls = [], []
        bus.subscribe("a", lambda e, **kw: a_calls.append(1))
        bus.subscribe("b", lambda e, **kw: b_calls.append(1))
        bus.publish("a")
        assert len(a_calls) == 1
        assert len(b_calls) == 0


# ══════════════════════════════════════════════════════════════════════════
#  LineupModel
# ══════════════════════════════════════════════════════════════════════════

class TestLineupModel:
    def _make(self):
        bus = EventBus()
        model = LineupModel(bus)
        return bus, model

    def test_default_state(self):
        _, model = self._make()
        assert model.title == ""
        assert model.slots == []
        assert model.output_format == "discord"

    def test_load_from_dict(self):
        bus, model = self._make()
        notified = []
        bus.subscribe("model_changed", lambda *a, **kw: notified.append(1))

        model.load_from_dict({
            "title": "Friday Night",
            "vol": "3",
            "timestamp": "2025-06-01 20:00",
            "genres": ["House", "Techno"],
            "slots": [
                {"name": "DJ Alpha", "genre": "House", "duration": "60"},
                {"name": "DJ Beta", "genre": "Techno", "duration": "45"},
            ],
            "include_od": True,
            "od_count": "2",
            "od_duration": "30",
        })

        assert model.title == "Friday Night"
        assert model.vol == "3"
        assert len(model.slots) == 2
        assert model.slots[0].name == "DJ Alpha"
        assert model.slots[1].duration == 45
        assert model.open_decks.enabled is True
        assert model.open_decks.count == 2
        assert notified == [1]

    def test_to_dict_roundtrip(self):
        _, model = self._make()
        original = {
            "title": "Test",
            "vol": "1",
            "timestamp": "2025-06-01 20:00",
            "master_duration": "60",
            "genres": ["House"],
            "names_only": False,
            "include_od": False,
            "od_count": "4",
            "od_duration": "30",
            "slots": [{"name": "DJ A", "genre": "House", "duration": "60"}],
        }
        model.load_from_dict(original)
        result = model.to_dict()
        assert result["title"] == "Test"
        assert result["vol"] == "1"
        assert result["slots"][0]["name"] == "DJ A"

    def test_snapshot_is_independent_copy(self):
        _, model = self._make()
        model.title = "Original"
        model.slots = [SlotData("DJ A", "House", 60)]
        snap = model.snapshot()
        model.title = "Changed"
        model.slots[0].name = "DJ B"
        assert snap.title == "Original"
        assert snap.slots[0].name == "DJ A"

    def test_notify_publishes(self):
        bus, model = self._make()
        calls = []
        bus.subscribe("model_changed", lambda *a, **kw: calls.append(1))
        model.notify()
        assert calls == [1]


# ══════════════════════════════════════════════════════════════════════════
#  EventSnapshot
# ══════════════════════════════════════════════════════════════════════════

class TestEventSnapshot:
    def test_full_title_with_vol(self):
        snap = EventSnapshot(title="Friday Night", vol="3")
        assert snap.full_title == "Friday Night VOL.3"

    def test_full_title_without_vol(self):
        snap = EventSnapshot(title="Friday Night", vol="")
        assert snap.full_title == "Friday Night"

    def test_full_title_non_numeric_vol(self):
        snap = EventSnapshot(title="Friday Night", vol="abc")
        assert snap.full_title == "Friday Night"

    def test_start_datetime_valid(self):
        snap = EventSnapshot(timestamp="2025-06-01 20:00")
        assert snap.start_datetime == datetime.datetime(2025, 6, 1, 20, 0)

    def test_start_datetime_fallback(self):
        snap = EventSnapshot(timestamp="bad")
        # Should not raise, falls back to now
        assert isinstance(snap.start_datetime, datetime.datetime)


# ══════════════════════════════════════════════════════════════════════════
#  OutputGenerator — VRCDN conversion
# ══════════════════════════════════════════════════════════════════════════

class TestVRCDNConvert:
    def test_quest_format(self):
        link = "rtspt://stream.vrcdn.live/live/mykey"
        result = OutputGenerator.vrcdn_convert(link, "quest")
        assert result == "https://stream.vrcdn.live/live/mykey.live.ts"

    def test_pc_format(self):
        link = "https://stream.vrcdn.live/live/mykey.live.ts"
        result = OutputGenerator.vrcdn_convert(link, "pc")
        assert result == "rtspt://stream.vrcdn.live/live/mykey"

    def test_non_vrcdn_passthrough(self):
        link = "https://twitch.tv/someone"
        assert OutputGenerator.vrcdn_convert(link, "quest") == link
        assert OutputGenerator.vrcdn_convert(link, "pc") == link

    def test_empty_string(self):
        assert OutputGenerator.vrcdn_convert("", "quest") == ""

    def test_none_passthrough(self):
        assert OutputGenerator.vrcdn_convert(None, "quest") is None


# ══════════════════════════════════════════════════════════════════════════
#  OutputGenerator — Discord format
# ══════════════════════════════════════════════════════════════════════════

class TestDiscordOutput:
    @pytest.fixture
    def base_snap(self):
        return EventSnapshot(
            title="Friday Night Beats",
            vol="3",
            timestamp="2025-06-01 20:00",
            genres=["House", "Techno"],
            slots=[
                SlotData("DJ Alpha", "House", 60),
                SlotData("DJ Beta", "Techno", 45),
            ],
            output_format="discord",
        )

    def test_contains_title(self, base_snap):
        out = OutputGenerator.generate(base_snap)
        assert "# Friday Night Beats VOL.3" in out

    def test_contains_discord_timestamp(self, base_snap):
        out = OutputGenerator.generate(base_snap)
        start = datetime.datetime(2025, 6, 1, 20, 0)
        unix = int(start.timestamp())
        assert f"<t:{unix}:F>" in out
        assert f"<t:{unix}:R>" in out

    def test_contains_genres(self, base_snap):
        out = OutputGenerator.generate(base_snap)
        assert "## House // Techno" in out

    def test_contains_lineup_header(self, base_snap):
        out = OutputGenerator.generate(base_snap)
        assert "### LINEUP" in out

    def test_slot_times_are_sequential(self, base_snap):
        out = OutputGenerator.generate(base_snap)
        start = datetime.datetime(2025, 6, 1, 20, 0)
        unix1 = int(start.timestamp())
        unix2 = int((start + datetime.timedelta(minutes=60)).timestamp())
        assert f"<t:{unix1}:t> | **DJ Alpha** (House)" in out
        assert f"<t:{unix2}:t> | **DJ Beta** (Techno)" in out

    def test_names_only_mode(self):
        snap = EventSnapshot(
            title="Test",
            timestamp="2025-06-01 20:00",
            slots=[SlotData("DJ Alpha", "House", 60)],
            names_only=True,
            output_format="discord",
        )
        out = OutputGenerator.generate(snap)
        assert "• DJ Alpha" in out
        assert "<t:" not in out.split("### LINEUP")[1]

    def test_empty_slot_name_shows_index(self):
        snap = EventSnapshot(
            title="Test",
            timestamp="2025-06-01 20:00",
            slots=[SlotData("", "", 60)],
            output_format="discord",
        )
        out = OutputGenerator.generate(snap)
        assert "**1**" in out

    def test_open_decks(self):
        snap = EventSnapshot(
            title="Test",
            timestamp="2025-06-01 20:00",
            slots=[SlotData("DJ A", "", 60)],
            open_decks=OpenDecksConfig(enabled=True, count=3, duration=30),
            output_format="discord",
        )
        out = OutputGenerator.generate(snap)
        assert "### OPEN DECKS" in out
        assert "Slot 1: [Available]" in out
        assert "Slot 2: [Available]" in out
        assert "Slot 3: [Available]" in out

    def test_no_open_decks_when_disabled(self, base_snap):
        out = OutputGenerator.generate(base_snap)
        assert "OPEN DECKS" not in out


# ══════════════════════════════════════════════════════════════════════════
#  OutputGenerator — Plain text format
# ══════════════════════════════════════════════════════════════════════════

class TestPlainTextOutput:
    @pytest.fixture
    def base_snap(self):
        return EventSnapshot(
            title="Friday Night Beats",
            vol="3",
            timestamp="2025-06-01 20:00",
            genres=["House", "Techno"],
            slots=[
                SlotData("DJ Alpha", "House", 60),
                SlotData("DJ Beta", "Techno", 45),
            ],
            output_format="local",
        )

    def test_no_discord_markdown(self, base_snap):
        out = OutputGenerator.generate(base_snap)
        assert "# " not in out
        assert "## " not in out
        assert "**" not in out

    def test_title_present(self, base_snap):
        out = OutputGenerator.generate(base_snap)
        assert "Friday Night Beats VOL.3" in out

    def test_time_format(self, base_snap):
        out = OutputGenerator.generate(base_snap)
        assert "20:00 | DJ Alpha (House)" in out
        assert "21:00 | DJ Beta (Techno)" in out

    def test_contains_lineup_header(self, base_snap):
        out = OutputGenerator.generate(base_snap)
        assert "LINEUP" in out
        assert "### LINEUP" not in out


# ══════════════════════════════════════════════════════════════════════════
#  OutputGenerator — Stream links (Quest/PC)
# ══════════════════════════════════════════════════════════════════════════

class TestStreamLinksOutput:
    def test_quest_links(self):
        snap = EventSnapshot(
            output_format="quest",
            slots=[SlotData("DJ A", "", 60)],
            saved_djs=[DJInfo("DJ A", "rtspt://stream.vrcdn.live/live/mykey")],
        )
        out = OutputGenerator.generate(snap)
        assert "https://stream.vrcdn.live/live/mykey.live.ts" in out
        assert "```" in out

    def test_pc_links(self):
        snap = EventSnapshot(
            output_format="pc",
            slots=[SlotData("DJ A", "", 60)],
            saved_djs=[DJInfo("DJ A", "https://stream.vrcdn.live/live/mykey.live.ts")],
        )
        out = OutputGenerator.generate(snap)
        assert "rtspt://stream.vrcdn.live/live/mykey" in out

    def test_exact_link_bypasses_conversion(self):
        snap = EventSnapshot(
            output_format="quest",
            slots=[SlotData("DJ A", "", 60)],
            saved_djs=[DJInfo("DJ A", "https://custom.stream/path", exact_link=True)],
        )
        out = OutputGenerator.generate(snap)
        assert "https://custom.stream/path" in out

    def test_missing_stream_excluded(self):
        snap = EventSnapshot(
            output_format="quest",
            slots=[SlotData("DJ A", "", 60), SlotData("DJ B", "", 60)],
            saved_djs=[DJInfo("DJ A", ""), DJInfo("DJ B", "rtspt://stream.vrcdn.live/live/key")],
        )
        out = OutputGenerator.generate(snap)
        assert "key" in out
        # DJ A has no stream, should not appear
        lines = [l for l in out.splitlines() if l.strip() and l.strip() != "```"]
        assert len(lines) == 1

    def test_empty_output_when_no_streams(self):
        snap = EventSnapshot(
            output_format="quest",
            slots=[SlotData("DJ A", "", 60)],
            saved_djs=[],
        )
        out = OutputGenerator.generate(snap)
        assert out == ""


# ══════════════════════════════════════════════════════════════════════════
#  OutputGenerator — Slot time labels
# ══════════════════════════════════════════════════════════════════════════

class TestSlotTimes:
    def test_sequential_times(self):
        snap = EventSnapshot(
            timestamp="2025-06-01 20:00",
            slots=[
                SlotData("A", "", 60),
                SlotData("B", "", 45),
                SlotData("C", "", 30),
            ],
        )
        times = OutputGenerator.compute_slot_times(snap)
        assert times == ["20:00", "21:00", "21:45"]

    def test_empty_slots(self):
        snap = EventSnapshot(timestamp="2025-06-01 20:00", slots=[])
        assert OutputGenerator.compute_slot_times(snap) == []

    def test_midnight_rollover(self):
        snap = EventSnapshot(
            timestamp="2025-06-01 23:00",
            slots=[SlotData("A", "", 90), SlotData("B", "", 60)],
        )
        times = OutputGenerator.compute_slot_times(snap)
        assert times == ["23:00", "00:30"]
