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
        self.destroy()
