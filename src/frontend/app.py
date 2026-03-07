"""
Module: app.py
Purpose: App class — composes all mixins, owns DPG lifecycle.
"""
import datetime
import os

import dearpygui.dearpygui as dpg

from src.backend.data_manager import DataMixin
from src.backend.debounce import DebounceMixin
from src.backend.discord_service import DiscordService
from src.backend.event_bus import EventBus
from src.backend.lineup_model import LineupModel
from src.backend.output_builder import OutputMixin

from .drag_drop import DragDropMixin
from .events_manager import EventsMixin
from .fonts import setup_fonts
from .genre_manager import GenreMixin
from .import_parser import ImportMixin
from .roster import RosterMixin
from .settings_manager import SettingsMixin
from .slot_manager import SlotMixin
from .slot_ui import DPGBoolVar, DPGVar
from .ui_builder import UISetupMixin
from .utils import get_data_dir, get_icon_path


class App(
    UISetupMixin,
    RosterMixin,
    DragDropMixin,
    EventsMixin,
    GenreMixin,
    SlotMixin,
    OutputMixin,
    DataMixin,
    SettingsMixin,
    DebounceMixin,
    ImportMixin,
):
    @staticmethod
    def _data_path(filename: str) -> str:
        return os.path.join(get_data_dir(), filename)

    def _sync_path(self, filename: str) -> str:
        """Like _data_path but uses the user-configured sync directory when set."""
        sync_dir = getattr(self, "sync_data_dir", "").strip()
        base = sync_dir if (sync_dir and os.path.isdir(sync_dir)) else get_data_dir()
        return os.path.join(base, filename)

    LIBRARY_FILE      = property(lambda self: self._sync_path("lineup_library.yaml"))
    EVENTS_FILE       = property(lambda self: self._sync_path("lineup_events.yaml"))
    WINDOW_STATE_FILE = property(lambda self: self._data_path("window_state.json"))
    AUTO_SAVE_FILE    = property(lambda self: self._data_path("auto_save.json"))

    def __init__(self):
        dpg.create_context()
        setup_fonts()
        # Core architecture
        self.bus   = EventBus()
        self.model = LineupModel(self.bus)
        self._discord_service = DiscordService()

        # ── State variables (DPGVar — tk.StringVar replacements) ─────────
        now = datetime.datetime.now()
        self.event_title_var = DPGVar(default="")
        self.event_vol_var   = DPGVar(default="")
        self.event_timestamp = DPGVar(default=now.strftime("%Y-%m-%d") + " 20:00")
        self.master_duration = DPGVar(default="60")
        self.active_genres   = []
        self.names_only      = DPGBoolVar(default=False)
        self.output_format   = DPGVar(default="discord")
        self.genre_entry_var  = DPGVar(default="")
        self.genre_search_var = DPGVar(default="")
        self.dj_search_var   = DPGVar(default="")
        self.slots           = []
        self.social_links: dict[str, str] = {}

        # ── Debounce state ────────────────────────────────────────────────
        self._init_debounce()
        self._current_event_key = None

        # ── Load data & settings ─────────────────────────────────────────
        self.load_settings()  # must run first so sync_data_dir is available
        self.load_data()

        # ── DPG viewport ─────────────────────────────────────────────────
        _icon = get_icon_path() or ""
        dpg.create_viewport(
            title="Lineup Builder",
            width=800,
            height=600,
            min_width=800,
            min_height=600,
            small_icon=_icon,
            large_icon=_icon,
        )

        # Apply the DPG theme from settings
        self.apply_theme()

        # Build the UI (widgets created here)
        self.setup_ui()

        dpg.setup_dearpygui()
        dpg.show_viewport()

        # Restore window geometry NOW (viewport exists)
        self._restore_window_state()

        # Populate lineup
        self.add_initial_slots()
        self.update_output()

        # Check for unclean-exit auto-save on the first frame
        self._work_queue.put(self._check_auto_save)
        
        # Give DPG a few frames to calculate real widget sizes before packing genres
        dpg.set_frame_callback(3, lambda: self._schedule_genre_refresh())

    def run(self):
        """Main DPG render loop — processes the work queue every frame."""
        while dpg.is_dearpygui_running():
            self.process_queue()
            dpg.render_dearpygui_frame()
        self._on_close()
        dpg.destroy_context()

    def _save_window_state(self):
        try:
            state = {
                "pos":          list(dpg.get_viewport_pos()),
                "width":        dpg.get_viewport_width(),
                "height":       dpg.get_viewport_height(),
                "slots_height": dpg.get_item_height("slots_scroll") if dpg.does_item_exist("slots_scroll") else 320,
            }
            with open(self.WINDOW_STATE_FILE, "w") as f:
                import json
                json.dump(state, f, indent=2)
        except Exception as e:
            print(f"[app] _save_window_state error: {e}")

    def _restore_window_state(self):
        try:
            import json
            if not os.path.exists(self.WINDOW_STATE_FILE):
                return
            with open(self.WINDOW_STATE_FILE) as f:
                state = json.load(f)
            if "pos" in state:
                dpg.set_viewport_pos(state["pos"])
            if "width" in state and "height" in state:
                dpg.set_viewport_width(state["width"])
                dpg.set_viewport_height(state["height"])
            if "slots_height" in state and dpg.does_item_exist("slots_scroll"):
                dpg.configure_item("slots_scroll", height=int(state["slots_height"]))
        except Exception as e:
            print(f"[app] _restore_window_state error: {e}")

    def _on_close(self):
        self._save_window_state()
        # Cancel any pending debounce timers then flush a final library save
        for attr in ("_update_job", "_roster_job", "_save_lib_job",
                     "_auto_save_job", "_auto_event_save_job"):
            self._cancel(attr)
        self._save_library()
