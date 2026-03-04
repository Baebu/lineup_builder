import copy
import datetime
import customtkinter as ctk
from tkinter import messagebox


class EventsMixin:
    """Manages saved event lineups: save, load, delete, duplicate, and UI refresh."""

    def save_event_lineup(self):
        title = self.event_title_var.get().strip()
        vol = self.event_vol_var.get().strip()
        if not title:
            messagebox.showwarning("Missing Title", "Please set an Event Title before saving the lineup.")
            return

        full_title = f"{title} VOL.{vol}" if vol.isdigit() else title

        event_data = {
            "title": title,
            "vol": vol,
            "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "timestamp": self.event_timestamp.get(),
            "master_duration": self.master_duration.get(),
            "genres": self.active_genres.copy(),
            "names_only": self.names_only.get(),
            "include_od": self.include_od.get(),
            "od_duration": self.od_duration.get(),
            "od_count": self.od_count.get(),
            "slots": []
        }

        for slot in self.slots:
            event_data["slots"].append({
                "name": slot.name_var.get().strip(),
                "genre": slot.genre_var.get().strip(),
                "duration": slot.duration_var.get()
            })

        existing_idx = None
        for i, ev in enumerate(self.saved_events):
            saved_full_title = (
                f"{ev['title']} VOL.{ev['vol']}" if ev.get('vol', '').isdigit() else ev['title']
            )
            if saved_full_title == full_title:
                existing_idx = i
                break

        if existing_idx is not None:
            if messagebox.askyesno("Update Event", f"'{full_title}' already exists. Overwrite?"):
                self.saved_events[existing_idx] = event_data
            else:
                return
        else:
            self.saved_events.append(event_data)

        self.saved_events.sort(key=lambda e: e.get('created_at', ''), reverse=True)
        self._current_event_key = (title, vol)
        self._save_events()
        self.refresh_saved_events_ui()
        messagebox.showinfo("Success", f"Event '{full_title}' saved successfully!")

    def new_event(self):
        """Reset all event fields and slots to a blank state."""
        if any(s.name_var.get().strip() or s.genre_var.get().strip() for s in self.slots):
            if not messagebox.askyesno("New Event", "Clear the current lineup and start fresh?"):
                return

        self._current_event_key = None

        import datetime as _dt
        now = _dt.datetime.now()
        self.event_title_var.set("")
        self.event_vol_var.set("")
        self.event_timestamp.set(now.strftime("%Y-%m-%d") + " 20:00")
        self.master_duration.set("60")
        self.active_genres = []
        self.refresh_genre_tags()
        self.names_only.set(False)
        self.include_od.set(False)
        self.od_count.set("4")
        self.od_duration.set("30")
        self.toggle_od()

        for slot in self.slots:
            slot.destroy()
        self.slots.clear()
        self.add_slot()

        self.left_tabs.set("Event")
        if hasattr(self, "_event_saved_panel") and self._event_saved_panel.winfo_ismapped():
            self._toggle_event_panel()
        self.update_output()

    def load_event_lineup(self, event_data):
        self.event_title_var.set(event_data.get("title", ""))
        self.event_vol_var.set(event_data.get("vol", ""))
        self.event_timestamp.set(event_data.get("timestamp", ""))
        self.master_duration.set(event_data.get("master_duration", "60"))

        self.active_genres = event_data.get("genres", []).copy()
        self.refresh_genre_tags()

        self.names_only.set(event_data.get("names_only", False))
        self.include_od.set(event_data.get("include_od", False))
        self.od_duration.set(event_data.get("od_duration", "30"))
        self.od_count.set(event_data.get("od_count", "4"))
        self.toggle_od()

        for slot in self.slots:
            slot.destroy()
        self.slots.clear()

        for slot_data in event_data.get("slots", []):
            self.add_slot(
                slot_data.get("name", ""),
                slot_data.get("genre", ""),
                int(slot_data.get("duration", 60))
            )

        self.left_tabs.set("Event")
        # Ensure config panel is visible (not the saved events panel)
        if hasattr(self, "_event_saved_panel") and self._event_saved_panel.winfo_ismapped():
            self._toggle_event_panel()
        self.update_output()
        self._current_event_key = (event_data.get("title", ""), event_data.get("vol", ""))

    def _auto_event_save(self):
        """Silently save the current event; bump vol if title collides with a different event."""
        title = self.event_title_var.get().strip()
        if not title:
            return
        vol = self.event_vol_var.get().strip()

        def _full(t, v):
            return f"{t} VOL.{v}" if str(v).isdigit() else t

        full_title = _full(title, vol)
        my_key_full = _full(*self._current_event_key) if self._current_event_key else None

        # Detect collision with a DIFFERENT saved event
        clash = any(
            _full(ev["title"], ev.get("vol", "")) == full_title
            for ev in self.saved_events
            if _full(ev["title"], ev.get("vol", "")) != my_key_full
        )
        if clash:
            all_vols = [
                int(ev["vol"]) for ev in self.saved_events
                if ev["title"] == title and str(ev.get("vol", "")).isdigit()
            ]
            next_vol = str(max(all_vols) + 1) if all_vols else "2"
            self.event_vol_var.set(next_vol)
            vol = next_vol
            full_title = _full(title, vol)

        event_data = {
            "title": title,
            "vol": vol,
            "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "timestamp": self.event_timestamp.get(),
            "master_duration": self.master_duration.get(),
            "genres": self.active_genres.copy(),
            "names_only": self.names_only.get(),
            "include_od": self.include_od.get(),
            "od_duration": self.od_duration.get(),
            "od_count": self.od_count.get(),
            "slots": [
                {"name": s.name_var.get().strip(), "genre": s.genre_var.get().strip(), "duration": s.duration_var.get()}
                for s in self.slots
            ]
        }

        existing_idx = next(
            (i for i, ev in enumerate(self.saved_events)
             if _full(ev["title"], ev.get("vol", "")) == full_title),
            None
        )
        if existing_idx is not None:
            self.saved_events[existing_idx] = event_data
        else:
            self.saved_events.append(event_data)

        self._current_event_key = (title, vol)
        self.saved_events.sort(key=lambda e: e.get("created_at", ""), reverse=True)
        self._save_events()
        # Only rebuild the saved-events list when it's actually visible
        if hasattr(self, "_event_saved_panel") and self._event_saved_panel.winfo_ismapped():
            self.refresh_saved_events_ui()

    def delete_event_lineup(self, event_data):
        full_title = (
            f"{event_data['title']} VOL.{event_data.get('vol', '')}"
            if event_data.get('vol', '').isdigit()
            else event_data['title']
        )
        if messagebox.askyesno("Confirm Delete", f"Delete saved event '{full_title}'?"):
            self.saved_events.remove(event_data)
            self._save_events()
            self.refresh_saved_events_ui()

    def duplicate_event_lineup(self, event_data):
        dupe = copy.deepcopy(event_data)
        try:
            dupe["vol"] = str(int(dupe.get("vol", "0")) + 1)
        except (ValueError, TypeError):
            dupe["vol"] = ""
        dupe["created_at"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.saved_events.append(dupe)
        self.saved_events.sort(key=lambda e: e.get("created_at", ""), reverse=True)
        self._save_events()
        self.refresh_saved_events_ui()

    def refresh_saved_events_ui(self):
        for widget in self.saved_events_scroll.winfo_children():
            widget.destroy()

        if not self.saved_events:
            ctk.CTkLabel(
                self.saved_events_scroll, text="No saved events yet.", text_color="#94A3B8"
            ).pack(pady=20)
            return

        for ev in self.saved_events:
            frame = ctk.CTkFrame(
                self.saved_events_scroll, fg_color="#0F172A",
                border_width=1, border_color="#334155", corner_radius=8
            )
            frame.pack(fill="x", pady=5)
            frame.grid_columnconfigure(0, weight=1)

            full_title = (
                f"{ev['title']} VOL.{ev.get('vol', '')}"
                if ev.get('vol', '').isdigit()
                else ev['title']
            )

            info_frame = ctk.CTkFrame(frame, fg_color="transparent")
            info_frame.grid(row=0, column=0, padx=(10, 4), pady=(8, 0), sticky="ew")

            ctk.CTkLabel(
                info_frame, text=full_title, font=("Arial", 13, "bold"),
                text_color="#CBD5E1", anchor="w"
            ).pack(anchor="w")

            slots_count = len(ev.get("slots", []))
            timestamp = ev.get("timestamp", "")
            saved_at = ev.get("created_at", "")[:16]
            ctk.CTkLabel(
                info_frame, text=f"{timestamp}  •  {slots_count} slots",
                font=("Arial", 10), text_color="#94A3B8", anchor="w"
            ).pack(anchor="w")
            if saved_at:
                ctk.CTkLabel(
                    info_frame, text=f"saved {saved_at}",
                    font=("Arial", 9), text_color="#475569", anchor="w"
                ).pack(anchor="w")

            btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
            btn_frame.grid(row=0, column=1, padx=(0, 8), pady=8, sticky="e")

            ctk.CTkButton(
                btn_frame, text="Load", width=54, height=28,
                fg_color="#3730A3", hover_color="#4338CA", font=("Arial", 10, "bold"),
                command=lambda e=ev: self.load_event_lineup(e)
            ).pack(side="left", padx=(0, 2))

            ctk.CTkButton(
                btn_frame, text="", image=self.icon_copy, width=28, height=28,
                fg_color="#334155", hover_color="#475569",
                command=lambda e=ev: self.duplicate_event_lineup(e)
            ).pack(side="left", padx=(0, 2))

            ctk.CTkButton(
                btn_frame, text="", image=self.icon_trash, width=28, height=28,
                fg_color="#7F1D1D", hover_color="#991B1B",
                command=lambda e=ev: self.delete_event_lineup(e)
            ).pack(side="left")
