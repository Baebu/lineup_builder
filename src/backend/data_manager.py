"""
Module: data_manager.py
Purpose: File I/O for library, events, window state, and crash recovery.
"""
import json
import os

import yaml


class DataMixin:
    """Handles all YAML/JSON persistence and window-state save/restore."""

    def load_data(self):
        lib = {}
        for src in [self.LIBRARY_FILE, "lineup_data.yaml"]:
            if os.path.exists(src):
                try:
                    with open(src, "r") as f:
                        lib = yaml.safe_load(f) or {}
                    break
                except Exception as e:
                    print(f"Error loading {src}: {e}")

        self.saved_titles = lib.get("titles", [])

        raw_djs = lib.get("djs", []) or []
        self.saved_djs = []
        for _d in raw_djs:
            if not isinstance(_d, dict):
                name = _d or ""
                if not name:
                    continue
                self.saved_djs.append({"name": name, "stream": ""})
            elif "stream" not in _d:
                name = _d.get("name") or ""
                if not name:
                    continue
                self.saved_djs.append({
                    "name": name,
                    "stream": _d.get("goggles", "") or _d.get("link", "") or "",
                })
            else:
                name = _d.get("name") or ""
                if not name:
                    continue
                self.saved_djs.append(_d)

        self.saved_genres = lib.get("genres", [])

        evts = {}
        for src in [self.EVENTS_FILE, "lineup_data.yaml"]:
            if os.path.exists(src):
                try:
                    with open(src, "r") as f:
                        evts = yaml.safe_load(f) or {}
                    break
                except Exception as e:
                    print(f"Error loading {src}: {e}")

        raw_events = evts.get("events", [])
        self.saved_events = sorted(
            raw_events, key=lambda e: e.get("created_at", ""), reverse=True
        )

    def get_dj_names(self):
        return [d["name"] for d in self.saved_djs if d.get("name")]

    def save_data(self):
        self._save_library()
        self._save_events()

    def _save_library(self):
        data = {
            "titles": self.saved_titles,
            "djs": self.saved_djs,
            "genres": self.saved_genres,
        }
        try:
            with open(self.LIBRARY_FILE, "w") as f:
                yaml.dump(data, f, allow_unicode=True)
        except Exception as e:
            print(f"Error saving {self.LIBRARY_FILE}: {e}")

    def _save_events(self):
        try:
            with open(self.EVENTS_FILE, "w") as f:
                yaml.dump({"events": self.saved_events}, f, allow_unicode=True)
        except Exception as e:
            print(f"Error saving {self.EVENTS_FILE}: {e}")

    def _save_auto_state(self):
        state = {
            "title":           self.event_title_var.get(),
            "vol":             self.event_vol_var.get(),
            "timestamp":       self.event_timestamp.get(),
            "master_duration": self.master_duration.get(),
            "genres":          list(self.active_genres),
            "names_only":      self.names_only.get(),
            "slots": [
                {
                    "name":     s.name_var.get().strip(),
                    "genre":    s.genre_var.get().strip(),
                    "duration": s.duration_var.get(),
                }
                for s in self.slots
            ],
        }
        try:
            with open(self.AUTO_SAVE_FILE, "w") as f:
                json.dump(state, f)
        except Exception as e:
            print(f"Auto-save error: {e}")

    def _check_auto_save(self):
        """On startup, detect an unclean exit and offer to restore."""
        if not os.path.exists(self.AUTO_SAVE_FILE):
            return
        try:
            with open(self.AUTO_SAVE_FILE, "r") as f:
                state = json.load(f)
        except Exception:
            return
        if state.get("clean_close"):
            return
        title = state.get("title", "").strip()
        slots = state.get("slots", [])
        has_content = title or any(s.get("name") or s.get("genre") for s in slots)
        if not has_content:
            return
        # Show a DPG modal asking to restore
        msg = f"An unsaved lineup was found{(' — ' + title) if title else ''}.\nRestore it?"
        self._show_confirm(msg, lambda: self.load_event_lineup(state))

    def _restore_window_state(self):
        try:
            if os.path.exists(self.WINDOW_STATE_FILE):
                with open(self.WINDOW_STATE_FILE, "r") as f:
                    state = json.load(f)
                import dearpygui.dearpygui as dpg
                if "pos" in state:
                    dpg.set_viewport_pos(state["pos"])
                if "width" in state and "height" in state:
                    dpg.set_viewport_width(int(state["width"]))
                    dpg.set_viewport_height(int(state["height"]))
        except Exception:
            pass

    def _on_close(self):
        import dearpygui.dearpygui as dpg
        try:
            pos = dpg.get_viewport_pos()
            w   = dpg.get_viewport_width()
            h   = dpg.get_viewport_height()
            with open(self.WINDOW_STATE_FILE, "w") as f:
                json.dump({"pos": list(pos), "width": w, "height": h}, f)
        except Exception:
            pass
        try:
            with open(self.AUTO_SAVE_FILE, "w") as f:
                json.dump({"clean_close": True}, f)
        except Exception:
            pass
