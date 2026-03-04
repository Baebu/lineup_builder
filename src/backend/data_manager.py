import datetime
import json
import os
import yaml


class DataMixin:
    """Handles all YAML/JSON persistence and window-state save/restore."""

    # ── Data loading ──────────────────────────────────────────────────────

    def load_data(self):
        # ── Library: titles, DJs, genres ─────────────────────────────────
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
                # Migrate old goggles/link fields → stream
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

        # ── Events ───────────────────────────────────────────────────────
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

    # ── Persistence ───────────────────────────────────────────────────────

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

    # ── Auto-save (crash recovery) ────────────────────────────────────────

    def _save_auto_state(self):
        """Persist the current working session to auto_save.json for crash recovery."""
        state = {
            "title": self.event_title_var.get(),
            "vol": self.event_vol_var.get(),
            "timestamp": self.event_timestamp.get(),
            "master_duration": self.master_duration.get(),
            "genres": list(self.active_genres),
            "names_only": self.names_only.get(),
            "include_od": self.include_od.get(),
            "od_duration": self.od_duration.get(),
            "od_count": self.od_count.get(),
            "slots": [
                {
                    "name": s.name_var.get().strip(),
                    "genre": s.genre_var.get().strip(),
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
        """On startup, detect an unclean exit and offer to restore the session."""
        if not os.path.exists(self.AUTO_SAVE_FILE):
            return
        try:
            with open(self.AUTO_SAVE_FILE, "r") as f:
                state = json.load(f)
        except Exception:
            return
        # Clean-exit flag written by _on_close — no restore needed
        if state.get("clean_close"):
            return
        # Skip if essentially empty (no title and all slots are blank)
        title = state.get("title", "").strip()
        slots = state.get("slots", [])
        has_content = title or any(s.get("name") or s.get("genre") for s in slots)
        if not has_content:
            return
        from tkinter import messagebox
        if messagebox.askyesno(
            "Restore Unsaved Session",
            f"An unsaved lineup was found{(' \u2014 ' + title) if title else ''}.\n"
            "Restore it?"
        ):
            self.load_event_lineup(state)

    # ── Window state ──────────────────────────────────────────────────────

    def _restore_window_state(self):
        try:
            if os.path.exists(self.WINDOW_STATE_FILE):
                with open(self.WINDOW_STATE_FILE, "r") as f:
                    state = json.load(f)
                geo = state.get("geometry")
                if geo:
                    self.geometry(geo)
                if state.get("maximized"):
                    self.after(50, lambda: self.state("zoomed"))
        except Exception:
            pass

    def _on_close(self):
        try:
            maximized = self.state() == "zoomed"
            if not maximized:
                geo = self.geometry()
            else:
                geo = (
                    f"{self.winfo_width()}x{self.winfo_height()}"
                    f"+{self.winfo_x()}+{self.winfo_y()}"
                )
            with open(self.WINDOW_STATE_FILE, "w") as f:
                json.dump({"geometry": geo, "maximized": maximized}, f)
        except Exception:
            pass
        # Mark clean exit so auto-save won't prompt on next launch
        try:
            with open(self.AUTO_SAVE_FILE, "w") as f:
                json.dump({"clean_close": True}, f)
        except Exception:
            pass
        self.destroy()
