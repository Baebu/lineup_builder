import copy
import datetime

import dearpygui.dearpygui as dpg

from ..styling.fonts import BODY, LABEL, MUTED, Icon, bind_icon_font, styled_text
from ..ui.widgets import add_icon_button, popup_pos


class EventsMixin:
    """Manages saved event lineups: save, load, delete, duplicate, and UI refresh."""

    def save_event_lineup(self):
        title = self.event_title_var.get().strip()
        vol = self.event_vol_var.get().strip()
        if not title:
            _warn_win = "save_warn_win"
            if not dpg.does_item_exist(_warn_win):
                with dpg.window(tag=_warn_win, label="Warning", modal=True,
                                autosize=True, no_resize=True, no_scrollbar=True,
                                pos=popup_pos()):
                    dpg.add_text("Please set an Event Title before saving the lineup.")
                    dpg.add_button(label="OK", width=-1, user_data=_warn_win,
                                   callback=lambda s, a, u: dpg.delete_item(u))
            return

        full_title = f"{title} VOL.{vol}" if vol.isdigit() else title

        event_data = {
            "title": title,
            "vol": vol,
            "group_name": self.group_name_var.get().strip(),
            "collab": bool(self.collab_with_var.get().strip()),
            "collab_with": self.collab_with_var.get().strip(),
            "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "timestamp": self.event_timestamp.get(),
            "genres": self.active_genres.copy(),
            "names_only": self.names_only.get(),
            "social_links": dict(getattr(self, "social_links", {})),
            "discord_embed_image": getattr(self, "discord_embed_image", ""),
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
                            autosize=True, no_resize=True, no_scrollbar=True,
                            pos=popup_pos()):
                dpg.add_text(f"'{full_title}' already exists. Overwrite?")
                with dpg.group(horizontal=True):
                    yes_btn = dpg.add_button(label="Yes", width=140, user_data=wt,
                                   callback=lambda s, a, u: _do_save(u))
                    dpg.bind_item_theme(yes_btn, "primary_btn_theme")
                    dpg.add_button(label="No", width=140, user_data=wt,
                                   callback=lambda s, a, u: dpg.delete_item(u))
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
            self.group_name_var.set("")
            self.collab_var.set(False)
            self.collab_with_var.set("")
            self.event_timestamp.set(now.strftime("%Y-%m-%d") + " 20:00")
            self.active_genres = []
            self.refresh_genre_tags()
            self.names_only.set(False)
            self.social_links = {}
            self._sync_social_link_inputs()
            self.discord_embed_image = ""
            if dpg.does_item_exist("embed_image_browse_btn"):
                dpg.set_item_label("embed_image_browse_btn", "Select Image...")
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
            from ..ui.confirm_dialog import confirm
            confirm(
                "Clear the current lineup and start fresh?",
                on_confirm=_do_new,
                title="New Event",
                confirm_label="Clear",
                danger=True
            )
        else:
            _do_new()

    def _load_last_event(self):
        """Load the most recently saved event, or the current event if set."""
        if self._current_event_key:
            title, vol = self._current_event_key
            for ev in self.saved_events:
                ev_full = (
                    f"{ev['title']} VOL.{ev['vol']}"
                    if ev.get('vol', '').isdigit() else ev['title']
                )
                cur_full = (
                    f"{title} VOL.{vol}" if vol.isdigit() else title
                )
                if ev_full == cur_full:
                    self.load_event_lineup(ev)
                    return
        if self.saved_events:
            self.load_event_lineup(self.saved_events[0])

    def load_event_lineup(self, event_data):
        self.event_title_var.set(event_data.get("title", ""))
        self.event_vol_var.set(event_data.get("vol", ""))
        self.group_name_var.set(event_data.get("group_name", ""))
        self.collab_var.set(event_data.get("collab", False))
        self.collab_with_var.set(event_data.get("collab_with", ""))
        self.event_timestamp.set(event_data.get("timestamp", ""))

        self.active_genres = event_data.get("genres", []).copy()
        self.refresh_genre_tags()

        self.names_only.set(event_data.get("names_only", False))
        self.social_links = event_data.get("social_links", {}).copy()
        self._sync_social_link_inputs()

        img_path = event_data.get("discord_embed_image", "")
        self.discord_embed_image = img_path
        if dpg.does_item_exist("embed_image_browse_btn"):
            if img_path:
                import os
                dpg.set_item_label("embed_image_browse_btn", os.path.basename(img_path))
            else:
                dpg.set_item_label("embed_image_browse_btn", "Select Image...")

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
            self._save_auto_state()
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
            "group_name": self.group_name_var.get().strip(),
            "collab": bool(self.collab_with_var.get().strip()),
            "collab_with": self.collab_with_var.get().strip(),
            "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "timestamp": self.event_timestamp.get(),
            "genres": self.active_genres.copy(),
            "names_only": self.names_only.get(),
            "social_links": dict(getattr(self, "social_links", {})),
            "discord_embed_image": getattr(self, "discord_embed_image", ""),
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
                        autosize=True, no_resize=True, no_scrollbar=True,
                        pos=popup_pos()):
            dpg.add_text(f"Delete saved event '{full_title}'?")
            with dpg.group(horizontal=True):
                _yes = dpg.add_button(label="Yes", width=140, callback=lambda s, a, u=None: _do_delete())
                dpg.bind_item_theme(_yes, self._danger_btn_theme)
                dpg.add_button(label="No", width=140, user_data=wt,
                               callback=lambda s, a, u: dpg.delete_item(u))

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

    def _toggle_saved_events_drawer(self):
        """Toggle the saved events drawer open/closed inside the Event tab."""
        self._saved_events_drawer_open = not self._saved_events_drawer_open
        show = self._saved_events_drawer_open
        dpg.configure_item("saved_events_drawer", show=show)
        if show:
            self.refresh_saved_events_ui()

    def refresh_saved_events_ui(self):
        if not dpg.does_item_exist("saved_events_scroll"):
            return
        dpg.delete_item("saved_events_scroll", children_only=True)
        if not self.saved_events:
            styled_text("No saved events yet.",
                         LABEL, parent="saved_events_scroll")
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
                with dpg.table(header_row=False, borders_innerH=False, borders_innerV=False, borders_outerH=False, borders_outerV=False, pad_outerX=False):
                    dpg.add_table_column(width_stretch=True)
                    dpg.add_table_column(width_fixed=True)
                    with dpg.table_row():
                        with dpg.group():
                            styled_text(full_title, BODY)
                            styled_text(f"{timestamp}  |  {slots_count} slots", MUTED)
                        with dpg.group(horizontal=True):
                            add_icon_button(Icon.DOWNLOAD, width=28, height=20, user_data=ev, callback=lambda s, a, u: (self.load_event_lineup(u), self._toggle_saved_events_drawer() if self._saved_events_drawer_open else None))
                            add_icon_button(Icon.COPY, width=28, height=20, user_data=ev, callback=lambda s, a, u: self.duplicate_event_lineup(u))
                            add_icon_button(Icon.DELETE, width=28, height=20, is_danger=True, user_data=ev, callback=lambda s, a, u: self.delete_event_lineup(u))
                            dpg.add_spacer(width=10)
                dpg.add_separator()
