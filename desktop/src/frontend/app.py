"""
Module: app.py
Purpose: App class — composes all mixins, owns DPG lifecycle.
"""
import datetime
import logging
import os
import queue

import dearpygui.dearpygui as dpg

from src.backend.services.discord_service import DiscordService
from src.backend.models.event_bus import EventBus
from src.backend.models.lineup_model import LineupModel
from src.backend.output.output_builder import OutputMixin
from src.backend.data_manager import DataMixin
from src.backend.debounce import DebounceMixin

from .mixins.drag_drop import DragDropMixin
from .mixins.events_manager import EventsMixin
from .styling.fonts import setup_fonts, styled_text, HEADER, MUTED, ERROR
from .mixins.genre_manager import GenreMixin
from .mixins.import_parser import ImportMixin
from .mixins.roster import RosterMixin
from .mixins.sections import SectionsMixin
from .mixins.settings_manager import SettingsMixin
from .mixins.slot_manager import SlotMixin
from .ui.slot_ui import DPGBoolVar, DPGVar
from .ui.ui_builder import UISetupMixin
from .utils import get_data_dir, get_icon_path
from .ui.widgets import add_primary_button

log = logging.getLogger("app")


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
    SectionsMixin,
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

        self.bus   = EventBus()
        self.model = LineupModel(self.bus)
        self._discord_service = DiscordService()
        self._local_mode = True

        self.load_settings()

        _icon = get_icon_path() or ""
        dpg.create_viewport(
            title="Lineup Builder",
            width=1000,
            height=900,
            min_width=800,
            min_height=700,
            small_icon=_icon,
            large_icon=_icon,
        )
        self.apply_theme()
        dpg.setup_dearpygui()
        dpg.show_viewport()

        self._init_main_app()

    # ── Login window ──────────────────────────────────────────────────────



    # ── Main app init ─────────────────────────────────────────────────────

    def _init_main_app(self):
        """Initialize the full application (state + UI) inside the existing viewport."""
        # ── State variables (DPGVar — tk.StringVar replacements) ─────────
        now = datetime.datetime.now()
        self.event_title_var  = DPGVar(default="")
        self.event_vol_var   = DPGVar(default="")
        self.group_name_var  = DPGVar(default="")
        self.collab_var      = DPGBoolVar(default=False)
        self.collab_with_var = DPGVar(default="")
        self.event_timestamp = DPGVar(default=now.strftime("%Y-%m-%d") + " 20:00")
        self.active_genres   = []
        self.names_only      = DPGBoolVar(default=False)
        self.output_format   = DPGVar(default="discord")
        self.stream_link_format = DPGVar(default="")
        self.genre_entry_var  = DPGVar(default="")
        self.genre_search_var = DPGVar(default="")
        self.dj_search_var   = DPGVar(default="")
        self.slots           = []
        self.social_links: dict[str, str] = {}

        # ── Debounce state ────────────────────────────────────────────────
        self._init_debounce()
        self._current_event_key = None

        # ── Load data ─────────────────────────────────────────────────────
        self.load_data()

        # Build the UI (widgets created here)
        self.setup_ui()

        # Restore window geometry
        self._restore_window_state()

        # Populate lineup
        self.add_initial_slots()
        self.update_output()

        # Check for unclean-exit auto-save on the first frame
        self._work_queue.put(self._check_auto_save)
        
        # Give DPG a few frames to calculate real widget sizes before packing genres
        dpg.set_frame_callback(3, lambda: self._schedule_genre_refresh())






    def run(self):
        """Main entry point — load minimal app."""
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
                "tabs_height":  dpg.get_item_height("right_tabs_content") if dpg.does_item_exist("right_tabs_content") else 360,
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
            if "tabs_height" in state and dpg.does_item_exist("right_tabs_content"):
                h = int(state["tabs_height"])
                dpg.configure_item("right_tabs_content", height=h)
                self._base_tabs_height = h
                self._base_vp_height = dpg.get_viewport_height()
        except Exception as e:
            print(f"[app] _restore_window_state error: {e}")

    def _on_close(self):
        self._save_window_state()
        # Cancel any pending debounce timers then flush a final library save
        for attr in ("_update_job", "_roster_job", "_save_lib_job",
                     "_auto_save_job", "_auto_event_save_job"):
            self._cancel(attr)
        self._save_library()
