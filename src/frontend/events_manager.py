import copy
import datetime

import dearpygui.dearpygui as dpg

from . import theme as T
from .fonts import Icon


class EventsMixin:
    """Manages saved event lineups: save, load, delete, duplicate, and UI refresh."""

    def save_event_lineup(self):
        title = self.event_title_var.get().strip()
        vol = self.event_vol_var.get().strip()
        if not title:
            _warn_win = "save_warn_win"
            if not dpg.does_item_exist(_warn_win):
                with dpg.window(tag=_warn_win, label="Warning", modal=True,
                                width=380, height=80, no_resize=True):
                    dpg.add_text("Please set an Event Title before saving the lineup.")
                    dpg.add_button(label=Icon.CHECK + " OK", callback=lambda s, a, wt=_warn_win: dpg.delete_item(wt))
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

        def _do_save(_wt=None):
            if existing_idx is not None:
                self.saved_events[existing_idx] = event_data
            else:
                self.saved_events.append(event_data)
            self.saved_events.sort(key=lambda e: e.get('created_at', ''), reverse=True)
            self._current_event_key = (title, vol)
            self._save_events()
            self.refresh_saved_events_ui()
            if _wt and dpg.does_item_exist(_wt):
                dpg.delete_item(_wt)

        if existing_idx is not None:
            wt = "overwrite_confirm_win"
            if dpg.does_item_exist(wt):
                dpg.delete_item(wt)
            with dpg.window(tag=wt, label="Update Event", modal=True,
                            width=320, height=90, no_resize=True):
                dpg.add_text(f"'{full_title}' already exists. Overwrite?")
                with dpg.group(horizontal=True):
                    dpg.add_button(label=Icon.CHECK + " Yes", callback=lambda s, a, _wt=wt: _do_save(_wt))
                    dpg.add_button(label=Icon.CLOSE + " No",  callback=lambda s, a, _wt=wt: dpg.delete_item(_wt))
        else:
            _do_save()

    def new_event(self):
        """Reset all event fields and slots to a blank state."""
        has_content = any(s.name_var.get().strip() or s.genre_var.get().strip() for s in self.slots)

        def _do_new(_wt=None):
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
            if dpg.does_item_exist("left_tabs"):
                dpg.set_value("left_tabs", "Event")
            self.update_output()
            if _wt and dpg.does_item_exist(_wt):
                dpg.delete_item(_wt)

        if has_content:
            wt = "new_event_confirm"
            if dpg.does_item_exist(wt):
                dpg.delete_item(wt)
            with dpg.window(tag=wt, label="New Event", modal=True,
                            width=300, height=90, no_resize=True):
                dpg.add_text("Clear the current lineup and start fresh?")
                with dpg.group(horizontal=True):
                    dpg.add_button(label=Icon.CHECK + " Yes", callback=lambda s, a, _wt=wt: _do_new(_wt))
                    dpg.add_button(label=Icon.CLOSE + " No",  callback=lambda s, a, _wt=wt: dpg.delete_item(_wt))
        else:
            _do_new()

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

        if dpg.does_item_exist("left_tabs"):
            dpg.set_value("left_tabs", "Event")
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
        self.refresh_saved_events_ui()

    def delete_event_lineup(self, event_data):
        full_title = (
            f"{event_data['title']} VOL.{event_data.get('vol', '')}"
            if event_data.get('vol', '').isdigit()
            else event_data['title']
        )
        wt = "delete_event_confirm"
        if dpg.does_item_exist(wt):
            dpg.delete_item(wt)
        def _do_delete(_wt=wt, _ev=event_data):
            if _ev in self.saved_events:
                self.saved_events.remove(_ev)
            self._save_events()
            self.refresh_saved_events_ui()
            if dpg.does_item_exist(_wt):
                dpg.delete_item(_wt)
        with dpg.window(tag=wt, label="Confirm Delete", modal=True,
                        width=300, height=90, no_resize=True):
            dpg.add_text(f"Delete saved event '{full_title}'?")
            with dpg.group(horizontal=True):
                dpg.add_button(label=Icon.CHECK + " Yes", callback=lambda s, a: _do_delete())
                dpg.add_button(label=Icon.CLOSE + " No",  callback=lambda s, a, _wt=wt: dpg.delete_item(_wt))

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
        if not dpg.does_item_exist("saved_events_scroll"):
            return
        dpg.delete_item("saved_events_scroll", children_only=True)
        if not self.saved_events:
            dpg.add_text("No saved events yet.",
                         parent="saved_events_scroll", color=T.DPG_TEXT_SECONDARY)
            return
        for ev in self.saved_events:
            full_title = (
                f"{ev['title']} VOL.{ev.get('vol', '')}"
                if ev.get('vol', '').isdigit()
                else ev['title']
            )
            slots_count = len(ev.get("slots", []))
            timestamp = ev.get("timestamp", "")
            saved_at = ev.get("created_at", "")[:16]
            with dpg.group(parent="saved_events_scroll"):
                with dpg.group(horizontal=True):
                    dpg.add_text(full_title, color=T.DPG_TEXT_PRIMARY)
                    dpg.add_button(label=Icon.FOLDER, small=True,
                                   callback=lambda s, a, e=ev: self.load_event_lineup(e))
                    dpg.add_button(label=Icon.COPY, small=True,
                                   callback=lambda s, a, e=ev: self.duplicate_event_lineup(e))
                    dpg.add_button(label=Icon.DELETE, small=True,
                                   callback=lambda s, a, e=ev: self.delete_event_lineup(e))
                dpg.add_text(f"{timestamp}  \u2022  {slots_count} slots",
                             color=T.DPG_TEXT_SECONDARY)
                if saved_at:
                    dpg.add_text(f"saved {saved_at}", color=T.DPG_TEXT_MUTED)
                dpg.add_separator()
