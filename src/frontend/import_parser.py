import re
import datetime
import customtkinter as ctk
from . import theme as T


class ImportMixin:
    """Parses pasted Discord / plain-text event text and loads it into the editor."""

    # ── Import dialog ─────────────────────────────────────────────────────

    def open_import_dialog(self):
        """Open a modal with a paste area and Import button."""
        popup = ctk.CTkToplevel(self)
        popup.title("Import Event")
        popup.geometry("540x520")
        popup.resizable(True, True)
        popup.configure(fg_color=T.CARD_BG)
        popup.grab_set()
        popup.focus_force()

        self.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() - 540) // 2
        y = self.winfo_y() + (self.winfo_height() - 520) // 2
        popup.geometry(f"540x520+{x}+{y}")

        content = ctk.CTkFrame(popup, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=20, pady=16)
        content.grid_columnconfigure(0, weight=1)
        content.grid_rowconfigure(2, weight=1)

        # Header
        header = ctk.CTkFrame(content, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 2))
        ctk.CTkLabel(
            header, text="IMPORT EVENT",
            font=T.FONT_BODY_BOLD, text_color=T.ACCENT,
        ).pack(side="left")

        # Hint
        ctk.CTkLabel(
            content,
            text="Paste a Discord or plain-text formatted event below.\n"
                 "Supports: titles, timestamps, genres, lineup slots, and Open Decks.",
            font=T.FONT_SMALL, text_color=T.TEXT_MUTED, justify="left",
        ).grid(row=1, column=0, sticky="w", pady=(0, 6))

        # Paste area
        text_box = ctk.CTkTextbox(
            content, fg_color=T.PANEL_BG, text_color=T.TEXT_PRIMARY,
            font=("Consolas", 12), border_width=T.BORDER_W, border_color=T.BORDER,
            wrap="word",
        )
        text_box.grid(row=2, column=0, sticky="nsew", pady=(0, 8))

        # Status / preview label
        status_lbl = ctk.CTkLabel(
            content, text="", font=T.FONT_SMALL, text_color=T.TEXT_SECONDARY,
        )
        status_lbl.grid(row=3, column=0, sticky="w", pady=(0, 6))

        # Buttons
        btn_row = ctk.CTkFrame(content, fg_color="transparent")
        btn_row.grid(row=4, column=0, sticky="e")

        def _preview():
            raw = text_box.get("1.0", "end-1c").strip()
            if not raw:
                status_lbl.configure(text="Paste something first.", text_color=T.ERROR)
                return
            parsed = self._parse_event_text(raw)
            if not parsed:
                status_lbl.configure(text="Could not recognise any event data.", text_color=T.ERROR)
                return
            n_slots = len(parsed.get("slots", []))
            title = parsed.get("title") or "Untitled"
            genres = ", ".join(parsed.get("genres", [])) or "—"
            od = f" + {parsed['od_count']} OD" if parsed.get("include_od") else ""
            status_lbl.configure(
                text=f'"{title}" — {n_slots} slot(s){od} — Genres: {genres}',
                text_color=T.IMPORT_SUCCESS,
            )

        def _import():
            raw = text_box.get("1.0", "end-1c").strip()
            if not raw:
                status_lbl.configure(text="Paste something first.", text_color=T.ERROR)
                return
            parsed = self._parse_event_text(raw)
            if not parsed:
                status_lbl.configure(text="Could not recognise any event data.", text_color=T.ERROR)
                return
            self._apply_parsed_event(parsed)
            popup.destroy()

        ctk.CTkButton(
            btn_row, text="Cancel", width=80, height=T.WIDGET_H_SM,
            **T.BTN_SECONDARY,
            font=T.FONT_BODY_BOLD, command=popup.destroy,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            btn_row, text="Preview", width=80, height=T.WIDGET_H_SM,
            **T.BTN_SECONDARY,
            font=T.FONT_BODY_BOLD, text_color=T.ACCENT,
            command=_preview,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            btn_row, text="Import", width=90, height=T.WIDGET_H_SM,
            **T.BTN_PRIMARY,
            font=T.FONT_BODY_BOLD, command=_import,
        ).pack(side="left")

        popup.bind("<Escape>", lambda e: popup.destroy())
        text_box.focus_set()

    # ── Parser ────────────────────────────────────────────────────────────

    def _parse_event_text(self, text: str) -> dict | None:
        """Parse event text from any common format.

        Handles Discord markdown (bold names, Unix timestamps) and plain-text
        variations.  Flexible on:
          • dividers between time and name: | – — - or plain whitespace
          • name bold markup (**Name**) being present or absent
          • genre in (parens), [brackets], or as a trailing "- Genre" suffix
          • VOL written as VOL.3 / Vol 3 / Volume 3 / #3
          • section headers with or without # prefixes
        """
        lines = text.strip().splitlines()
        if not lines:
            return None

        parsed = {
            "title": "",
            "vol": "",
            "timestamp": "",
            "genres": [],
            "slots": [],
            "names_only": False,
            "include_od": False,
            "od_count": "0",
            "od_duration": "30",
        }

        slot_times: list[int] = []
        od_times: list[int] = []
        in_lineup = False
        in_od = False

        for line in lines:
            s = line.strip()
            if not s:
                continue

            # Strip bold / italic markdown for cleaner matching while
            # preserving the original line (s) for edge-case checks.
            clean = re.sub(r'\*\*(.+?)\*\*', r'\1', s)
            clean = re.sub(r'\*([^*]+?)\*', r'\1', clean)
            clean = re.sub(r'__(.+?)__', r'\1', clean)

            # ── Title: "#+ Title" / "## Title Vol 3" / "**Title**" ───
            m = re.match(r'^#{1,3}\s+(.+?)\s*$', clean)
            if m and not parsed["title"] and '<t:' not in s and '//' not in m.group(1):
                candidate = m.group(1).strip()
                vol_m = re.search(
                    r'\s+(?:VOL\.?\s*|Vol\.?\s*|Volume\s+|#)(\d+)\s*$',
                    candidate, re.IGNORECASE,
                )
                if vol_m:
                    parsed["vol"] = vol_m.group(1)
                    candidate = candidate[:vol_m.start()].strip()
                parsed["title"] = candidate
                continue

            # ── Discord event timestamp: "<t:UNIX:F>" ─────────────────
            m = re.search(r'<t:(\d+):F>', s)
            if m and not parsed["timestamp"]:
                dt = datetime.datetime.fromtimestamp(int(m.group(1)))
                parsed["timestamp"] = dt.strftime("%Y-%m-%d %H:%M")
                continue

            # ── Plain-text timestamp: "YYYY-MM-DD @ HH:MM" ───────────
            m = re.match(r'^(\d{4}-\d{2}-\d{2})\s*@\s*(\d{2}:\d{2})', s)
            if m and not parsed["timestamp"]:
                parsed["timestamp"] = f"{m.group(1)} {m.group(2)}"
                continue

            # ── Genres: any line with "//" that isn't a slot ──────────
            if '//' in s and not in_lineup and not in_od:
                genre_text = re.sub(r'^#{1,3}\s+', '', clean).strip()
                if genre_text and not parsed["genres"]:
                    parsed["genres"] = [g.strip() for g in genre_text.split("//") if g.strip()]
                    continue

            # ── Section markers ───────────────────────────────────────
            if re.match(r'^(?:#{1,3}\s+)?LINEUP\s*$', clean, re.IGNORECASE):
                in_lineup = True
                in_od = False
                continue
            if re.match(r'^(?:#{1,3}\s+)?OPEN\s*DECKS?\s*$', clean, re.IGNORECASE):
                in_od = True
                in_lineup = False
                continue

            # ── Bullet / names-only: "• Name" / "- Name" / "* Name" ──
            m = re.match(r'^[•\-\*]\s+(.+)$', s)
            if m and not in_od:
                name = re.sub(r'\*\*(.+?)\*\*', r'\1', m.group(1)).strip()
                parsed["slots"].append({"name": name, "genre": "", "duration": "60"})
                parsed["names_only"] = True
                continue

            # ── Discord slot: "<t:UNIX:t> [divider] Name [(Genre)]" ───
            # Divider may be |, –, —, - or absent; bold markers already
            # stripped from `clean`.
            discord_m = re.match(
                r'^<t:(\d+):t>\s*(?:[|–—\-]\s*)?(.+)$', clean,
            )
            if discord_m:
                unix = int(discord_m.group(1))
                rest = discord_m.group(2).strip()
                name, genre = self._extract_name_genre(rest)
                is_placeholder = (
                    re.match(r'Slot\s+\d+\s*:', name, re.IGNORECASE)
                    or '[Available]' in name
                )
                if is_placeholder:
                    od_times.append(unix)
                    in_od = True
                elif in_od:
                    od_times.append(unix)
                else:
                    slot_times.append(unix)
                    parsed["slots"].append({"name": name, "genre": genre, "duration": "60"})
                continue

            # ── Plain time slot: "HH:MM [divider] Name [(Genre)]" ─────
            # Divider may be |, –, —, - or plain whitespace.
            time_m = re.match(
                r'^(\d{1,2}:\d{2})(?!\d)\s*(?:[|–—\-]\s*|\s+)(.+)$', clean,
            )
            if time_m:
                time_str = time_m.group(1)
                rest = time_m.group(2).strip()
                name, genre = self._extract_name_genre(rest)
                unix = self._time_str_to_unix(time_str, parsed.get("timestamp", ""))
                is_placeholder = (
                    re.match(r'Slot\s+\d+\s*:', name, re.IGNORECASE)
                    or '[Available]' in name
                )
                if is_placeholder or in_od:
                    if unix is not None:
                        od_times.append(unix)
                    in_od = True
                else:
                    if unix is not None:
                        slot_times.append(unix)
                    parsed["slots"].append({"name": name, "genre": genre, "duration": "60"})
                continue

            # ── Fallback: first unrecognised line → title candidate ────
            if not parsed["title"] and not in_lineup and not in_od:
                if not any(ch in s for ch in ['|', '<t:', '•', '# ', '//']):
                    # Standalone **bold** line
                    bold_m = re.match(r'^\*\*(.+?)\*\*\s*$', s)
                    candidate = bold_m.group(1).strip() if bold_m else clean.strip()
                    vol_m = re.search(
                        r'\s+(?:VOL\.?\s*|Vol\.?\s*|Volume\s+|#)(\d+)\s*$',
                        candidate, re.IGNORECASE,
                    )
                    if vol_m:
                        parsed["vol"] = vol_m.group(1)
                        candidate = candidate[:vol_m.start()].strip()
                    if candidate:
                        parsed["title"] = candidate

        # ── Compute durations from consecutive timestamps ─────────────
        self._compute_slot_durations(parsed["slots"], slot_times, od_times)

        # ── Open Decks ────────────────────────────────────────────────
        if od_times:
            parsed["include_od"] = True
            parsed["od_count"] = str(len(od_times))
            if len(od_times) >= 2:
                diff = (od_times[1] - od_times[0]) // 60
                if 0 < diff <= 480:
                    parsed["od_duration"] = str(diff)

        return parsed if (parsed["title"] or parsed["slots"]) else None

    # ── Helpers ───────────────────────────────────────────────────────────

    @staticmethod
    def _extract_name_genre(rest: str) -> tuple[str, str]:
        """Split the right-hand side of a slot line into (name, genre).

        Handles:
          ``Name (Genre)``  – parens
          ``Name [Genre]``  – square brackets
          ``Name - Genre``  – trailing dash / en-dash separator
          ``Name``          – no genre
        """
        name = rest.strip()
        genre = ""

        # (Genre) or [Genre] at end
        m = re.search(r'\s*[\(\[]([^\)\]]+)[\)\]]\s*$', name)
        if m:
            genre = m.group(1).strip()
            name = name[: m.start()].strip()
            return name, genre

        # " - Genre" or " – Genre" trailing suffix
        m = re.search(r'\s+[-–]\s+(.+)$', name)
        if m:
            possible_name = name[: m.start()].strip()
            if possible_name:          # only split if name part is non-empty
                genre = m.group(1).strip()
                name = possible_name

        return name, genre

    @staticmethod
    def _time_str_to_unix(time_str: str, timestamp_ctx: str) -> int | None:
        """Convert 'HH:MM' to unix seconds using the event date for context."""
        try:
            h, m = time_str.split(":")
            if timestamp_ctx:
                date_part = timestamp_ctx.split(" ")[0]
                dt = datetime.datetime.strptime(f"{date_part} {time_str}", "%Y-%m-%d %H:%M")
            else:
                today = datetime.date.today()
                dt = datetime.datetime(today.year, today.month, today.day, int(h), int(m))
            return int(dt.timestamp())
        except (ValueError, IndexError):
            return None

    @staticmethod
    def _compute_slot_durations(slots: list, slot_times: list[int], od_times: list[int]):
        """Fill in duration for each slot from consecutive start-time deltas."""
        if not slot_times or len(slot_times) != len(slots):
            return

        # Handle midnight wrap-around for plain-text times
        for i in range(1, len(slot_times)):
            if slot_times[i] <= slot_times[i - 1]:
                slot_times[i] += 86400  # +24h
        if od_times:
            for i in range(len(od_times)):
                ref = slot_times[-1] if slot_times else 0
                if od_times[i] <= ref:
                    od_times[i] += 86400

        for i in range(len(slot_times)):
            if i + 1 < len(slot_times):
                diff = (slot_times[i + 1] - slot_times[i]) // 60
            elif od_times:
                diff = (od_times[0] - slot_times[i]) // 60
            else:
                diff = 0
            if 0 < diff <= 480:
                slots[i]["duration"] = str(diff)

    # ── Apply parsed data to editor ───────────────────────────────────────

    def _apply_parsed_event(self, parsed: dict):
        """Load parsed event data into the current editor state."""
        if parsed.get("title"):
            self.event_title_var.set(parsed["title"])
        if parsed.get("vol"):
            self.event_vol_var.set(parsed["vol"])
        if parsed.get("timestamp"):
            self.event_timestamp.set(parsed["timestamp"])

        if parsed.get("genres"):
            self.active_genres = parsed["genres"][:]
            for g in parsed["genres"]:
                if g.lower() not in [sg.lower() for sg in self.saved_genres]:
                    self.saved_genres.append(g)
            self._save_library()
            self.refresh_genre_tags()

        self.names_only.set(parsed.get("names_only", False))

        # Clear existing slots and rebuild
        for slot in self.slots:
            slot.destroy()
        self.slots.clear()

        for slot_data in parsed.get("slots", []):
            self.add_slot(
                slot_data.get("name", ""),
                slot_data.get("genre", ""),
                int(slot_data.get("duration", 60)),
            )

        # Save new DJs to roster (preserve existing entries that already have links)
        existing_names = {d.get("name", "").strip().lower() for d in self.saved_djs}
        added = False
        for slot_data in parsed.get("slots", []):
            name = slot_data.get("name", "").strip()
            # Skip open-decks placeholders like "Slot 1: [Available]"
            if not name or re.match(r'Slot\s+\d+', name, re.IGNORECASE):
                continue
            if name.lower() not in existing_names:
                self.saved_djs.append({"name": name, "stream": "", "exact_link": False})
                existing_names.add(name.lower())
                added = True
        if added:
            self._save_library()
            self.after(0, self.refresh_dj_roster_ui)
            self.after(0, self._refresh_slot_combos)

        # Open Decks
        if parsed.get("include_od"):
            self.include_od.set(True)
            self.od_count.set(parsed.get("od_count", "4"))
            self.od_duration.set(parsed.get("od_duration", "30"))
        else:
            self.include_od.set(False)
        self.toggle_od()

        self.left_tabs.set("Event")
        self.right_tabs.set("Lineup")
        self.update_output()
