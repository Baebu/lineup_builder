import datetime
import re

from .lineup_model import EventSnapshot, SlotData, DJInfo, OpenDecksConfig
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
            _slot.time_lbl.configure(text=time_str)

        # Delegate the heavy lifting to the pure-Python generator
        body = OutputGenerator.generate(snap)

        self.output_text.configure(state="normal")
        self.output_text.delete("1.0", "end")
        self.output_text.insert("1.0", body)
        self.output_text.configure(state="disabled")

    # ── Copy helpers ──────────────────────────────────────────────────────

    def _on_output_leave(self, event):
        """Hide the copy icon only when the pointer truly leaves both the textbox and button."""
        widget_under = self.winfo_containing(event.x_root, event.y_root)
        if widget_under is None:
            self.copy_icon_btn.place_forget()
            return
        w_str = str(widget_under)
        if str(self.copy_icon_btn) in w_str or str(self.output_text) in w_str:
            return
        self.copy_icon_btn.place_forget()

    def copy_template(self):
        text = self.output_text.get("1.0", "end-1c")
        self.clipboard_clear()
        self.clipboard_append(text)
        self.copy_icon_btn.configure(
            text="✓", fg_color="#059669", hover_color="#047857", text_color="#FFFFFF"
        )
        self.after(
            1500,
            lambda: self.copy_icon_btn.configure(
                text="⎘", fg_color="#3F4147", hover_color="#4F46E5", text_color="#94A3B8"
            ),
        )

    def copy_quest_links(self):
        self.set_quest_view()
        self._copy_output_to_clipboard()

    def copy_pc_links(self):
        self.set_pc_view()
        self._copy_output_to_clipboard()

    def _copy_output_to_clipboard(self):
        text = self.output_text.get("1.0", "end-1c")
        self.clipboard_clear()
        self.clipboard_append(text)

    # ── Format-button state ───────────────────────────────────────────────

    def _reset_format_btns(self):
        """Set all four format buttons to their inactive style."""
        self.format_btn.configure(fg_color="transparent", text_color="#94A3B8")
        self.plain_btn.configure(fg_color="transparent", text_color="#94A3B8")
        self.quest_btn.configure(fg_color="transparent", text_color="#94A3B8")
        self.pc_btn.configure(fg_color="transparent", text_color="#94A3B8")

    def toggle_format(self):
        self.output_format.set("discord")
        self._reset_format_btns()
        self.format_btn.configure(fg_color="#1E293B", text_color="#818CF8")
        self.update_output()

    def set_plain_text(self):
        self.output_format.set("local")
        self._reset_format_btns()
        self.plain_btn.configure(fg_color="#1E293B", text_color="#34D399")
        self.update_output()

    def set_quest_view(self):
        self.output_format.set("quest")
        self._reset_format_btns()
        self.quest_btn.configure(fg_color="#1E293B", text_color="#34D399")
        self.update_output()

    def set_pc_view(self):
        self.output_format.set("pc")
        self._reset_format_btns()
        self.pc_btn.configure(fg_color="#1E293B", text_color="#818CF8")
        self.update_output()
