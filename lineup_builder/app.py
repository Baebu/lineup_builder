import customtkinter as ctk
import datetime
from iconipy import IconFactory

from .utils import _make_icon
from .data_manager import DataMixin
from .debounce import DebounceMixin
from .ui_builder import UISetupMixin
from .dj_roster import DJRosterMixin
from .drag_drop import DragDropMixin
from .events_manager import EventsMixin
from .genre_manager import GenreMixin
from .slot_manager import SlotMixin
from .output_builder import OutputMixin


class App(
    UISetupMixin,
    DJRosterMixin,
    DragDropMixin,
    EventsMixin,
    GenreMixin,
    SlotMixin,
    OutputMixin,
    DataMixin,
    DebounceMixin,
    ctk.CTk,
):
    LIBRARY_FILE = "lineup_library.yaml"
    EVENTS_FILE = "lineup_events.yaml"
    WINDOW_STATE_FILE = "window_state.json"

    def __init__(self):
        ctk.CTk.__init__(self)

        self.title("Lineup Builder")
        self.geometry("1150x850")
        self._restore_window_state()

        ctk.set_appearance_mode("dark")
        self.configure(fg_color="#0F172A")

        self.grid_columnconfigure(0, weight=1, uniform="group1")
        self.grid_columnconfigure(1, weight=1, uniform="group1")
        self.grid_rowconfigure(0, weight=1)

        # Icons
        _icons = IconFactory(icon_size=36, font_color="white")
        self.icon_discord       = _make_icon(_icons, "message-square-text", 18)
        self.icon_text          = _make_icon(_icons, "file-text",            18)
        self.icon_trash         = _make_icon(_icons, "trash-2",              16)
        self.icon_quest         = _make_icon(_icons, "glasses",              18)
        self.icon_pc            = _make_icon(_icons, "monitor",              18)
        self.icon_arrow_up      = _make_icon(_icons, "arrow-up",             14)
        self.icon_arrow_down    = _make_icon(_icons, "arrow-down",           14)
        self.icon_chevron_down  = _make_icon(_icons, "chevron-down",         14)
        self.icon_chevron_up    = _make_icon(_icons, "chevron-up",           14)
        self.icon_chevron_right = _make_icon(_icons, "chevron-right",        14)
        self.icon_grip          = _make_icon(_icons, "grip-vertical",        14)
        self.icon_save          = _make_icon(_icons, "save",                 16)
        self.icon_copy          = _make_icon(_icons, "copy",                 16)

        self.load_data()

        now = datetime.datetime.now()
        self.event_timestamp = ctk.StringVar(value=f"{now.strftime('%Y-%m-%d')} 20:00")
        self.event_title_var = ctk.StringVar(value="")
        self.event_vol_var = ctk.StringVar(value="")
        self.master_duration = ctk.StringVar(value="60")
        self.active_genres = []
        self.genre_entry_var = ctk.StringVar()
        self.genre_dropdown_var = ctk.StringVar(value="")
        self.names_only = ctk.BooleanVar(value=False)
        self.output_format = ctk.StringVar(value="discord")
        self.include_od = ctk.BooleanVar(value=False)
        self.od_duration = ctk.StringVar(value="30")
        self.od_count = ctk.StringVar(value="4")
        self.slots = []

        # Drag-and-drop state
        self._drag_ghost = None
        self._slot_ghost = None
        self._drop_indicator = None

        # Debounce state
        self._update_job = None
        self._roster_job = None
        self._save_lib_job = None

        # DJ roster search
        self.dj_search_var = ctk.StringVar()

        self.setup_ui()
        self.add_initial_slots()
        self.update_output()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
