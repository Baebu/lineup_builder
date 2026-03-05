import dearpygui.dearpygui as dpg

from .lineup_model import DJInfo, EventSnapshot, OpenDecksConfig, SlotData
from .output_generator import OutputGenerator


class OutputMixin:
    """Bridges the Tkinter UI with the pure-Python OutputGenerator.

    Reads widget state → builds an ``EventSnapshot`` → delegates text
    generation to ``OutputGenerator`` → writes the result back to the
    output textbox.  Copy helpers and format-button state remain here
    because they are inherently UI concerns.
    """

    # ── VRCDN link conversion (thin wrapper kept for backward compat) ─────

    @staticmethod
    def _vrcdn_convert(link: str, fmt: str) -> str:
        """Delegate to ``OutputGenerator.vrcdn_convert``."""
        return OutputGenerator.vrcdn_convert(link, fmt)

    # ── Snapshot builder ──────────────────────────────────────────────────

    def _build_snapshot(self) -> EventSnapshot:
        """Harvest the current UI state into an ``EventSnapshot``."""
        slots = []
        for s in self.slots:
            try:
                dur = int(s.duration_var.get())
            except (ValueError, AttributeError):
                dur = 0
            slots.append(SlotData(
                name=s.name_var.get().strip(),
                genre=s.genre_var.get().strip(),
                duration=dur,
            ))

        try:
            od_count = int(self.od_count.get())
        except (ValueError, AttributeError):
            od_count = 0
        try:
            od_dur = int(self.od_duration.get())
        except (ValueError, AttributeError):
            od_dur = 0

        dj_list = [
            DJInfo(
                name=d.get("name", ""),
                stream=d.get("stream", ""),
                exact_link=bool(d.get("exact_link")),
            )
            for d in self.saved_djs
        ]

        return EventSnapshot(
            title=self.event_title_var.get().strip(),
            vol=self.event_vol_var.get().strip(),
            timestamp=self.event_timestamp.get(),
            genres=list(self.active_genres),
            slots=slots,
            names_only=self.names_only.get(),
            output_format=self.output_format.get(),
            open_decks=OpenDecksConfig(
                enabled=self.include_od.get(),
                count=od_count,
                duration=od_dur,
            ),
            saved_djs=dj_list,
        )

    # ── Main output builder ───────────────────────────────────────────────

    def update_output(self):
        snap = self._build_snapshot()

        # Always refresh slot start-time labels regardless of output format
        slot_times = OutputGenerator.compute_slot_times(snap)
        for _slot, time_str in zip(self.slots, slot_times):
            tag = f"slot_time_{_slot._id}"
            if dpg.does_item_exist(tag):
                dpg.set_value(tag, time_str)

        # Delegate the heavy lifting to the pure-Python generator
        body = OutputGenerator.generate(snap)

        if dpg.does_item_exist("output_text"):
            dpg.set_value("output_text", body)

    # ── Copy helpers ──────────────────────────────────────────────────────

    def copy_template(self):
        import threading
        text = dpg.get_value("output_text") if dpg.does_item_exist("output_text") else ""
        dpg.set_clipboard_text(text)

    def copy_quest_links(self):
        self.set_quest_view()
        self._copy_output_to_clipboard()

    def copy_pc_links(self):
        self.set_pc_view()
        self._copy_output_to_clipboard()

    def _copy_output_to_clipboard(self):
        text = dpg.get_value("output_text") if dpg.does_item_exist("output_text") else ""
        dpg.set_clipboard_text(text)

    # ── Format-button state ───────────────────────────────────────────────

    def toggle_format(self):
        self.output_format.set("discord")
        self.update_output()

    def set_plain_text(self):
        self.output_format.set("local")
        self.update_output()

    def set_quest_view(self):
        self.output_format.set("quest")
        self.update_output()

    def set_pc_view(self):
        self.output_format.set("pc")
        self.update_output()
