"""
Module: app.py
Purpose: App class — composes all mixins, owns DPG lifecycle.
"""
import datetime
import os

import dearpygui.dearpygui as dpg

from src.backend.data_manager import DataMixin
from src.backend.debounce import DebounceMixin
from src.backend.event_bus import EventBus
from src.backend.lineup_model import LineupModel
from src.backend.output_builder import OutputMixin

from .dj_roster import DJRosterMixin
from .drag_drop import DragDropMixin
from .events_manager import EventsMixin
from .genre_manager import GenreMixin
from .import_parser import ImportMixin
from .settings_manager import SettingsMixin
from .slot_manager import SlotMixin
from .slot_ui import DPGBoolVar, DPGVar
from .ui_builder import UISetupMixin
from .utils import get_data_dir, get_icon_path
from .fonts import Icon, setup_fonts


class App(
    UISetupMixin,
    DJRosterMixin,
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

    LIBRARY_FILE      = property(lambda self: self._data_path("lineup_library.yaml"))
    EVENTS_FILE       = property(lambda self: self._data_path("lineup_events.yaml"))
    WINDOW_STATE_FILE = property(lambda self: self._data_path("window_state.json"))
    AUTO_SAVE_FILE    = property(lambda self: self._data_path("auto_save.json"))

    def __init__(self):
        dpg.create_context()
        setup_fonts()
        # Core architecture
        self.bus   = EventBus()
        self.model = LineupModel(self.bus)

        # ── State variables (DPGVar — tk.StringVar replacements) ─────────
        now = datetime.datetime.now()
        self.event_title_var = DPGVar(default="")
        self.event_vol_var   = DPGVar(default="")
        self.event_timestamp = DPGVar(default=now.strftime("%Y-%m-%d") + " 20:00")
        self.master_duration = DPGVar(default="60")
        self.active_genres   = []
        self.names_only      = DPGBoolVar(default=False)
        self.output_format   = DPGVar(default="discord")
        self.include_od      = DPGBoolVar(default=False)
        self.od_duration     = DPGVar(default="30")
        self.od_count        = DPGVar(default="4")
        self.genre_entry_var = DPGVar(default="")
        self.dj_search_var   = DPGVar(default="")
        self.slots           = []

        # ── Debounce state ────────────────────────────────────────────────
        self._init_debounce()
        self._current_event_key = None

        # ── Load data & settings ─────────────────────────────────────────
        self.load_data()
        self.load_settings()

        # ── DPG viewport ─────────────────────────────────────────────────
        _icon = get_icon_path() or ""
        dpg.create_viewport(
            title="Lineup Builder",
            width=1280,
            height=960,
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

    def run(self):
        """Main DPG render loop — processes the work queue every frame."""
        while dpg.is_dearpygui_running():
            self.process_queue()
            dpg.render_dearpygui_frame()
        self._on_close()
        dpg.destroy_context()
