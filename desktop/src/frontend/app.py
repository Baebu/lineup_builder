"""
Module: app.py
Purpose: App class — composes all mixins, owns DPG lifecycle.
"""
import datetime
import logging
import os
import queue

import dearpygui.dearpygui as dpg

from src.backend.services.api_client import APIClient
from src.backend.data_manager import DataMixin
from src.backend.debounce import DebounceMixin
from src.backend.services.discord_oauth import DiscordOAuth
from src.backend.services.discord_service import DiscordService
from src.backend.models.event_bus import EventBus
from src.backend.models.lineup_model import LineupModel
from src.backend.output.output_builder import OutputMixin

from .mixins.drag_drop import DragDropMixin
from .mixins.events_manager import EventsMixin
from .mixins.bookings import BookingsMixin
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
    BookingsMixin,
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

        # ── Minimal init for settings (needed for OAuth credentials) ─────
        self.bus   = EventBus()
        self.model = LineupModel(self.bus)
        self._discord_service = DiscordService()
        self._login_queue = queue.SimpleQueue()
        self._oauth = DiscordOAuth()
        self._local_mode = False

        # Load settings so we can read discord_client_id, discord_oauth, etc.
        self.load_settings()
        self.api = APIClient(self.server_url, self.server_api_key)

        # Try to restore a previous Discord OAuth session
        saved_oauth = getattr(self, "discord_oauth", {})
        self._auth_valid = False
        if saved_oauth.get("access_token"):
            self._oauth.restore(saved_oauth)
            if self._oauth.is_signed_in:
                self._auth_valid = True

        # Create the viewport once — login and main app share it
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
        self.apply_theme()
        dpg.setup_dearpygui()
        dpg.show_viewport()

        if self._auth_valid:
            self._init_main_app()
        else:
            self._show_login_window()

    # ── Login window ──────────────────────────────────────────────────────

    def _show_login_window(self):
        """Show centered login UI inside the main viewport."""
        with dpg.window(tag="login_window", no_title_bar=True, no_resize=True,
                        no_move=True, no_scrollbar=True):
            dpg.add_spacer(height=200)
            with dpg.group(indent=250):
                styled_text("LINEUP BUILDER", HEADER)
                dpg.add_spacer(height=16)
                add_primary_button(
                    "Sign in with Discord",
                    tag="discord_login_btn",
                    width=300,
                    callback=lambda: self._start_discord_login(),
                )
                dpg.add_spacer(height=6)
                dpg.add_button(
                    label="Run in local mode",
                    tag="local_mode_btn",
                    width=300,
                    callback=lambda: self._login_queue.put(("local", None)),
                )
                dpg.add_spacer(height=8)
                styled_text("", ERROR, tag="login_error_label")

        dpg.set_primary_window("login_window", True)

    def _start_discord_login(self, error_tag="login_error_label", btn_tag="discord_login_btn"):
        """Kick off the Discord OAuth flow."""
        client_id = getattr(self, "discord_client_id", "")
        client_secret = getattr(self, "discord_client_secret", "")

        if not client_id:
            if dpg.does_item_exist(error_tag):
                dpg.set_value(error_tag, "   Discord Client ID not configured.")
            return

        if dpg.does_item_exist(error_tag):
            dpg.set_value(error_tag, "   Opening browser...")
        if dpg.does_item_exist(btn_tag):
            dpg.configure_item(btn_tag, enabled=False)

        def _on_success(user_info):
            self._login_queue.put(("ok", user_info))

        def _on_error(msg):
            self._login_queue.put(("error", msg))

        self._oauth.start_sign_in(
            client_id, client_secret,
            on_success=_on_success,
            on_error=_on_error,
        )

    def _sign_in_from_app(self):
        """Sign in with Discord from the Account tab (replaces local data with cloud)."""
        import threading

        client_id = getattr(self, "discord_client_id", "")
        client_secret = getattr(self, "discord_client_secret", "")

        if not client_id:
            if dpg.does_item_exist("account_error_label"):
                dpg.set_value("account_error_label", "  Discord Client ID not configured.")
            return

        if dpg.does_item_exist("account_error_label"):
            dpg.set_value("account_error_label", "  Opening browser...")
        if dpg.does_item_exist("account_signin_btn"):
            dpg.configure_item("account_signin_btn", enabled=False)

        def _on_success(user_info):
            # Push result to work queue so it runs on the main thread
            def _finish():
                self._local_mode = False
                self.discord_oauth = self._oauth.to_dict()
                self.save_settings()
                # Reload all data from cloud (replaces local)
                self.load_data()
                self._load_cloud_settings()
                self.apply_theme()
                # Refresh the UI with the new data
                self._schedule_roster_refresh()
                self._schedule_genre_refresh()
                self._schedule_update()
                self._refresh_account_drawer()
                self._apply_local_mode_visibility()
                # Auto-link DJ profile if not already linked
                if not self.dj_profile.get("signed_in"):
                    self._dj_discord_sign_in()
                # Load VRChat group link for new account
                self._load_vrchat_group_info()
            self._work_queue.put(_finish)

        def _on_error(msg):
            def _show_err():
                if dpg.does_item_exist("account_error_label"):
                    dpg.set_value("account_error_label", f"  {msg}")
                if dpg.does_item_exist("account_signin_btn"):
                    dpg.configure_item("account_signin_btn", enabled=True)
            self._work_queue.put(_show_err)

        self._oauth.start_sign_in(
            client_id, client_secret,
            on_success=_on_success,
            on_error=_on_error,
        )

    def _run_login_loop(self):
        """Render loop for the login window. Returns True if auth succeeded."""
        while dpg.is_dearpygui_running():
            # Check for OAuth callback results
            try:
                kind, data = self._login_queue.get_nowait()
                if kind == "ok":
                    # Save OAuth data
                    self.discord_oauth = self._oauth.to_dict()
                    self.save_settings()
                    return True
                elif kind == "local":
                    self._local_mode = True
                    return True
                else:
                    dpg.set_value("login_error_label", f"   {data}")
                    dpg.configure_item("discord_login_btn", enabled=True)
            except queue.Empty:
                pass
            dpg.render_dearpygui_frame()
        return False

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

        # Load persisted scheduled posts
        self._load_scheduled_posts()

        # Update the auth card to reflect current sign-in status
        dpg.set_frame_callback(5, lambda: self._update_auth_card())

        # Hide server-dependent tabs in local mode
        dpg.set_frame_callback(6, lambda: self._apply_local_mode_visibility())

        # Load existing VRChat group link (if signed in)
        dpg.set_frame_callback(7, lambda: self._load_vrchat_group_info())

        # Fetch booked DJs from server (if signed in)
        dpg.set_frame_callback(8, lambda: self._fetch_booked_djs())

    def run(self):
        """Main entry point — login → main app → render loop."""
        if not self._auth_valid:
            # Run the login loop; if user closes the window, exit
            if not self._run_login_loop():
                dpg.destroy_context()
                return
            # Transition: remove login UI, build main app in same viewport
            dpg.delete_item("login_window")
            if not self._local_mode:
                self._oauth.restore(self.discord_oauth)
            self._init_main_app()

        # Main render loop
        while dpg.is_dearpygui_running():
            self.process_queue()
            self.check_scheduled_posts()
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
