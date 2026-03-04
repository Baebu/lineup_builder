import re
import datetime
import customtkinter as ctk


class ImportMixin:
    """Parses pasted Discord / plain-text event text and loads it into the editor."""

    # ── Import dialog ─────────────────────────────────────────────────────

    def open_import_dialog(self):
        """Open a modal with a paste area and Import button."""
        popup = ctk.CTkToplevel(self)
        popup.title("Import Event")
        popup.geometry("540x520")
        popup.resizable(True, True)
        popup.configure(fg_color="#0F172A")
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
            font=("Arial", 11, "bold"), text_color="#818CF8",
        ).pack(side="left")

        # Hint
        ctk.CTkLabel(
            content,
            text="Paste a Discord or plain-text formatted event below.\n"
                 "Supports: titles, timestamps, genres, lineup slots, and Open Decks.",
            font=("Arial", 10), text_color="#475569", justify="left",
        ).grid(row=1, column=0, sticky="w", pady=(0, 6))

        # Paste area
        text_box = ctk.CTkTextbox(
            content, fg_color="#1E293B", text_color="#CBD5E1",
            font=("Consolas", 12), border_width=1, border_color="#334155",
            wrap="word",
        )
        text_box.grid(row=2, column=0, sticky="nsew", pady=(0, 8))

        # Status / preview label
        status_lbl = ctk.CTkLabel(
            content, text="", font=("Arial", 10), text_color="#94A3B8",
        )
        status_lbl.grid(row=3, column=0, sticky="w", pady=(0, 6))

        # Buttons
        btn_row = ctk.CTkFrame(content, fg_color="transparent")
        btn_row.grid(row=4, column=0, sticky="e")

        def _preview():
            raw = text_box.get("1.0", "end-1c").strip()
            if not raw:
                status_lbl.configure(text="Paste something first.", text_color="#EF4444")
                return
            parsed = self._parse_event_text(raw)
            if not parsed:
                status_lbl.configure(text="Could not recognise any event data.", text_color="#EF4444")
                return
            n_slots = len(parsed.get("slots", []))
            title = parsed.get("title") or "Untitled"
            genres = ", ".join(parsed.get("genres", [])) or "—"
            od = f" + {parsed['od_count']} OD" if parsed.get("include_od") else ""
            status_lbl.configure(
                text=f'"{title}" — {n_slots} slot(s){od} — Genres: {genres}',
                text_color="#34D399",
            )

        def _import():
            raw = text_box.get("1.0", "end-1c").strip()
            if not raw:
                status_lbl.configure(text="Paste something first.", text_color="#EF4444")
                return
            parsed = self._parse_event_text(raw)
            if not parsed:
                status_lbl.configure(text="Could not recognise any event data.", text_color="#EF4444")
                return
            self._apply_parsed_event(parsed)
            popup.destroy()

        ctk.CTkButton(
            btn_row, text="Cancel", width=80, height=32,
            fg_color="#334155", hover_color="#475569",
            font=("Arial", 11, "bold"), command=popup.destroy,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            btn_row, text="Preview", width=80, height=32,
            fg_color="#334155", hover_color="#475569",
            font=("Arial", 11, "bold"), text_color="#818CF8",
            command=_preview,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            btn_row, text="Import", width=90, height=32,
            fg_color="#4F46E5", hover_color="#4338CA",
            font=("Arial", 11, "bold"), command=_import,
        ).pack(side="left")

        popup.bind("<Escape>", lambda e: popup.destroy())
        text_box.focus_set()

    # ── Parser ────────────────────────────────────────────────────────────

    def _parse_event_text(self, text: str) -> dict | None:
        """Auto-detect Discord or plain-text format and extract event details."""
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

        slot_times: list[int] = []     # unix seconds for lineup slots
        od_times: list[int] = []       # unix seconds for OD slots
        in_lineup = False
        in_od = False

        for line in lines:
            s = line.strip()
            if not s:
                continue

            # ── Title: "# Title" or "# Title VOL.3" ──────────────────
            m = re.match(r'^#{1}\s+(.+?)(?:\s+VOL\.(\d+))?\s*$', s)
            if m and not parsed["title"] and '<t:' not in s:
                parsed["title"] = m.group(1).strip()
                if m.group(2):
                    parsed["vol"] = m.group(2)
                continue

            # ── Discord timestamp: "# <t:UNIX:F> ..." ────────────────
            m = re.search(r'<t:(\d+):F>', s)
            if m and not parsed["timestamp"]:
                dt = datetime.datetime.fromtimestamp(int(m.group(1)))
                parsed["timestamp"] = dt.strftime("%Y-%m-%d %H:%M")
                continue

            # ── Plain-text timestamp: "YYYY-MM-DD @ HH:MM (TZ)" ──────
            m = re.match(r'^(\d{4}-\d{2}-\d{2})\s*@\s*(\d{2}:\d{2})', s)
            if m and not parsed["timestamp"]:
                parsed["timestamp"] = f"{m.group(1)} {m.group(2)}"
                continue

            # ── Genres: "## Genre1 // Genre2" or "Genre1 // Genre2" ───
            if '//' in s and not in_lineup and not in_od:
                m = re.match(r'^(?:#{1,3}\s+)?(.+?//.*?)$', s)
                if m and not parsed["genres"]:
                    parsed["genres"] = [g.strip() for g in m.group(1).split("//") if g.strip()]
                    continue

            # ── Section markers ───────────────────────────────────────
            if re.match(r'^(?:#{1,3}\s+)?LINEUP\s*$', s, re.IGNORECASE):
                in_lineup = True
                in_od = False
                continue
            if re.match(r'^(?:#{1,3}\s+)?OPEN\s*DECKS\s*$', s, re.IGNORECASE):
                in_od = True
                in_lineup = False
                continue

            # ── Bullet / names-only: "• Name" or "- Name" ────────────
            m = re.match(r'^[•\-\*]\s+(.+)$', s)
            if m and not in_od:
                parsed["slots"].append({"name": m.group(1).strip(), "genre": "", "duration": "60"})
                parsed["names_only"] = True
                continue

            # ── Discord slot: "<t:UNIX:t> | **Name** (Genre)" ────────
            m = re.match(r'<t:(\d+):t>\s*\|\s*\*\*(.+?)\*\*(?:\s*\((.+?)\))?\s*$', s)
            if m:
                unix = int(m.group(1))
                name = m.group(2).strip()
                genre = (m.group(3) or "").strip()
                if in_od:
                    od_times.append(unix)
                else:
                    slot_times.append(unix)
                    parsed["slots"].append({"name": name, "genre": genre, "duration": "60"})
                continue

            # ── Discord OD slot: "<t:UNIX:t> | Slot N: [Available]" ──
            m = re.match(r'<t:(\d+):t>\s*\|\s*Slot\s+\d+\s*:\s*\[Available\]', s)
            if m:
                od_times.append(int(m.group(1)))
                in_od = True
                continue

            # ── Plain slot: "HH:MM | Name (Genre)" ───────────────────
            m = re.match(r'(\d{1,2}:\d{2})\s*\|\s*(.+?)(?:\s*\((.+?)\))?\s*$', s)
            if m:
                time_str = m.group(1)
                name = m.group(2).strip()
                genre = (m.group(3) or "").strip()
                unix = self._time_str_to_unix(time_str, parsed.get("timestamp", ""))
                if re.match(r'Slot\s+\d+\s*:\s*\[Available\]', name) or in_od:
                    if unix is not None:
                        od_times.append(unix)
                    in_od = True
                else:
                    if unix is not None:
                        slot_times.append(unix)
                    parsed["slots"].append({"name": name, "genre": genre, "duration": "60"})
                continue

            # ── Fallback: treat first non-matched line as title ───────
            if not parsed["title"] and not in_lineup and not in_od:
                if not any(ch in s for ch in ['|', '<t:', '•', '#']):
                    m = re.match(r'^(.+?)(?:\s+VOL\.(\d+))?\s*$', s)
                    if m:
                        parsed["title"] = m.group(1).strip()
                        if m.group(2):
                            parsed["vol"] = m.group(2)

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
        self.update_output()
