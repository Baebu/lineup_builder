import datetime
import re


class OutputMixin:
    """Builds the text output and manages output-format button state."""

    # ── VRCDN link conversion ─────────────────────────────────────────────

    @staticmethod
    def _vrcdn_convert(link: str, fmt: str) -> str:
        """Return a VRCDN link reformatted for *fmt* ('quest' or 'pc').
        Non-VRCDN links are returned unchanged."""
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

    # ── Main output builder ───────────────────────────────────────────────

    def update_output(self):
        out_format = self.output_format.get()

        # ── Quest / PC: stream-link-only view ────────────────────────────
        if out_format in ("quest", "pc"):
            links = []
            for slot in self.slots:
                slot_name = slot.name_var.get().strip()
                if slot_name:
                    dj_info = next(
                        (d for d in self.saved_djs if d.get("name") == slot_name), None
                    )
                    if dj_info and dj_info.get("stream"):
                        links.append(self._vrcdn_convert(dj_info["stream"], out_format))
            body = "```\n" + "\n".join(links) + "\n```" if links else ""
            self.output_text.configure(state="normal")
            self.output_text.delete("1.0", "end")
            self.output_text.insert("1.0", body)
            self.output_text.configure(state="disabled")
            return

        # ── Discord / Plain Text view ─────────────────────────────────────
        lines = []

        event_title = self.event_title_var.get().strip()
        event_vol = self.event_vol_var.get().strip()

        if event_title:
            title_display = (
                f"{event_title} VOL.{event_vol}" if event_vol.isdigit() else event_title
            )
            lines.append(f"# {title_display}" if out_format == "discord" else title_display)

        try:
            event_start_obj = datetime.datetime.strptime(
                self.event_timestamp.get(), "%Y-%m-%d %H:%M"
            )
        except ValueError:
            event_start_obj = datetime.datetime.now()

        if out_format == "discord":
            event_unix = int(event_start_obj.timestamp())
            lines.append(f"# <t:{event_unix}:F> (<t:{event_unix}:R>)")
        else:
            local_tz = datetime.datetime.now().astimezone().tzname()
            if sum(1 for c in local_tz if c.isupper()) >= 3:
                local_tz = "".join(c for c in local_tz if c.isupper())
            lines.append(f"{event_start_obj.strftime('%Y-%m-%d @ %H:%M')} ({local_tz})")

        # Genres
        if self.active_genres:
            genres_str = " // ".join(self.active_genres)
            lines.append(
                f"## {genres_str}" if out_format == "discord" else genres_str
            )

        lines.append("### LINEUP" if out_format == "discord" else "LINEUP")

        current_pointer = event_start_obj
        names_only = self.names_only.get()

        for idx, slot in enumerate(self.slots, start=1):
            try:
                duration = int(slot.duration_var.get())
            except ValueError:
                duration = 0

            slot_name = slot.name_var.get().strip()
            slot_genre = slot.genre_var.get().strip()
            name_display = slot_name if slot_name else str(idx)

            if names_only:
                lines.append(f"• {name_display}")
            else:
                genre_str = f" ({slot_genre})" if slot_genre else ""
                if out_format == "discord":
                    unix = int(current_pointer.timestamp())
                    lines.append(f"<t:{unix}:t> | **{name_display}**{genre_str}")
                else:
                    time_display = current_pointer.strftime("%H:%M")
                    lines.append(f"{time_display} | {name_display}{genre_str}")

            current_pointer += datetime.timedelta(minutes=duration)

        if self.include_od.get():
            lines.append("\n### OPEN DECKS" if out_format == "discord" else "\nOPEN DECKS")
            try:
                od_count = int(self.od_count.get())
                od_dur = int(self.od_duration.get())
            except ValueError:
                od_count = od_dur = 0

            for i in range(od_count):
                if out_format == "discord":
                    unix = int(current_pointer.timestamp())
                    time_display = f"<t:{unix}:t>"
                else:
                    time_display = current_pointer.strftime("%H:%M")
                lines.append(f"{time_display} | Slot {i + 1}: [Available]")
                current_pointer += datetime.timedelta(minutes=od_dur)

        self.output_text.configure(state="normal")
        self.output_text.delete("1.0", "end")
        self.output_text.insert("1.0", "\n".join(lines))
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
