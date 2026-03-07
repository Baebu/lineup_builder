import dearpygui.dearpygui as dpg

from .types import DJInfo, EventSnapshot, SlotData
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

        dj_list = [
            DJInfo(
                name=d.get("name", ""),
                stream=d.get("stream", ""),
                exact_link=bool(d.get("exact_link")),
            )
            for d in self.saved_djs
        ]

        # Merge persistent links over the event-specific ones
        merged_social = dict(getattr(self, "social_links", {}))
        for key, val in getattr(self, "persistent_links", {}).items():
            if isinstance(val, dict) and val.get("enabled") and val.get("link", "").strip():
                merged_social[key] = val["link"].strip()

        return EventSnapshot(
            title=self.event_title_var.get().strip(),
            vol=self.event_vol_var.get().strip(),
            timestamp=self.event_timestamp.get(),
            genres=list(self.active_genres),
            slots=slots,
            names_only=self.names_only.get(),
            output_format=self.output_format.get(),
            saved_djs=dj_list,
            social_links=merged_social,
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

        # Sync button themes for formats and times toggle
        if hasattr(self, "output_format") and hasattr(self, "names_only"):
            fmt = self.output_format.get()
            if dpg.does_item_exist("fmt_discord"):
                dpg.bind_item_theme("fmt_discord", "success_btn_theme" if fmt == "discord" else "secondary_btn_theme")
            if dpg.does_item_exist("fmt_plain"):
                dpg.bind_item_theme("fmt_plain", "success_btn_theme" if fmt == "local" else "secondary_btn_theme")
            if dpg.does_item_exist("fmt_quest"):
                dpg.bind_item_theme("fmt_quest", "success_btn_theme" if fmt == "quest" else "secondary_btn_theme")
            if dpg.does_item_exist("fmt_pc"):
                dpg.bind_item_theme("fmt_pc", "success_btn_theme" if fmt == "pc" else "secondary_btn_theme")
                
            if dpg.does_item_exist("fmt_times"):
                times_on = not self.names_only.get()
                dpg.configure_item("fmt_times", label="Times on" if times_on else "Times off")
                dpg.bind_item_theme("fmt_times", "success_btn_theme" if times_on else "secondary_btn_theme")

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
