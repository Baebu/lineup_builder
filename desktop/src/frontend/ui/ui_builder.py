"""
Module: ui_builder.py
Purpose: Builds the entire application UI layout (Dear PyGui).
Architecture: Mixin for App class.
"""
from datetime import datetime, timedelta
import io
import logging
import os as _os
import secrets
import threading

import dearpygui.dearpygui as dpg

from ..styling import theme as T
from .date_time_picker import add_datetime_row, add_date_row, add_time_row
from ..styling.fonts import styled_text, bind_icon_font, Icon, HEADER, LABEL, BODY, MUTED, HINT, ERROR, SUCCESS
from .widgets import add_icon_button, add_primary_button, add_danger_button

log = logging.getLogger("ui-builder")



class UISetupMixin:
    """Builds the entire application UI and provides helpers."""

    _LEFT_MIN = 300
    _LEFT_MAX = 350
    _LEFT_DEFAULT = 325

    def setup_ui(self):
        with dpg.window(tag="primary_window", no_title_bar=True, no_resize=True,
                        no_move=True, no_scrollbar=True,
                        no_scroll_with_mouse=True):
            with dpg.table(header_row=False, resizable=False,
                           scrollX=False, scrollY=False,
                           policy=dpg.mvTable_SizingFixedFit):
                dpg.add_table_column(init_width_or_weight=self._LEFT_DEFAULT,
                                     width_fixed=True)
                dpg.add_table_column(init_width_or_weight=1, width_fixed=True)
                dpg.add_table_column(width_stretch=True)
                with dpg.table_row():
                    with dpg.child_window(tag="left_panel", border=False,
                                          no_scrollbar=True):
                        self._build_left_panel()
                    with dpg.child_window(tag="panel_divider", border=False,
                                          no_scrollbar=True, width=1):
                        with dpg.theme() as _div_theme:
                            with dpg.theme_component(dpg.mvChildWindow):
                                dpg.add_theme_color(dpg.mvThemeCol_ChildBg, T.DPG_BORDER)
                        dpg.bind_item_theme("panel_divider", _div_theme)
                    with dpg.child_window(tag="right_panel", border=False,
                                          no_scrollbar=True):
                        self._build_right_panel()

        dpg.set_primary_window("primary_window", True)
        self._build_settings_tab()
        self.apply_theme()
        self._setup_wheel_handler()

        # Track base dimensions for proportional resize of right_tabs_content
        self._base_vp_height = dpg.get_viewport_height()
        self._base_tabs_height = 360
        dpg.set_viewport_resize_callback(self._on_viewport_resize)

    # ── Left panel ────────────────────────────────────────────────────────

    _DRAWER_HEIGHT = 130
    _AUTH_BTN_HEIGHT = 26

    def _build_left_panel(self):
        self._account_drawer_open = False

        with dpg.child_window(tag="left_tabs_wrapper", border=False,
                              autosize_x=True, height=-self._AUTH_BTN_HEIGHT,
                              no_scrollbar=True):
            with dpg.tab_bar(tag="left_tabs"):
                with dpg.tab(label="Event", tag="Event"):
                    self._build_event_tab()
                with dpg.tab(label="Club", tag="Club"):
                    self._build_club_tab()
                with dpg.tab(label="Bookings", tag="Bookings"):
                    self._build_bookings_tab()
                with dpg.tab(label="Roster", tag="Roster"):
                    self._build_dj_roster_tab()
                with dpg.tab(label="DJ", tag="DJ"):
                    self._build_dj_profile_tab()
                with dpg.tab(label="Settings", tag="Settings"):
                    with dpg.child_window(tag="settings_scroll", height=-1,
                                          border=False, autosize_x=True):
                        pass  # populated by _build_settings_tab()

        # ── Avatar texture (must exist before drawer references it) ────────
        with dpg.texture_registry():
            dpg.add_static_texture(1, 1, [0, 0, 0, 0], tag="auth_avatar_tex")

        # ── Account drawer (hidden by default, expands upward) ───────────
        with dpg.child_window(tag="account_drawer", height=self._DRAWER_HEIGHT,
                              border=True, autosize_x=True, no_scrollbar=True,
                              show=False):
            self._build_account_drawer()

        # ── Auth card toggle button ───────────────────────────────────
        dpg.add_button(tag="auth_card_btn", label="Local", width=-1,
                       height=self._AUTH_BTN_HEIGHT,
                       callback=lambda: self._toggle_account_drawer())

    def _build_event_tab(self):
        with dpg.child_window(tag="event_tab_inner", border=False,
                              autosize_x=True, height=-1):
            # ── Header row ────────────────────────────────────────────────────
            styled_text("   EVENT CONFIGURATION", HEADER)
            with dpg.group(horizontal=True):
                dpg.add_spacer(width=4)
                dpg.add_button(label="+ New", width=80,
                               callback=lambda: self.new_event())
                add_primary_button("Load", tag="load_event_btn", width=80,
                                   callback=lambda: self._toggle_saved_events_drawer())
            dpg.add_separator()

            # ── Saved events drawer (inline, hidden by default) ─────────
            with dpg.child_window(tag="saved_events_drawer", height=200,
                                  border=True, autosize_x=True, show=False):
                with dpg.child_window(tag="saved_events_scroll", height=-1,
                                      border=False, autosize_x=True):
                    pass  # populated by refresh_saved_events_ui()
            self._saved_events_drawer_open = False

            # ── Form fields (table for aligned labels) ─────────────────────
            _LABEL_W = 62
            with dpg.table(header_row=False, borders_innerH=False,
                           borders_innerV=False, borders_outerH=False,
                           borders_outerV=False, pad_outerX=False):
                dpg.add_table_column(init_width_or_weight=_LABEL_W, width_fixed=True)
                dpg.add_table_column(width_stretch=True)

                # ── Title + Vol ───────────────────────────────────────────
                with dpg.table_row():
                    styled_text("   TITLE", LABEL)
                    with dpg.group(horizontal=True):
                        dpg.add_input_text(
                            tag="event_title_input",
                            default_value=self.event_title_var.get(),
                            hint="Event title...", width=-50,
                            callback=lambda s, a, u=None: self._schedule_update(),
                        )
                        dpg.add_input_text(
                            tag="event_vol_input",
                            default_value=self.event_vol_var.get(),
                            hint="Vol",
                            width=38,
                            callback=lambda s, a, u=None: self._schedule_update(),
                        )
                        with dpg.theme() as _pill_theme:
                            with dpg.theme_component(dpg.mvInputText):
                                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 999)
                        dpg.bind_item_theme("event_vol_input", _pill_theme)

                # ── Club ──────────────────────────────────────────────────
                with dpg.table_row():
                    styled_text("   CLUB", LABEL)
                    dpg.add_input_text(
                        tag="group_name_input",
                        default_value=self.group_name_var.get(),
                        hint="Club name...", width=-1,
                        callback=lambda s, a, u=None: self._schedule_update(),
                    )

                # ── Collab ────────────────────────────────────────────────
                with dpg.table_row():
                    styled_text("   COLLAB", LABEL)
                    dpg.add_input_text(
                        tag="collab_with_input",
                        default_value=self.collab_with_var.get(),
                        hint="Collab with...", width=-1,
                        callback=lambda s, a, u=None: self._schedule_update(),
                    )

                # ── Start ─────────────────────────────────────────────────
                with dpg.table_row():
                    styled_text("   START", LABEL)
                    add_datetime_row(
                        "event_timestamp_input", self.event_timestamp,
                        callback=lambda s, a, u=None: self._schedule_update(),
                    )

                # ── Genres ────────────────────────────────────────────────
                with dpg.table_row():
                    styled_text("   GENRES", LABEL)
                    with dpg.group(horizontal=True):
                        dpg.add_input_text(
                            tag="genre_entry",
                            default_value=self.genre_entry_var.get(),
                            hint="Search or press Enter to add...", width=-50,
                            on_enter=True,
                            callback=lambda s, a, u=None: self.add_genre_from_entry(),
                            user_data=None,
                        )
                        add_icon_button(Icon.EDIT, callback=lambda: self.open_genre_editor())
                        dpg.add_spacer(width=10)

            # ── Post-table tag wiring ─────────────────────────────────────────
            self.event_title_var._tag = "event_title_input"
            self.event_vol_var._tag   = "event_vol_input"
            self._register_scroll_int("event_vol_input", min_val=1,
                                      on_change=lambda: self._schedule_update())
            self.group_name_var._tag  = "group_name_input"
            self.collab_var._tag      = "collab_check"
            self.collab_with_var._tag = "collab_with_input"
            self.genre_entry_var._tag = "genre_entry"
            self.genre_search_var._tag = "genre_entry"
            with dpg.item_handler_registry(tag="genre_entry_hr"):
                dpg.add_item_edited_handler(
                    callback=lambda s, a, u=None: self._schedule_genre_refresh()
                )
            dpg.add_separator()
            dpg.bind_item_handler_registry("genre_entry", "genre_entry_hr")
            with dpg.child_window(tag="genre_tags_frame", height=90,
                                  border=False, autosize_x=True):
                pass  # populated by refresh_genre_tags()
            dpg.add_separator()

            # ── Social Links ──────────────────────────────────────────────
            styled_text("   LINKS", HEADER)
            with dpg.table(header_row=False, borders_innerH=False,
                           borders_innerV=False, borders_outerH=False,
                           borders_outerV=False, pad_outerX=False):
                dpg.add_table_column(init_width_or_weight=_LABEL_W, width_fixed=True)
                dpg.add_table_column(width_stretch=True)
                for label, hint in self._SOCIAL_FIELDS:
                    tag_key = label.replace(' ', '_')
                    with dpg.table_row():
                        styled_text(f"   {label}", LABEL)
                        dpg.add_input_text(
                            tag=f"social_input_{tag_key}",
                            default_value=self.social_links.get(label, ""),
                            hint=hint, width=-1,
                            callback=lambda s, a, u=label: self._on_social_link_changed(u),
                        )

        self.refresh_genre_tags()

    def _build_dj_roster_tab(self):
        with dpg.group(horizontal=True):
            styled_text("   DJS", HEADER)
        add_primary_button("+ New DJ", tag="new_dj_btn", width=-1, callback=lambda: self.add_new_dj_to_roster())
        dpg.add_input_text(
            tag="dj_search_input",
            default_value=self.dj_search_var.get(),
            hint="Search...", width=-11,
            callback=lambda s, a, u=None: self._schedule_roster_refresh(),
        )
        self.dj_search_var._tag = "dj_search_input"
        with dpg.child_window(tag="dj_roster_scroll", height=-1,
                              border=False, autosize_x=True):
            pass  # populated by refresh_dj_roster_ui()
        self.refresh_dj_roster_ui()

    # ── DJ Profile tab ────────────────────────────────────────────────────

    _DJ_LINK_FIELDS = [
        ("Twitch",    "https://twitch.tv/"),
        ("SoundCloud", "https://soundcloud.com/"),
        ("X",         "https://x.com/"),
        ("Instagram", "https://instagram.com/"),
        ("YouTube",   "https://youtube.com/@"),
        ("Website",   ""),
    ]

    def _build_dj_profile_tab(self):
        with dpg.child_window(tag="dj_profile_inner", border=False,
                              autosize_x=True, height=-1):
            # ── Sign-in view (shown when not signed in) ───────────────
            with dpg.group(tag="dj_signin_group"):
                styled_text("   DJ PROFILE", HEADER)
                dpg.add_spacer(height=8)
                styled_text("   Link your Discord account to manage", MUTED)
                styled_text("   your DJ profile, availability, and bookings.", MUTED)
                dpg.add_spacer(height=12)
                add_primary_button(
                    "Link DJ Profile", tag="dj_link_btn", width=-1,
                    callback=lambda: self._dj_discord_sign_in(),
                )
                dpg.add_spacer(height=4)
                styled_text("", HINT, tag="dj_signin_error")

            # ── Profile view (shown when signed in) ───────────────────
            with dpg.group(tag="dj_profile_group", show=False):
                _LABEL_W = 62

                # ── Header with name + sign out ───────────────────────
                with dpg.group(horizontal=True):
                    styled_text("   DJ PROFILE", HEADER)
                dpg.add_spacer(height=2)
                with dpg.group(horizontal=True):
                    dpg.add_spacer(width=4)
                    styled_text("", LABEL, tag="dj_signed_in_label")
                    dpg.add_button(
                        tag="dj_signout_btn", label="Sign Out", width=70,
                        callback=lambda: self._dj_sign_out(),
                    )
                dpg.add_separator()

                # ── Links ─────────────────────────────────────────────
                styled_text("   LINKS", HEADER)
                dpg.add_spacer(height=4)
                with dpg.table(header_row=False, borders_innerH=False,
                               borders_innerV=False, borders_outerH=False,
                               borders_outerV=False, pad_outerX=False):
                    dpg.add_table_column(init_width_or_weight=_LABEL_W, width_fixed=True)
                    dpg.add_table_column(width_stretch=True)
                    for label, hint in self._DJ_LINK_FIELDS:
                        tag_key = label.replace(' ', '_')
                        with dpg.table_row():
                            styled_text(f"   {label.upper()}", LABEL)
                            dpg.add_input_text(
                                tag=f"dj_link_{tag_key}",
                                hint=hint or "https://...", width=-1,
                                callback=lambda s, a, u=label: self._on_dj_link_changed(u),
                            )

                dpg.add_separator()

                # ── Logo ──────────────────────────────────────────────
                styled_text("   LOGO", HEADER)
                dpg.add_spacer(height=4)
                with dpg.table(header_row=False, borders_innerH=False,
                               borders_innerV=False, borders_outerH=False,
                               borders_outerV=False, pad_outerX=False):
                    dpg.add_table_column(init_width_or_weight=_LABEL_W, width_fixed=True)
                    dpg.add_table_column(width_stretch=True)
                    with dpg.table_row():
                        styled_text("   URL", LABEL)
                        dpg.add_input_text(
                            tag="dj_profile_logo",
                            hint="Image URL or local path...", width=-1,
                            callback=lambda s, a: self._on_dj_profile_changed(
                                "logo", dpg.get_value("dj_profile_logo").strip()),
                        )

                dpg.add_separator()

                # ── Genres ────────────────────────────────────────────
                styled_text("   GENRES", HEADER)
                dpg.add_spacer(height=4)
                with dpg.group(horizontal=True):
                    dpg.add_input_text(
                        tag="dj_genre_input", hint="Add genre...",
                        width=-60, on_enter=True,
                        callback=lambda s, a: self._dj_add_genre(),
                    )
                    dpg.add_button(
                        label="+", width=40,
                        callback=lambda: self._dj_add_genre(),
                    )
                dpg.add_spacer(height=4)
                with dpg.group(tag="dj_genre_tags"):
                    pass  # populated by _dj_refresh_genres()

                dpg.add_separator()

                # ── Availability ──────────────────────────────────────
                styled_text("   AVAILABILITY", HEADER)
                dpg.add_spacer(height=4)
                add_primary_button(
                    "+ Add Date", tag="dj_avail_add_btn", width=-1,
                    callback=lambda: self._dj_add_availability(),
                )
                dpg.add_spacer(height=4)
                with dpg.child_window(tag="dj_avail_scroll", height=150,
                                      border=False, autosize_x=True):
                    pass  # populated by _dj_refresh_availability()

                dpg.add_separator()

                # ── My Bookings ───────────────────────────────────────
                with dpg.group(horizontal=True):
                    styled_text("   MY BOOKINGS", HEADER)
                    add_icon_button(
                        Icon.REFRESH,
                        callback=lambda: self._refresh_dj_bookings(),
                    )
                dpg.add_spacer(height=4)
                with dpg.child_window(tag="dj_bookings_scroll", height=-1,
                                      border=False, autosize_x=True):
                    pass  # populated by _refresh_dj_bookings()

        # If already signed in from a previous session, restore the view
        if self.dj_profile.get("signed_in") and self.dj_profile.get("name"):
            self._dj_restore_session()

    def _dj_discord_sign_in(self):
        """Link DJ profile using the current Discord OAuth identity."""
        discord_id = ""
        discord_name = ""
        if self._oauth and self._oauth.is_signed_in and self._oauth.user_info:
            discord_id = str(self._oauth.user_info.get("id", ""))
            discord_name = self._oauth.user_info.get("username", "")

        if not discord_id:
            dpg.set_value("dj_signin_error", "   Sign in with Discord first.")
            return

        if not self.api.base_url:
            dpg.set_value("dj_signin_error", "   Server URL not configured.")
            return

        dpg.set_value("dj_signin_error", "   Linking profile...")
        dpg.configure_item("dj_link_btn", enabled=False)

        def _do():
            try:
                from src.backend.services.api_client import APIError
                result = self.api.dj_discord_auth(discord_id, discord_name)
                name = result["name"]
                profile = self.api.dj_get_profile(name)

                def _on_ok():
                    self.dj_profile["name"] = name
                    self.dj_profile["discord_id"] = discord_id
                    self.dj_profile["links"] = profile.get("links", {})
                    self.dj_profile["logo"] = profile.get("logo", "")
                    self.dj_profile["genres"] = profile.get("genres", [])
                    self.dj_profile["availability"] = profile.get("availability", [])
                    self.dj_profile["signed_in"] = True
                    self.save_settings()
                    dpg.set_value("dj_signin_error", "")
                    dpg.configure_item("dj_link_btn", enabled=True)
                    self._dj_show_profile()

                self._work_queue.put(_on_ok)
            except APIError as exc:
                def _on_err():
                    dpg.set_value("dj_signin_error", f"   {exc.detail}")
                    dpg.configure_item("dj_link_btn", enabled=True)
                self._work_queue.put(_on_err)
            except Exception:
                def _on_err():
                    dpg.set_value("dj_signin_error", "   Connection failed.")
                    dpg.configure_item("dj_link_btn", enabled=True)
                self._work_queue.put(_on_err)

        threading.Thread(target=_do, daemon=True).start()

    def _dj_sign_out(self):
        """Unlink — keeps the account on the server but marks as not signed in locally."""
        self.dj_profile["signed_in"] = False
        self.save_settings()
        dpg.configure_item("dj_profile_group", show=False)
        dpg.configure_item("dj_signin_group", show=True)
        dpg.set_value("dj_signin_error", "")

    def _dj_restore_session(self):
        """Restore profile view if already signed in from settings."""
        dpg.configure_item("dj_signin_group", show=False)
        self._dj_show_profile()

        # Fetch latest profile from server in background
        if self.api.base_url and self.dj_profile.get("name"):
            name = self.dj_profile["name"]

            def _do():
                try:
                    profile = self.api.dj_get_profile(name)

                    def _on_ok():
                        self.dj_profile["links"] = profile.get("links", {})
                        self.dj_profile["logo"] = profile.get("logo", "")
                        self.dj_profile["genres"] = profile.get("genres", [])
                        self.dj_profile["availability"] = profile.get("availability", [])
                        self.save_settings()
                        self._dj_show_profile()

                    self._work_queue.put(_on_ok)
                except Exception:
                    log.debug("Failed to refresh profile from server", exc_info=True)

            threading.Thread(target=_do, daemon=True).start()

    def _dj_show_profile(self):
        """Switch to the profile editor and populate fields from saved data."""
        profile = self.dj_profile
        name = profile.get("name", "")

        # Update header label
        dpg.set_value("dj_signed_in_label", f"   Signed in as {name}")

        # Populate links
        links = profile.get("links", {})
        for label, _ in self._DJ_LINK_FIELDS:
            tag = f"dj_link_{label.replace(' ', '_')}"
            if dpg.does_item_exist(tag):
                dpg.set_value(tag, links.get(label, ""))

        # Populate logo
        if dpg.does_item_exist("dj_profile_logo"):
            dpg.set_value("dj_profile_logo", profile.get("logo", ""))

        # Populate genres
        self._dj_refresh_genres()

        # Populate availability
        self._dj_refresh_availability()

        # Refresh bookings from server
        self._refresh_dj_bookings()

        dpg.configure_item("dj_signin_group", show=False)
        dpg.configure_item("dj_profile_group", show=True)

    def _on_dj_profile_changed(self, key: str, value):
        """Generic handler for scalar profile fields."""
        self.dj_profile[key] = value
        self.save_settings()
        self._dj_sync_profile_to_server()

    def _on_dj_link_changed(self, label: str):
        """Called when a DJ profile link input changes."""
        tag = f"dj_link_{label.replace(' ', '_')}"
        value = dpg.get_value(tag).strip()
        if "links" not in self.dj_profile:
            self.dj_profile["links"] = {}
        self.dj_profile["links"][label] = value
        self.save_settings()
        self._dj_sync_profile_to_server()

    def _dj_sync_profile_to_server(self):
        """Debounced sync of local DJ profile data to the server."""
        if not self.api.base_url or not self.dj_profile.get("signed_in"):
            return
        name = self.dj_profile.get("name", "")
        if not name:
            return

        def _do():
            try:
                self.api.dj_update_profile(
                    name,
                    links=self.dj_profile.get("links", {}),
                    logo=self.dj_profile.get("logo", ""),
                    genres=self.dj_profile.get("genres", []),
                    availability=self.dj_profile.get("availability", []),
                )
            except Exception:
                log.debug("Failed to sync profile to server", exc_info=True)

        threading.Thread(target=_do, daemon=True).start()

    def _refresh_dj_bookings(self):
        """Fetch and display bookings for the signed-in DJ."""
        if not self.api.base_url or not self.dj_profile.get("signed_in"):
            return
        name = self.dj_profile.get("name", "")
        if not name:
            return

        def _do():
            try:
                bookings = self.api.list_dj_bookings(name)

                def _on_ok():
                    self._render_dj_bookings(bookings)

                self._work_queue.put(_on_ok)
            except Exception:
                log.debug("Failed to refresh DJ bookings", exc_info=True)

        threading.Thread(target=_do, daemon=True).start()

    def _render_dj_bookings(self, bookings: list[dict]):
        """Render booking cards with accept/decline buttons."""
        container = "dj_bookings_scroll"
        if not dpg.does_item_exist(container):
            return
        for child in dpg.get_item_children(container, 1) or []:
            dpg.delete_item(child)

        if not bookings:
            styled_text("   No bookings yet.", MUTED, parent=container)
            return

        for b in bookings:
            bid = b["id"]
            status = b.get("status", "pending")
            with dpg.group(parent=container):
                with dpg.group(horizontal=True):
                    styled_text(f"   #{bid}  ", LABEL)
                    styled_text(b.get("group_name", ""), BODY)
                    if status == "pending":
                        styled_text("  [pending]", MUTED)
                    elif status == "accepted":
                        styled_text("  [accepted]", LABEL)
                    else:
                        styled_text("  [declined]", HINT)

                if b.get("event_title"):
                    styled_text(
                        f"      {b['event_title']}  {b.get('event_date', '')}  "
                        f"{b.get('start_time', '')}  ({b.get('duration', 60)} min)",
                        MUTED,
                    )
                if b.get("message"):
                    styled_text(f"      \"{b['message']}\"", MUTED)

                if status == "pending":
                    with dpg.group(horizontal=True):
                        dpg.add_spacer(width=14)
                        add_primary_button(
                            "Accept", width=70,
                            callback=lambda s=None, a=None, bk=bid: self._respond_booking(bk, "accepted"),
                        )
                        dpg.add_button(
                            label="Decline", width=70,
                            callback=lambda s=None, a=None, bk=bid: self._respond_booking(bk, "declined"),
                        )
                dpg.add_separator()

    def _respond_booking(self, booking_id: int, status: str):
        """Accept or decline a booking."""
        if not self.api.base_url:
            return

        def _do():
            try:
                self.api.respond_to_booking(booking_id, status)

                def _on_ok():
                    self._refresh_dj_bookings()

                self._work_queue.put(_on_ok)
            except Exception:
                log.debug("Failed to respond to booking %s", booking_id, exc_info=True)

        threading.Thread(target=_do, daemon=True).start()

    def _dj_add_availability(self):
        """Add a new blank availability entry."""
        entries = self.dj_profile.get("availability", [])
        if not isinstance(entries, list) or (entries and isinstance(entries[0], str)):
            entries = []  # migrate from old day-of-week format
        now = datetime.now()
        entries.append({
            "date": now.strftime("%Y-%m-%d"),
            "start": "8:00 PM",
            "end": "11:00 PM",
        })
        self.dj_profile["availability"] = entries
        self.save_settings()
        self._dj_sync_profile_to_server()
        self._dj_refresh_availability()

    def _dj_remove_availability(self, idx: int):
        """Remove an availability entry by index."""
        entries = self.dj_profile.get("availability", [])
        if not isinstance(entries, list):
            return
        if 0 <= idx < len(entries):
            entries.pop(idx)
            self.save_settings()
            self._dj_sync_profile_to_server()
            self._dj_refresh_availability()

    def _dj_update_availability(self, idx: int, key: str, value: str):
        """Update a field on an availability entry."""
        entries = self.dj_profile.get("availability", [])
        if not isinstance(entries, list):
            return
        if 0 <= idx < len(entries):
            entries[idx][key] = value
            self.save_settings()
            self._dj_sync_profile_to_server()

    def _dj_refresh_availability(self):
        """Rebuild the availability list UI inside the scroll container."""
        container = "dj_avail_scroll"
        if not dpg.does_item_exist(container):
            return
        for child in dpg.get_item_children(container, 1) or []:
            dpg.delete_item(child)

        entries = self.dj_profile.get("availability", [])
        if not isinstance(entries, list):
            return

        for i, entry in enumerate(entries):
            if not isinstance(entry, dict):
                continue
            date_tag = f"avail_date_{i}"
            start_tag = f"avail_start_{i}"
            end_tag = f"avail_end_{i}"
            with dpg.group(parent=container):
                with dpg.group(horizontal=True):
                    add_date_row(
                        date_tag, default=entry.get("date", ""), width=90,
                        callback=lambda val, idx=i: self._dj_update_availability(
                            idx, "date", val),
                    )
                    add_time_row(
                        start_tag, default=entry.get("start", "8:00 PM"), width=80,
                        callback=lambda val, idx=i: self._dj_update_availability(
                            idx, "start", val),
                    )
                    styled_text("to", MUTED)
                    add_time_row(
                        end_tag, default=entry.get("end", "11:00 PM"), width=80,
                        callback=lambda val, idx=i: self._dj_update_availability(
                            idx, "end", val),
                    )
                    add_icon_button(
                        Icon.DELETE,
                        callback=lambda s=None, a=None, idx=i: self._dj_remove_availability(idx),
                    )
                dpg.add_separator()

    # ── DJ genres ──────────────────────────────────────────────────────

    def _dj_add_genre(self):
        """Add a genre tag to the DJ profile."""
        tag = "dj_genre_input"
        if not dpg.does_item_exist(tag):
            return
        genre = dpg.get_value(tag).strip()
        if not genre:
            return
        genres = self.dj_profile.get("genres", [])
        if not isinstance(genres, list):
            genres = []
        if genre.lower() not in [g.lower() for g in genres]:
            genres.append(genre)
            self.dj_profile["genres"] = genres
            self.save_settings()
            self._dj_sync_profile_to_server()
        dpg.set_value(tag, "")
        self._dj_refresh_genres()

    def _dj_remove_genre(self, genre: str):
        """Remove a genre tag from the DJ profile."""
        genres = self.dj_profile.get("genres", [])
        if not isinstance(genres, list):
            return
        genres = [g for g in genres if g.lower() != genre.lower()]
        self.dj_profile["genres"] = genres
        self.save_settings()
        self._dj_sync_profile_to_server()
        self._dj_refresh_genres()

    def _dj_refresh_genres(self):
        """Rebuild the genre tags display."""
        container = "dj_genre_tags"
        if not dpg.does_item_exist(container):
            return
        for child in dpg.get_item_children(container, 1) or []:
            dpg.delete_item(child)
        genres = self.dj_profile.get("genres", [])
        if not isinstance(genres, list) or not genres:
            styled_text("   No genres added.", MUTED, parent=container)
            return
        row = dpg.add_group(horizontal=True, parent=container)
        for genre in genres:
            dpg.add_button(
                label=f"{genre}  x", parent=row, height=20,
                callback=lambda s, a, g=genre: self._dj_remove_genre(g),
            )

    # ── Social link fields ─────────────────────────────────────────

    _SOCIAL_FIELDS = [
        ("TIMELINE",   "https://vrc.tl/event/"),
        ("VRCPOP",     "https://vrcpop.com/event/"),
        ("X",          "https://x.com/"),
        ("IG",         "https://www.instagram.com/p/"),
    ]

    _CLUB_LINK_FIELDS = [
        ("DISCORD",    "https://discord.gg/"),
    ]

    def _on_social_link_changed(self, label: str):
        """Called when any inline social-link input changes."""
        tag = f"social_input_{label.replace(' ', '_')}"
        self.social_links[label] = dpg.get_value(tag).strip()
        self._schedule_update()

    def _on_club_link_changed(self, label: str):
        """Called when a Club-tab link input changes. Auto-saves to settings."""
        tag = f"group_link_{label.replace(' ', '_')}"
        value = dpg.get_value(tag).strip()
        self.persistent_links[label] = {"link": value, "enabled": True}
        self.save_settings()
        self._schedule_update()

    def _sync_social_link_inputs(self):
        """Push self.social_links values into the inline DPG inputs."""
        for label, _ in self._SOCIAL_FIELDS:
            tag = f"social_input_{label.replace(' ', '_')}"
            if dpg.does_item_exist(tag):
                dpg.set_value(tag, self.social_links.get(label, ""))

    def _build_club_tab(self):
        with dpg.child_window(tag="club_tab_inner", border=False,
                              autosize_x=True, height=-1):
            styled_text("   CLUB LINKS", HEADER)
            styled_text("   Shared across all events.", MUTED)
            dpg.add_spacer(height=4)
            _LABEL_W = 62
            with dpg.table(header_row=False, borders_innerH=False,
                           borders_innerV=False, borders_outerH=False,
                           borders_outerV=False, pad_outerX=False):
                dpg.add_table_column(init_width_or_weight=_LABEL_W, width_fixed=True)
                dpg.add_table_column(width_stretch=True)
                for label, hint in self._CLUB_LINK_FIELDS:
                    tag_key = label.replace(' ', '_')
                    p = self.persistent_links.get(label, {})
                    with dpg.table_row():
                        styled_text(f"   {label}", LABEL)
                        dpg.add_input_text(
                            tag=f"group_link_{tag_key}",
                            default_value=p.get("link", "") if isinstance(p, dict) else "",
                            hint=hint, width=-1,
                            callback=lambda s, a, u=label: self._on_club_link_changed(u),
                        )

            dpg.add_separator()
            dpg.add_spacer(height=4)

            # ── VRChat group verification ─────────────────────────
            with dpg.group(tag="vrchat_verify_section"):
                styled_text("   VRCHAT GROUP", HEADER)
                styled_text("   Verify ownership of your VRChat group.", MUTED)
                dpg.add_spacer(height=4)
                with dpg.group(tag="vrchat_linked_info", show=False):
                    styled_text("   Linked group:", LABEL,
                                tag="vrchat_linked_name")
                    styled_text("   Members: —", MUTED,
                                tag="vrchat_linked_members")
                    styled_text("   URL: —", MUTED,
                                tag="vrchat_linked_url")
                    dpg.add_spacer(height=4)
                add_primary_button(
                    "Verify VRChat Group",
                    tag="vrchat_verify_btn", width=-1,
                    callback=lambda: self._open_vrchat_verify_popup(),
                )
                dpg.add_spacer(height=2)
                styled_text("", HINT, tag="vrchat_verify_status")

            dpg.add_separator()
            dpg.add_spacer(height=4)

            # ── Bookings section ──────────────────────────────────
            styled_text("   BOOK A DJ", HEADER)
            styled_text("   Send a booking request to a DJ.", MUTED)
            dpg.add_spacer(height=4)
            with dpg.table(header_row=False, borders_innerH=False,
                           borders_innerV=False, borders_outerH=False,
                           borders_outerV=False, pad_outerX=False):
                dpg.add_table_column(init_width_or_weight=_LABEL_W, width_fixed=True)
                dpg.add_table_column(width_stretch=True)
                with dpg.table_row():
                    styled_text("   DJ", LABEL)
                    dpg.add_input_text(
                        tag="booking_dj_name", hint="DJ name...", width=-1,
                    )
                with dpg.table_row():
                    styled_text("   EVENT", LABEL)
                    dpg.add_input_text(
                        tag="booking_event_title", hint="Event title...", width=-1,
                    )
                with dpg.table_row():
                    styled_text("   DATE", LABEL)
                    add_date_row("booking_event_date")
                with dpg.table_row():
                    styled_text("   TIME", LABEL)
                    add_time_row("booking_start_time", default="8:00 PM")
                with dpg.table_row():
                    styled_text("   MINS", LABEL)
                    dpg.add_input_int(
                        tag="booking_duration",
                        default_value=60, min_value=15, max_value=480,
                        min_clamped=True, max_clamped=True, width=-1,
                    )
                with dpg.table_row():
                    styled_text("   MSG", LABEL)
                    dpg.add_input_text(
                        tag="booking_message", hint="Optional message...",
                        width=-1, multiline=True, height=50,
                    )

            dpg.add_spacer(height=4)
            add_primary_button(
                "Send Booking Request", tag="booking_send_btn", width=-1,
                callback=lambda: self._send_booking_request(),
            )
            dpg.add_spacer(height=2)
            styled_text("", HINT, tag="booking_status_label")
            dpg.add_separator()
            dpg.add_spacer(height=4)

            # ── Sent bookings ─────────────────────────────────────
            with dpg.group(horizontal=True):
                styled_text("   SENT BOOKINGS", HEADER)
                add_icon_button(
                    Icon.REFRESH,
                    callback=lambda: self._refresh_group_bookings(),
                )
            dpg.add_spacer(height=4)
            with dpg.child_window(tag="group_bookings_scroll", height=-1,
                                  border=False, autosize_x=True):
                pass

    # ── Bookings tab ──────────────────────────────────────────────────────

    def _build_bookings_tab(self):
        with dpg.child_window(tag="bookings_tab_inner", border=False,
                              autosize_x=True, height=-1):
            styled_text("   FIND DJs", HEADER)
            styled_text("   Browse DJs by availability and genre.", MUTED)
            dpg.add_spacer(height=4)

            # ── Filters ───────────────────────────────────────────────
            _LABEL_W = 62
            with dpg.table(header_row=False, borders_innerH=False,
                           borders_innerV=False, borders_outerH=False,
                           borders_outerV=False, pad_outerX=False):
                dpg.add_table_column(init_width_or_weight=_LABEL_W, width_fixed=True)
                dpg.add_table_column(width_stretch=True)
                with dpg.table_row():
                    styled_text("   DATE", LABEL)
                    add_date_row("bookings_filter_date")
                with dpg.table_row():
                    styled_text("   TIME", LABEL)
                    add_time_row("bookings_filter_start", default="8:00 PM")
                with dpg.table_row():
                    styled_text("   GENRE", LABEL)
                    dpg.add_input_text(
                        tag="bookings_genre_search",
                        hint="Filter by genre...", width=-1,
                        callback=lambda s, a: self._bookings_apply_filters(),
                    )

            dpg.add_spacer(height=4)
            with dpg.group(horizontal=True):
                add_primary_button(
                    "Search", tag="bookings_search_btn", width=-1,
                    callback=lambda: self._bookings_fetch_djs(),
                )
            dpg.add_spacer(height=2)
            styled_text("", HINT, tag="bookings_status_label")

            dpg.add_separator()
            dpg.add_spacer(height=4)

            # ── DJ results scroll ─────────────────────────────────────
            with dpg.child_window(tag="bookings_dj_scroll", height=-1,
                                  border=False, autosize_x=True):
                styled_text("   Press Search to load DJs.", MUTED)

    # ── VRChat group logic ───────────────────────────────────────────────

    def _open_vrchat_verify_popup(self):
        """Open a popup to verify VRChat account ownership via bio code."""
        win_tag = "vrchat_verify_win"
        if dpg.does_item_exist(win_tag):
            dpg.focus_item(win_tag)
            return

        discord_id = getattr(self, "_oauth", None)
        if discord_id and hasattr(discord_id, "user_info"):
            discord_id = (discord_id.user_info or {}).get("id", "")
        if not discord_id:
            dpg.set_value("vrchat_verify_status", "   Sign in with Discord first.")
            return
        if not self.api.base_url:
            dpg.set_value("vrchat_verify_status", "   Server not configured.")
            return

        # Generate a unique verification code
        code = f"LB-{secrets.token_hex(4).upper()}"

        with dpg.window(
            tag=win_tag, label="Verify VRChat Group",
            modal=True, autosize=True, no_resize=True, no_scrollbar=True,
            on_close=lambda: dpg.delete_item(win_tag),
            min_size=(420, 0),
        ):
            styled_text("  VRCHAT GROUP VERIFICATION", HEADER)
            dpg.add_spacer(height=4)

            styled_text("  Step 1:  Copy this code", LABEL)
            dpg.add_input_text(
                default_value=code, readonly=True, width=380,
                tag="vrc_verify_code_display",
            )
            dpg.add_spacer(height=4)

            styled_text("  Step 2:  Paste it anywhere in your VRChat bio", LABEL)
            styled_text("  Open VRChat > Profile > Edit Bio > paste the code\n"
                        "  anywhere, then save.", MUTED)
            dpg.add_spacer(height=4)

            styled_text("  Step 3:  Enter your VRChat display name and verify",
                        LABEL)
            dpg.add_input_text(
                tag="vrc_verify_username",
                hint="Your VRChat display name...",
                width=380,
            )
            dpg.add_spacer(height=4)
            add_primary_button(
                "Verify Bio",
                tag="vrc_verify_lookup_btn", width=380,
                callback=lambda: self._vrchat_verify_bio(
                    code, discord_id, win_tag),
            )
            dpg.add_spacer(height=4)
            styled_text("", HINT, tag="vrc_verify_popup_status")

            # Container for group list (populated after verification)
            with dpg.group(tag="vrc_verify_groups_list"):
                pass

    def _vrchat_verify_bio(self, code: str, discord_id: str, win_tag: str):
        """Verify the user's VRChat bio contains the code, then show groups."""
        username = dpg.get_value("vrc_verify_username").strip()
        if not username:
            dpg.set_value("vrc_verify_popup_status",
                          "  Enter your display name first.")
            return

        dpg.set_value("vrc_verify_popup_status",
                      "  Checking your VRChat bio...")
        dpg.configure_item("vrc_verify_lookup_btn", enabled=False)

        def _do():
            try:
                from src.backend.services.api_client import APIError
                data = self.api.verify_vrchat_bio(username, code)
                owned = data.get("owned_groups", [])
                display_name = data.get("vrchat_display_name", username)

                def _show():
                    # Clear previous group buttons
                    if dpg.does_item_exist("vrc_verify_groups_list"):
                        for child in dpg.get_item_children(
                                "vrc_verify_groups_list", 1) or []:
                            dpg.delete_item(child)

                    if not owned:
                        dpg.set_value(
                            "vrc_verify_popup_status",
                            f"  Verified! But no owned groups found "
                            f"for '{display_name}'.")
                        dpg.configure_item("vrc_verify_lookup_btn",
                                           enabled=True)
                        return

                    dpg.set_value(
                        "vrc_verify_popup_status",
                        f"  Verified {display_name}! "
                        f"Select a group to link:")

                    with dpg.group(parent="vrc_verify_groups_list"):
                        dpg.add_spacer(height=4)
                        for g in owned:
                            gid = g["group_id"]
                            name = g["group_name"] or gid
                            members = g.get("member_count", 0)
                            label = f"  {name}  ({members} members)"

                            def _make_cb(_gid=gid, _did=discord_id,
                                         _wt=win_tag):
                                return lambda: self._vrchat_select_group(
                                    _gid, _did, _wt)

                            add_primary_button(
                                label, width=380,
                                callback=_make_cb(),
                            )
                            dpg.add_spacer(height=2)

                    dpg.configure_item("vrc_verify_lookup_btn", enabled=True)

                self._work_queue.put(_show)

            except APIError as exc:
                def _err():
                    dpg.set_value("vrc_verify_popup_status",
                                  f"  {exc.detail}")
                    dpg.configure_item("vrc_verify_lookup_btn", enabled=True)
                self._work_queue.put(_err)
            except Exception:
                def _err():
                    dpg.set_value("vrc_verify_popup_status",
                                  "  Connection failed.")
                    dpg.configure_item("vrc_verify_lookup_btn", enabled=True)
                self._work_queue.put(_err)

        threading.Thread(target=_do, daemon=True).start()

    def _vrchat_select_group(self, group_id: str, discord_id: str,
                             win_tag: str):
        """User selected an owned group — link it."""
        dpg.set_value("vrc_verify_popup_status", "  Linking group...")

        def _do():
            try:
                from src.backend.services.api_client import APIError
                data = self.api.verify_vrchat_group(group_id, discord_id)
                group_name = data.get("group_name", group_id)

                def _ok():
                    # Show success in the popup
                    if dpg.does_item_exist("vrc_verify_groups_list"):
                        for child in dpg.get_item_children(
                                "vrc_verify_groups_list", 1) or []:
                            dpg.delete_item(child)
                    dpg.set_value(
                        "vrc_verify_popup_status",
                        f"  Successfully linked to {group_name}!")
                    if dpg.does_item_exist("vrc_verify_lookup_btn"):
                        dpg.configure_item("vrc_verify_lookup_btn",
                                           show=False)

                    # Update the main UI
                    self._show_vrchat_group_info(data)
                    dpg.set_value("vrchat_verify_status",
                                  f"   Linked to {group_name}")

                    # Auto-close after a moment
                    def _close():
                        import time
                        time.sleep(1.5)
                        def _del():
                            if dpg.does_item_exist(win_tag):
                                dpg.delete_item(win_tag)
                        self._work_queue.put(_del)
                    threading.Thread(target=_close, daemon=True).start()

                self._work_queue.put(_ok)
            except APIError as exc:
                def _err():
                    dpg.set_value("vrc_verify_popup_status",
                                  f"  {exc.detail}")
                self._work_queue.put(_err)
            except Exception:
                def _err():
                    dpg.set_value("vrc_verify_popup_status",
                                  "  Connection failed.")
                self._work_queue.put(_err)

        threading.Thread(target=_do, daemon=True).start()

    def _load_vrchat_group_info(self):
        """Load existing VRChat group link from the server (if signed in)."""
        discord_id = getattr(self, "_oauth", None)
        if discord_id and hasattr(discord_id, "user_info"):
            discord_id = (discord_id.user_info or {}).get("id", "")
        if not discord_id or not self.api.base_url:
            return

        def _do():
            try:
                data = self.api.get_vrchat_group(discord_id)
                if data and data.get("group_name"):
                    self._work_queue.put(lambda: self._show_vrchat_group_info(data))
            except Exception:
                pass

        threading.Thread(target=_do, daemon=True).start()

    def _show_vrchat_group_info(self, data: dict):
        """Update the VRChat linked-group display and auto-set the VRC GROUP link."""
        name = data.get("group_name", "Unknown")
        members = data.get("member_count", "—")
        short_code = data.get("short_code", "")

        # Auto-set the VRC GROUP persistent link
        if short_code:
            url = f"https://vrc.group/{short_code}"
            self.persistent_links["VRC GROUP"] = {"link": url, "enabled": True}
            self.save_settings()
            self._schedule_update()
        elif not short_code and data.get("group_id"):
            url = f"https://vrchat.com/home/group/{data['group_id']}"
            self.persistent_links["VRC GROUP"] = {"link": url, "enabled": True}
            self.save_settings()
            self._schedule_update()
        else:
            url = ""

        if dpg.does_item_exist("vrchat_linked_name"):
            dpg.set_value("vrchat_linked_name", f"   {name}")
        if dpg.does_item_exist("vrchat_linked_members"):
            dpg.set_value("vrchat_linked_members", f"   Members: {members}")
        if dpg.does_item_exist("vrchat_linked_url"):
            dpg.set_value("vrchat_linked_url", f"   URL: {url}" if url else "   URL: —")
        if dpg.does_item_exist("vrchat_linked_info"):
            dpg.configure_item("vrchat_linked_info", show=True)

    # ── Booking logic ─────────────────────────────────────────────────────

    def _send_booking_request(self):
        """Send a booking request to the server."""
        dj_name = dpg.get_value("booking_dj_name").strip()
        if not dj_name:
            dpg.set_value("booking_status_label", "   DJ name is required.")
            return
        if not self.api.base_url:
            dpg.set_value("booking_status_label", "   Server URL not configured.")
            return

        event_title = dpg.get_value("booking_event_title").strip()
        event_date = dpg.get_value("booking_event_date").strip()
        start_time = dpg.get_value("booking_start_time")
        duration = dpg.get_value("booking_duration")
        message = dpg.get_value("booking_message").strip()

        # Use group name from settings
        group_name = ""
        for label in ("DISCORD", "VRC GROUP"):
            p = self.persistent_links.get(label, {})
            if isinstance(p, dict) and p.get("link"):
                group_name = p["link"]
                break
        # Try event title as group identifier if no link
        if not group_name:
            group_name = dpg.get_value("event_title_input").strip() if dpg.does_item_exist("event_title_input") else ""

        dpg.set_value("booking_status_label", "   Sending...")
        dpg.configure_item("booking_send_btn", enabled=False)

        def _do():
            try:
                from src.backend.services.api_client import APIError
                result = self.api.create_booking(
                    dj_name=dj_name,
                    group_name=group_name,
                    event_title=event_title,
                    event_date=event_date,
                    start_time=start_time,
                    duration=duration,
                    message=message,
                )

                def _on_ok():
                    dpg.set_value("booking_status_label",
                                  f"   Booking #{result['id']} sent! Status: pending")
                    dpg.configure_item("booking_send_btn", enabled=True)
                    self._refresh_group_bookings()

                self._work_queue.put(_on_ok)
            except APIError as exc:
                def _on_err():
                    dpg.set_value("booking_status_label", f"   {exc.detail}")
                    dpg.configure_item("booking_send_btn", enabled=True)
                self._work_queue.put(_on_err)
            except Exception:
                def _on_err():
                    dpg.set_value("booking_status_label", "   Connection failed.")
                    dpg.configure_item("booking_send_btn", enabled=True)
                self._work_queue.put(_on_err)

        threading.Thread(target=_do, daemon=True).start()

    def _refresh_group_bookings(self):
        """Fetch and display sent bookings for this group."""
        if not self.api.base_url:
            return

        group_name = ""
        for label in ("DISCORD", "VRC GROUP"):
            p = self.persistent_links.get(label, {})
            if isinstance(p, dict) and p.get("link"):
                group_name = p["link"]
                break
        if not group_name:
            return

        def _do():
            try:
                bookings = self.api.list_group_bookings(group_name)

                def _on_ok():
                    self._render_group_bookings(bookings)

                self._work_queue.put(_on_ok)
            except Exception:
                log.debug("Failed to refresh group bookings", exc_info=True)

        threading.Thread(target=_do, daemon=True).start()

    def _render_group_bookings(self, bookings: list[dict]):
        """Render booking cards in the group bookings scroll."""
        container = "group_bookings_scroll"
        if not dpg.does_item_exist(container):
            return
        for child in dpg.get_item_children(container, 1) or []:
            dpg.delete_item(child)

        if not bookings:
            styled_text("   No bookings sent yet.", MUTED, parent=container)
            return

        _STATUS_COLORS = {
            "pending": MUTED,
            "accepted": LABEL,
            "declined": HINT,
        }

        for b in bookings:
            with dpg.group(parent=container):
                with dpg.group(horizontal=True):
                    styled_text(f"   #{b['id']}  ", LABEL)
                    styled_text(b.get("dj_name", ""), BODY)
                    styled_text(
                        f"  [{b.get('status', 'pending')}]",
                        _STATUS_COLORS.get(b.get("status"), MUTED),
                    )
                if b.get("event_title"):
                    styled_text(f"      {b['event_title']}  {b.get('event_date', '')}", MUTED)
                dpg.add_separator()

    # ── Right panel ───────────────────────────────────────────────────────

    def _build_right_panel(self):
        # ── Tab bar wrapped in a resizable container ──────────────────────
        with dpg.child_window(tag="right_tabs_content", height=360,
                              border=False, autosize_x=True, no_scrollbar=True):
            with dpg.tab_bar(tag="right_tabs"):
                with dpg.tab(label="Lineup"):
                    styled_text("   TIMESLOTS  ", HEADER)

                    # ── Slots scroll area ─────────────────────────────────
                    with dpg.child_window(tag="slots_scroll", height=-1,
                                          border=True, autosize_x=True,
                                          payload_type="DJ_CARD",
                                          drop_callback=lambda s, a, u=None: self._drop_dj_on_lineup(s, a)):
                        pass  # populated by slot_manager

                with dpg.tab(label="Discord", tag="DiscordTab"):
                    dpg.add_spacer(height=4)
                    with dpg.group(horizontal=True):
                        styled_text("  DISCORD BOT", HEADER)
                        add_icon_button(
                            Icon.SETTINGS, tag="discord_settings_btn",
                            callback=lambda: self._toggle_discord_settings_drawer(),
                        )

                    # ── Discord settings drawer (inline, hidden) ─────────
                    with dpg.child_window(tag="discord_settings_drawer", height=260,
                                          border=True, autosize_x=True, show=False):
                        self._build_discord_settings_drawer()
                    self._discord_settings_drawer_open = False

                    with dpg.group(horizontal=True):
                        add_primary_button(
                            "Connect", tag="discord_connect_btn", width=120,
                            callback=lambda: self._connect_discord_bot(),
                        )
                        dpg.add_button(
                            tag="discord_disconnect_btn", label="Disconnect", width=120,
                            callback=lambda: self._disconnect_discord_bot(),
                        )
                    styled_text("  Not connected", MUTED, tag="discord_status_text")
                    dpg.add_spacer(height=4)

                    styled_text("  EMBED IMAGE", LABEL)
                    with dpg.group(horizontal=True):
                        dpg.add_input_text(
                            tag="embed_image_input",
                            default_value=getattr(self, "discord_embed_image", ""),
                            hint="Image URL or path...",
                            width=-1,
                            on_enter=True,
                            callback=lambda s, a, u=None: self._save_embed_image(),
                        )
                        add_primary_button(
                            "Browse", tag="embed_image_browse_btn",
                            callback=lambda: self._browse_embed_image(),
                        )
                        dpg.add_button(
                            tag="embed_image_clear_btn", label="Clear",
                            callback=lambda: self._clear_embed_image(),
                        )
                    dpg.add_spacer(height=4)

                    styled_text("  POST OUTPUT", LABEL)
                    with dpg.group(horizontal=True):
                        add_primary_button(
                            "Events", tag="discord_post_events_btn",
                            callback=lambda: self._post_to_discord("events"),
                        )
                        add_primary_button(
                            "Popup", tag="discord_post_popup_btn",
                            callback=lambda: self._post_to_discord("popup"),
                        )
                        add_primary_button(
                            "Signups", tag="discord_post_signups_btn",
                            callback=lambda: self._post_to_discord("signups"),
                        )
                    dpg.add_spacer(height=4)

                    styled_text("  SCHEDULE", LABEL)
                    with dpg.group(horizontal=True):
                        dpg.add_input_text(
                            tag="discord_schedule_datetime",
                            default_value="",
                            hint="YYYY-MM-DD HH:MM",
                            width=-80,
                        )
                        btn = dpg.add_button(
                            label=Icon.SCHEDULE, width=32, height=20,
                            callback=lambda: self._open_schedule_picker(),
                        )
                        bind_icon_font(btn)
                        dpg.add_combo(
                            tag="discord_schedule_channel",
                            items=["events", "popup", "signups"],
                            default_value="events",
                            width=70,
                        )
                    with dpg.group(horizontal=True):
                        add_primary_button(
                            "Schedule", tag="discord_schedule_btn", width=-60,
                            callback=lambda: self._schedule_discord_post(),
                        )
                        dpg.add_button(
                            label="Pending...", tag="discord_pending_btn",
                            width=55,
                            callback=lambda: self._open_pending_popup(),
                        )



        # ── Draggable resize handle (shared across all tabs) ──────────────
        dpg.add_button(tag="resize_handle", label="", width=-1, height=4)
        dpg.bind_item_theme("resize_handle", "resize_handle_theme")
        with dpg.item_handler_registry(tag="resize_handle_hr"):
            dpg.add_item_clicked_handler(button=dpg.mvMouseButton_Left,
                                         callback=self._resize_handle_click)
        dpg.bind_item_handler_registry("resize_handle", "resize_handle_hr")
        with dpg.handler_registry(tag="resize_global_hr"):
            dpg.add_mouse_drag_handler(button=dpg.mvMouseButton_Left,
                                       callback=self._resize_handle_drag)
            dpg.add_mouse_release_handler(button=dpg.mvMouseButton_Left,
                                          callback=self._resize_handle_release)

        # ── Output preview (always visible, below tabs) ───────────────────
        styled_text("   OUTPUT", HEADER)
        with dpg.table(header_row=False, borders_innerH=False, borders_innerV=False,
                       borders_outerH=False, borders_outerV=False, pad_outerX=False):
            for _ in range(4):
                dpg.add_table_column()
            with dpg.table_row():
                dpg.add_button(tag="fmt_discord", label="Discord", width=-1,
                               callback=lambda: self.toggle_format())
                dpg.add_button(tag="fmt_plain",   label="Plain",   width=-1,
                               callback=lambda: self.set_plain_text())
                dpg.add_button(tag="fmt_quest",   label="Quest",   width=-1,
                               callback=lambda: self.set_quest_view())
                dpg.add_button(tag="fmt_pc",      label="PC",      width=-1,
                               callback=lambda: self.set_pc_view())
        dpg.add_button(tag="fmt_times", label="Times on", width=-1,
                       callback=lambda: self._toggle_times())

        with dpg.child_window(tag="output_text_scroll", height=-30,
                              autosize_x=True, horizontal_scrollbar=True):
            dpg.add_input_text(
                tag="output_text",
                multiline=True, readonly=False,
                tab_input=True,
                width=-1, height=-1,
            )

        with dpg.table(header_row=False, borders_innerH=False, borders_innerV=False,
                       borders_outerH=False, borders_outerV=False, pad_outerX=False):
            for _ in range(2):
                dpg.add_table_column()
            with dpg.table_row():
                dpg.add_button(tag="refresh_output_btn", label="Refresh", width=-1,
                               callback=lambda: self.update_output())
                add_icon_button(Icon.COPY, tag="copy_output_btn", width=-1, height=20, is_primary=True, callback=lambda: self._copy_output())

    # ── Helpers ───────────────────────────────────────────────────────────

    def _apply_local_mode_visibility(self):
        """Hide server-dependent tabs/sections when running in local mode."""
        is_local = getattr(self, "_local_mode", False)
        for tag in ("DJ", "DiscordTab", "vrchat_verify_section"):
            if dpg.does_item_exist(tag):
                dpg.configure_item(tag, show=not is_local)
        self._update_auth_card()

    def _update_auth_card(self):
        """Refresh the auth card button label to reflect sign-in state."""
        if not dpg.does_item_exist("auth_card_btn"):
            return
        if self._oauth.is_signed_in:
            user = self._oauth.user_info or {}
            name = user.get("username", "Unknown")
            dpg.configure_item("auth_card_btn", label=name)
        else:
            dpg.configure_item("auth_card_btn", label="Local")

    def _load_discord_avatar(self, user: dict):
        """Download and display the user's Discord avatar in the auth card."""
        user_id = user.get("id", "")
        avatar_hash = user.get("avatar", "")
        if not user_id or not avatar_hash:
            return

        url = f"https://cdn.discordapp.com/avatars/{user_id}/{avatar_hash}.png?size=32"

        def _fetch():
            try:
                import urllib.request
                from PIL import Image

                req = urllib.request.Request(url, headers={"User-Agent": "LineupBuilder/1.2"})
                with urllib.request.urlopen(req, timeout=10) as resp:
                    data = resp.read()
                img = Image.open(io.BytesIO(data)).convert("RGBA").resize((16, 16))
                # Normalise to 0–1 floats for DPG
                pixels = [v / 255.0 for v in img.tobytes()]

                def _apply():
                    if dpg.does_item_exist("auth_avatar_tex"):
                        dpg.delete_item("auth_avatar_tex")
                    if dpg.does_alias_exist("auth_avatar_tex"):
                        dpg.remove_alias("auth_avatar_tex")
                    with dpg.texture_registry():
                        dpg.add_static_texture(16, 16, pixels, tag="auth_avatar_tex")
                    if dpg.does_item_exist("auth_avatar_img"):
                        dpg.configure_item("auth_avatar_img", texture_tag="auth_avatar_tex", show=True)
                self._work_queue.put(_apply)
            except Exception as exc:
                log.debug("Failed to load Discord avatar: %s", exc)

        threading.Thread(target=_fetch, daemon=True).start()

    def _build_account_drawer(self):
        """Build the account drawer contents (created once, shown/hidden)."""
        dpg.add_spacer(height=4)

        # Avatar + status row
        with dpg.group(horizontal=True):
            dpg.add_image(
                "auth_avatar_tex", tag="account_avatar_img",
                width=16, height=16, show=False,
            )
            styled_text("  Not signed in", MUTED, tag="account_status_text")
        dpg.add_spacer(height=6)

        # Sign-in button
        add_primary_button(
            "Sign in with Discord",
            tag="account_signin_btn",
            width=-1,
            callback=lambda: self._sign_in_from_app(),
        )

        # Sign-out button (hidden when not signed in)
        add_danger_button(
            "Sign Out",
            tag="account_signout_btn",
            width=-1,
            callback=lambda: self._sign_out_from_drawer(),
        )

        # Local-mode toggle
        dpg.add_checkbox(
            tag="account_local_mode_cb",
            label="Local Mode",
            default_value=getattr(self, "_local_mode", False),
            callback=lambda s, a: self._toggle_local_mode_from_drawer(a),
        )
        dpg.add_spacer(height=2)
        styled_text("", ERROR, tag="account_error_label")

    def _toggle_account_drawer(self):
        """Toggle the account drawer open/closed."""
        self._account_drawer_open = not self._account_drawer_open
        show = self._account_drawer_open
        dpg.configure_item("account_drawer", show=show)
        # Shrink tabs wrapper to make room for the drawer
        offset = self._AUTH_BTN_HEIGHT + (self._DRAWER_HEIGHT if show else 0)
        dpg.configure_item("left_tabs_wrapper", height=-offset)
        if show:
            self._refresh_account_drawer()

    def _sign_out_from_drawer(self):
        """Sign out and update the drawer + auth card."""
        self._local_mode = True
        self._oauth = type(self._oauth)()
        self.discord_oauth = {}
        self.save_settings()
        self._apply_local_mode_visibility()
        self._refresh_account_drawer()

    def _toggle_local_mode_from_drawer(self, value):
        """Toggle local mode from the drawer checkbox."""
        self._local_mode = bool(value)
        self._apply_local_mode_visibility()
        self._refresh_account_drawer()

    def _refresh_account_drawer(self):
        """Update the account drawer to reflect current sign-in status."""
        if not dpg.does_item_exist("account_status_text"):
            return
        signed_in = self._oauth.is_signed_in
        if signed_in:
            user = self._oauth.user_info or {}
            name = user.get("username", "Unknown")
            dpg.set_value("account_status_text", f"  Signed in as {name}")
            dpg.configure_item("account_signin_btn", show=False)
            dpg.configure_item("account_signout_btn", show=True)
            dpg.configure_item("account_local_mode_cb", show=False)
            dpg.set_value("account_error_label", "")
            if dpg.does_item_exist("account_avatar_img"):
                dpg.configure_item("account_avatar_img", show=True)
            self._load_discord_avatar(user)
        else:
            dpg.set_value("account_status_text", "  Not signed in")
            dpg.configure_item("account_signin_btn", show=True)
            dpg.configure_item("account_signout_btn", show=False)
            dpg.configure_item("account_local_mode_cb", show=True)
            if dpg.does_item_exist("account_avatar_img"):
                dpg.configure_item("account_avatar_img", show=False)
        self._update_auth_card()

    def _save_discord_credentials(self):
        """Persist client ID from the input field."""
        if dpg.does_item_exist("discord_client_id"):
            self.discord_client_id = dpg.get_value("discord_client_id").strip()
        self.save_settings()

    def _invite_discord_bot(self):
        """Open the bot invite URL in the browser."""
        client_id = getattr(self, "discord_client_id", "")
        if dpg.does_item_exist("discord_client_id"):
            client_id = dpg.get_value("discord_client_id").strip()
        if not client_id:
            self._set_discord_status("No Client ID provided.")
            return
        invite_url = (
            f"https://discord.com/oauth2/authorize"
            f"?client_id={client_id}&permissions=67584&scope=bot"
        )
        import webbrowser
        webbrowser.open(invite_url)

    def _save_embed_image(self):
        """Persist the embed image path/URL from the input field."""
        if dpg.does_item_exist("embed_image_input"):
            self.discord_embed_image = dpg.get_value("embed_image_input").strip()
            self.save_settings()

    def _clear_embed_image(self):
        """Clear the embed image."""
        self.discord_embed_image = ""
        if dpg.does_item_exist("embed_image_input"):
            dpg.set_value("embed_image_input", "")
        self.save_settings()

    def _browse_embed_image(self):
        """Open a file dialog to pick a local image."""
        fd_tag = "embed_image_file_dialog"
        if dpg.does_item_exist(fd_tag):
            dpg.delete_item(fd_tag)

        def _on_file_selected(_sender, app_data, _user):
            selections = app_data.get("selections", {})
            path = list(selections.values())[0] if selections else app_data.get("file_path_name", "")
            if path:
                if dpg.does_item_exist("embed_image_input"):
                    dpg.set_value("embed_image_input", path)
                self.discord_embed_image = path
                self.save_settings()

        with dpg.file_dialog(
            tag=fd_tag,
            directory_selector=False,
            show=True,
            callback=_on_file_selected,
            width=600, height=400,
        ):
            dpg.add_file_extension(".png", color=(0, 255, 100, 255))
            dpg.add_file_extension(".jpg", color=(0, 255, 100, 255))
            dpg.add_file_extension(".jpeg", color=(0, 255, 100, 255))
            dpg.add_file_extension(".gif", color=(0, 255, 100, 255))
            dpg.add_file_extension(".webp", color=(0, 255, 100, 255))
            dpg.add_file_extension(".*", color=(150, 150, 150, 255))

    def _build_discord_settings_drawer(self):
        """Populate the Discord settings drawer with config fields."""
        channels = getattr(self, "discord_channels", {})

        styled_text("  BOT CONFIGURATION", HEADER)
        dpg.add_spacer(height=4)

        styled_text("  Client ID", LABEL)
        dpg.add_input_text(
            tag="discord_client_id",
            default_value=getattr(self, "discord_client_id", ""),
            hint="Application Client ID...",
            width=-1,
            callback=lambda s, a, u=None: self._save_discord_credentials(),
        )
        dpg.add_spacer(height=2)
        styled_text("  Bot Token", LABEL)
        dpg.add_input_text(
            tag="discord_bot_token",
            default_value=getattr(self, "discord_bot_token", ""),
            hint="Paste bot token here...",
            password=True,
            width=-1,
            callback=lambda s, a, u=None: self._save_bot_token(),
        )

        dpg.add_spacer(height=4)
        add_primary_button(
            "Invite Bot to Server", width=-1,
            callback=lambda: self._invite_discord_bot(),
        )

        dpg.add_spacer(height=8)
        styled_text("  CHANNELS", HEADER)
        dpg.add_spacer(height=4)

        styled_text("  Events Channel", LABEL)
        dpg.add_combo(
            tag="discord_events_channel",
            items=[], default_value=self._channel_display(channels.get("events", "")),
            width=-1,
            callback=lambda s, a, u=None: self._save_discord_channels(),
        )
        styled_text("  Popup Channel", LABEL)
        dpg.add_combo(
            tag="discord_popup_channel",
            items=[], default_value=self._channel_display(channels.get("popup", "")),
            width=-1,
            callback=lambda s, a, u=None: self._save_discord_channels(),
        )
        styled_text("  Signups Channel", LABEL)
        dpg.add_combo(
            tag="discord_signups_channel",
            items=[], default_value=self._channel_display(channels.get("signups", "")),
            width=-1,
            callback=lambda s, a, u=None: self._save_discord_channels(),
        )

        dpg.add_spacer(height=4)
        add_primary_button(
            "Refresh Channels", tag="discord_refresh_channels_btn", width=-1,
            callback=lambda: self._fetch_discord_channels(),
        )

    def _toggle_discord_settings_drawer(self):
        """Toggle the Discord settings drawer open/closed."""
        self._discord_settings_drawer_open = not self._discord_settings_drawer_open
        show = self._discord_settings_drawer_open
        dpg.configure_item("discord_settings_drawer", show=show)
        if show and self._discord_service.is_running:
            self._fetch_discord_channels()

    def _save_discord_channels(self):
        """Read Discord channel combo selections and persist channel IDs."""
        channel_map = getattr(self, "_discord_channel_map", {})
        result = {}
        for key in ("events", "popup", "signups"):
            tag = f"discord_{key}_channel"
            if dpg.does_item_exist(tag):
                display = dpg.get_value(tag).strip()
                # Resolve display string back to channel ID
                result[key] = str(channel_map.get(display, ""))
            else:
                result[key] = getattr(self, "discord_channels", {}).get(key, "")
        self.discord_channels = result
        self.save_settings()

    def _channel_display(self, channel_id_str: str) -> str:
        """Return the display string for a saved channel ID, or empty."""
        channel_map = getattr(self, "_discord_channel_map", {})
        # Reverse lookup: find display string whose value matches the ID
        for display, cid in channel_map.items():
            if str(cid) == channel_id_str:
                return display
        return ""

    def _fetch_discord_channels(self):
        """Ask the bot to list all visible text channels."""
        if not self._discord_service.is_running:
            self._set_discord_status("Connect bot first to fetch channels.")
            return
        self._discord_service.get_text_channels(
            on_result=lambda channels: self._queue_on_main(
                lambda: self._on_channels_fetched(channels)),
            on_error=lambda e: self._set_discord_status(f"Error: {e}"),
        )

    def _on_channels_fetched(self, channels: list[tuple[str, str, int]]):
        """Populate channel combos with fetched data."""
        # Build display strings and a reverse map
        items = []
        channel_map: dict[str, int] = {}
        for guild_name, ch_name, ch_id in channels:
            display = f"#{ch_name}  ({guild_name})"
            items.append(display)
            channel_map[display] = ch_id

        self._discord_channel_map = channel_map

        saved = getattr(self, "discord_channels", {})
        for key in ("events", "popup", "signups"):
            tag = f"discord_{key}_channel"
            if dpg.does_item_exist(tag):
                dpg.configure_item(tag, items=items)
                # Restore previously selected channel by ID
                saved_id = saved.get(key, "")
                current = ""
                for display, cid in channel_map.items():
                    if str(cid) == saved_id:
                        current = display
                        break
                dpg.set_value(tag, current)

    def _save_bot_token(self):
        """Persist the bot token from the input field."""
        if dpg.does_item_exist("discord_bot_token"):
            self.discord_bot_token = dpg.get_value("discord_bot_token").strip()
            self.save_settings()

    def _set_discord_status(self, text: str):
        """Update the Discord status label (thread-safe via work queue)."""
        def _update():
            if dpg.does_item_exist("discord_status_text"):
                dpg.set_value("discord_status_text", f"  {text}")
        self._queue_on_main(_update)

    def _connect_discord_bot(self):
        """Start the Discord bot with the saved token."""
        token = getattr(self, "discord_bot_token", "")
        if dpg.does_item_exist("discord_bot_token"):
            token = dpg.get_value("discord_bot_token").strip()
            self.discord_bot_token = token
            self.save_settings()
        if not token:
            self._set_discord_status("No bot token provided.")
            return
        self._set_discord_status("Connecting...")
        self._discord_service.start(token, on_status=self._set_discord_status)

    def _disconnect_discord_bot(self):
        """Stop the Discord bot."""
        self._discord_service.stop()
        self._set_discord_status("Disconnected")

    def _post_to_discord(self, channel_key: str):
        """Post the current lineup as a Discord embed to the specified channel."""
        import datetime as _dt

        import discord

        if not self._discord_service.is_running:
            self._set_discord_status("Bot is not connected.")
            return

        channel_id_str = self.discord_channels.get(channel_key, "").strip()
        if not channel_id_str:
            self._set_discord_status(f"No channel ID set for '{channel_key}'.")
            return
        try:
            channel_id = int(channel_id_str)
        except ValueError:
            self._set_discord_status(f"Invalid channel ID for '{channel_key}'.")
            return

        snap = self._build_snapshot()
        if not snap.slots:
            self._set_discord_status("Lineup is empty — nothing to post.")
            return

        # ── Build embed ───────────────────────────────────────────────
        start = snap.start_datetime
        unix = int(start.timestamp())

        embed = discord.Embed(
            title=snap.full_title or "Lineup",
            description=f"<t:{unix}:F> (<t:{unix}:R>)",
            color=0x5865F2,  # Discord blurple
            timestamp=_dt.datetime.fromtimestamp(unix, tz=_dt.timezone.utc),
        )

        if snap.genres:
            embed.add_field(
                name="Genres",
                value=" // ".join(snap.genres),
                inline=False,
            )

        # Build lineup field(s) — split at 1024 chars (embed field limit)
        ptr = start
        lineup_lines: list[str] = []
        for slot in snap.slots:
            name = slot.name or "TBA"
            if snap.names_only:
                lineup_lines.append(f"**{name}**")
            else:
                ts = int(ptr.timestamp())
                genre_str = f"  •  {slot.genre}" if slot.genre else ""
                lineup_lines.append(f"<t:{ts}:t>  **{name}**{genre_str}")
            ptr += _dt.timedelta(minutes=slot.duration)

        lineup_text = "\n".join(lineup_lines)
        # Discord embed fields max 1024 chars; split into pages
        chunks = [lineup_text[i : i + 1024] for i in range(0, len(lineup_text), 1024)]
        for i, chunk in enumerate(chunks):
            embed.add_field(
                name="Lineup" if i == 0 else "\u200b",
                value=chunk,
                inline=False,
            )

        # Social links footer
        link_order = ["TIMELINE", "VRCPOP", "X", "IG", "DISCORD", "VRC GROUP"]
        if snap.social_links:
            parts = [
                f"[{label}]({snap.social_links[label]})"
                for label in link_order
                if snap.social_links.get(label, "").strip()
            ]
            if parts:
                embed.add_field(name="Links", value=" | ".join(parts), inline=False)

        # Embed image — URL or local file
        import os
        image_path = getattr(self, "discord_embed_image", "").strip()
        embed.set_footer(text="GitHub | Baebu/lineup_builder")

        attach_file = None
        if image_path:
            if image_path.startswith(("http://", "https://")):
                embed.set_image(url=image_path)
            elif os.path.isfile(image_path):
                filename = os.path.basename(image_path)
                attach_file = discord.File(image_path, filename=filename)
                embed.set_image(url=f"attachment://{filename}")

        self._set_discord_status(f"Posting to {channel_key}...")
        self._discord_service.send_embed(
            channel_id, embed,
            file=attach_file,
            on_success=lambda: self._set_discord_status(
                f"Posted to {channel_key} channel."),
            on_error=lambda e: self._set_discord_status(f"Error: {e}"),
        )

    # ── Scheduled posting ─────────────────────────────────────────────

    def _open_schedule_picker(self):
        """Open the calendar picker for the schedule datetime field."""
        from .date_time_picker import open_datetime_picker
        from ..types import DPGVar
        var = DPGVar(tag="discord_schedule_datetime")
        open_datetime_picker(var, callback=None)

    def _schedule_discord_post(self):
        """Add a scheduled post entry from the UI inputs."""
        raw_dt = ""
        if dpg.does_item_exist("discord_schedule_datetime"):
            raw_dt = dpg.get_value("discord_schedule_datetime").strip()
        if not raw_dt:
            self._set_discord_status("Enter a date/time to schedule.")
            return
        try:
            post_dt = datetime.strptime(raw_dt, "%Y-%m-%d %H:%M")
        except ValueError:
            self._set_discord_status("Invalid format. Use YYYY-MM-DD HH:MM")
            return
        if post_dt <= datetime.now():
            self._set_discord_status("Schedule time must be in the future.")
            return

        channel_key = "events"
        if dpg.does_item_exist("discord_schedule_channel"):
            channel_key = dpg.get_value("discord_schedule_channel")

        # Snapshot the current lineup state
        snap = self._build_snapshot()
        if not snap.slots:
            self._set_discord_status("Lineup is empty — nothing to schedule.")
            return

        # Store as a pending entry
        if not hasattr(self, "_discord_scheduled_posts"):
            self._discord_scheduled_posts = []

        entry = {
            "datetime": raw_dt,
            "channel": channel_key,
            "snapshot": snap,
            "image": getattr(self, "discord_embed_image", ""),
        }
        self._discord_scheduled_posts.append(entry)
        self._save_scheduled_posts()
        self._refresh_schedule_list_ui()
        self._set_discord_status(f"Scheduled for {raw_dt} → {channel_key}")

        # Clear the datetime input
        if dpg.does_item_exist("discord_schedule_datetime"):
            dpg.set_value("discord_schedule_datetime", "")

    def _cancel_scheduled_post(self, idx: int):
        """Remove a scheduled post by index."""
        posts = getattr(self, "_discord_scheduled_posts", [])
        if 0 <= idx < len(posts):
            posts.pop(idx)
            self._save_scheduled_posts()
            self._refresh_schedule_list_ui()

    def _open_pending_popup(self):
        """Open a popup window showing pending scheduled posts."""
        tag = "pending_posts_win"
        if dpg.does_item_exist(tag):
            dpg.delete_item(tag)
        with dpg.window(
            tag=tag, label="Pending Scheduled Posts",
            modal=True, autosize=True, no_resize=True,
            no_scrollbar=True, min_size=(320, 100),
        ):
            dpg.add_group(tag="discord_scheduled_list")
            self._refresh_schedule_list_ui()
            dpg.add_spacer(height=4)
            dpg.add_button(label="Close", width=-1,
                           callback=lambda: dpg.delete_item(tag))

    def _refresh_schedule_list_ui(self):
        """Rebuild the pending-posts list in the popup."""
        tag = "discord_scheduled_list"
        if not dpg.does_item_exist(tag):
            return
        dpg.delete_item(tag, children_only=True)

        posts = getattr(self, "_discord_scheduled_posts", [])
        if not posts:
            styled_text("  No scheduled posts", MUTED, parent=tag)
            return

        for i, entry in enumerate(posts):
            dt_str = entry.get("datetime", "?")
            ch = entry.get("channel", "?")
            with dpg.group(horizontal=True, parent=tag):
                styled_text(f"  {dt_str} → {ch}", LABEL)
                idx = i  # capture for closure
                dpg.add_button(
                    label=Icon.CLOSE, width=22, height=18,
                    callback=lambda s, a, u=idx: self._cancel_scheduled_post(u),
                )
                bind_icon_font(dpg.last_item())

    def check_scheduled_posts(self):
        """Called every frame via process_queue to fire due posts.

        Only checks once per second to avoid excess overhead.
        """
        now = datetime.now()
        last = getattr(self, "_last_schedule_check", None)
        if last and (now - last).total_seconds() < 1.0:
            return
        self._last_schedule_check = now

        posts = getattr(self, "_discord_scheduled_posts", [])
        if not posts:
            return

        fired = []
        for i, entry in enumerate(posts):
            try:
                post_dt = datetime.strptime(entry["datetime"], "%Y-%m-%d %H:%M")
            except (ValueError, KeyError):
                fired.append(i)
                continue
            if now >= post_dt:
                self._fire_scheduled_post(entry)
                fired.append(i)

        if fired:
            for idx in reversed(fired):
                posts.pop(idx)
            self._save_scheduled_posts()
            self._refresh_schedule_list_ui()

    def _fire_scheduled_post(self, entry: dict):
        """Execute a scheduled post using its stored snapshot."""
        import datetime as _dt
        import os

        import discord

        channel_key = entry.get("channel", "events")
        if not self._discord_service.is_running:
            self._set_discord_status(f"Missed schedule ({channel_key}): bot not connected.")
            return

        channel_id_str = self.discord_channels.get(channel_key, "").strip()
        if not channel_id_str:
            self._set_discord_status(f"Missed schedule: no channel for '{channel_key}'.")
            return
        try:
            channel_id = int(channel_id_str)
        except ValueError:
            self._set_discord_status(f"Missed schedule: invalid channel for '{channel_key}'.")
            return

        snap = entry.get("snapshot")
        if snap is None or not snap.slots:
            return

        start = snap.start_datetime
        unix = int(start.timestamp())

        embed = discord.Embed(
            title=snap.full_title or "Lineup",
            description=f"<t:{unix}:F> (<t:{unix}:R>)",
            color=0x5865F2,
            timestamp=_dt.datetime.fromtimestamp(unix, tz=_dt.timezone.utc),
        )

        if snap.genres:
            embed.add_field(name="Genres", value=" // ".join(snap.genres), inline=False)

        ptr = start
        lineup_lines: list[str] = []
        for slot in snap.slots:
            name = slot.name or "TBA"
            if snap.names_only:
                lineup_lines.append(f"**{name}**")
            else:
                ts = int(ptr.timestamp())
                genre_str = f"  •  {slot.genre}" if slot.genre else ""
                lineup_lines.append(f"<t:{ts}:t>  **{name}**{genre_str}")
            ptr += _dt.timedelta(minutes=slot.duration)

        lineup_text = "\n".join(lineup_lines)
        chunks = [lineup_text[i : i + 1024] for i in range(0, len(lineup_text), 1024)]
        for i, chunk in enumerate(chunks):
            embed.add_field(
                name="Lineup" if i == 0 else "\u200b",
                value=chunk, inline=False,
            )

        link_order = ["TIMELINE", "VRCPOP", "X", "IG", "DISCORD", "VRC GROUP"]
        if snap.social_links:
            parts = [
                f"[{label}]({snap.social_links[label]})"
                for label in link_order
                if snap.social_links.get(label, "").strip()
            ]
            if parts:
                embed.add_field(name="Links", value=" | ".join(parts), inline=False)

        image_path = entry.get("image", "").strip()
        attach_file = None
        if image_path:
            if image_path.startswith(("http://", "https://")):
                embed.set_image(url=image_path)
            elif os.path.isfile(image_path):
                filename = os.path.basename(image_path)
                attach_file = discord.File(image_path, filename=filename)
                embed.set_image(url=f"attachment://{filename}")

        embed.set_footer(text="GitHub | Baebu/lineup_builder")

        self._set_discord_status(f"Sending scheduled post to {channel_key}...")
        self._discord_service.send_embed(
            channel_id, embed,
            file=attach_file,
            on_success=lambda: self._set_discord_status(
                f"Scheduled post sent to {channel_key}."),
            on_error=lambda e: self._set_discord_status(f"Schedule error: {e}"),
        )

    def _save_scheduled_posts(self):
        """Persist scheduled posts to settings.json."""
        from ..types import DPGVar  # noqa: F401
        posts = getattr(self, "_discord_scheduled_posts", [])
        serializable = []
        for entry in posts:
            serializable.append({
                "datetime": entry.get("datetime", ""),
                "channel": entry.get("channel", ""),
                "image": entry.get("image", ""),
                "snapshot": self._snapshot_to_dict(entry.get("snapshot"))
                            if entry.get("snapshot") else None,
            })
        self.discord_scheduled_posts = serializable
        self.save_settings()

    @staticmethod
    def _snapshot_to_dict(snap) -> dict:
        """Serialize an EventSnapshot to a plain dict."""
        if snap is None:
            return {}
        return {
            "title": snap.title,
            "vol": snap.vol,
            "timestamp": snap.timestamp,
            "genres": list(snap.genres),
            "slots": [{"name": s.name, "genre": s.genre, "duration": s.duration}
                      for s in snap.slots],
            "names_only": snap.names_only,
            "output_format": snap.output_format,
            "saved_djs": [{"name": d.name, "stream": d.stream, "exact_link": d.exact_link}
                          for d in snap.saved_djs],
            "social_links": dict(snap.social_links),
        }

    @staticmethod
    def _dict_to_snapshot(d: dict):
        """Deserialize a plain dict back into an EventSnapshot."""
        from ..backend.types import DJInfo, EventSnapshot, SlotData
        if not d:
            return None
        return EventSnapshot(
            title=d.get("title", ""),
            vol=d.get("vol", ""),
            timestamp=d.get("timestamp", ""),
            genres=d.get("genres", []),
            slots=[SlotData(s.get("name", ""), s.get("genre", ""), s.get("duration", 60))
                   for s in d.get("slots", [])],
            names_only=d.get("names_only", False),
            output_format=d.get("output_format", "discord"),
            saved_djs=[DJInfo(dj.get("name", ""), dj.get("stream", ""), dj.get("exact_link", False))
                       for dj in d.get("saved_djs", [])],
            social_links=d.get("social_links", {}),
        )

    def _load_scheduled_posts(self):
        """Restore scheduled posts from settings (called at startup)."""
        self._discord_scheduled_posts = []
        raw = getattr(self, "discord_scheduled_posts", [])
        now = datetime.now()
        for entry in raw:
            try:
                post_dt = datetime.strptime(entry["datetime"], "%Y-%m-%d %H:%M")
            except (ValueError, KeyError):
                continue
            if post_dt > now:
                snap = self._dict_to_snapshot(entry.get("snapshot"))
                self._discord_scheduled_posts.append({
                    "datetime": entry["datetime"],
                    "channel": entry.get("channel", "events"),
                    "image": entry.get("image", ""),
                    "snapshot": snap,
                })

    def _toggle_times(self):
        self.names_only.set(not self.names_only.get())
        self.update_output()

    def _copy_output(self):
        """Copy the output text to the system clipboard."""
        if dpg.does_item_exist("output_text"):
            text = dpg.get_value("output_text")
            if text:
                dpg.set_clipboard_text(text)

    # ── Scroll-wheel helpers ─────────────────────────────────────────
    # One global handler checks is_item_hovered for every registered item.

    def _shift_timestamp(self, delta_mins: int):
        """Shift the event timestamp by *delta_mins* minutes."""
        raw = self.event_timestamp.get()
        try:
            dt = datetime.strptime(raw, "%Y-%m-%d %H:%M")
        except ValueError:
            return
        dt += timedelta(minutes=delta_mins)
        new_str = dt.strftime("%Y-%m-%d %H:%M")
        self.event_timestamp.set(new_str)
        if dpg.does_item_exist("event_timestamp_input"):
            dpg.set_value("event_timestamp_input", new_str)
        self._schedule_update()

    def _setup_wheel_handler(self):
        if not hasattr(self, '_scroll_combos'):
            self._scroll_combos = {}
        if not hasattr(self, '_scroll_ints'):
            self._scroll_ints = {}
        if not dpg.does_item_exist("global_wheel_hr"):
            with dpg.handler_registry(tag="global_wheel_hr"):
                dpg.add_mouse_wheel_handler(callback=self._on_mouse_wheel)
                dpg.add_key_press_handler(dpg.mvKey_Up, callback=self._on_arrow_key)
                dpg.add_key_press_handler(dpg.mvKey_Down, callback=self._on_arrow_key)

    def _register_scroll_combo(self, tag: str, items: list, on_change):
        if not hasattr(self, '_scroll_combos'):
            self._scroll_combos = {}
        self._scroll_combos[tag] = (list(items), on_change)

    def _register_scroll_int(self, tag: str, min_val: int = 0,
                             max_val: int = 9999, on_change=None):
        if not hasattr(self, '_scroll_ints'):
            self._scroll_ints = {}
        self._scroll_ints[tag] = (min_val, max_val, on_change)

    def _on_arrow_key(self, sender, app_data):
        """Arrow Up/Down on the timestamp input shifts time."""
        if not (dpg.does_item_exist("event_timestamp_input")
                and dpg.is_item_hovered("event_timestamp_input")):
            return
        shift = dpg.is_key_down(dpg.mvKey_LShift) or dpg.is_key_down(dpg.mvKey_RShift)
        step = 1440 if shift else 15
        if app_data == dpg.mvKey_Up:
            self._shift_timestamp(step)
        else:
            self._shift_timestamp(-step)

    def _on_mouse_wheel(self, sender, app_data):
        # app_data is positive when scrolling up, negative when down.
        # We invert so scroll-up = higher value.
        delta = 1 if app_data > 0 else -1

        # ── Timestamp scroll ──────────────────────────────────────────
        if (dpg.does_item_exist("event_timestamp_input")
                and dpg.is_item_hovered("event_timestamp_input")):
            shift = dpg.is_key_down(dpg.mvKey_LShift) or dpg.is_key_down(dpg.mvKey_RShift)
            step = 1440 if shift else 15
            self._shift_timestamp(delta * step)
            return

        for tag, (items, cb) in list(getattr(self, '_scroll_combos', {}).items()):
            if dpg.does_item_exist(tag) and dpg.is_item_hovered(tag):
                itype = dpg.get_item_info(tag).get("type", "")
                if "Button" in itype:
                    cur = dpg.get_item_configuration(tag).get("label")
                else:
                    cur = str(dpg.get_value(tag))
                try:
                    idx = items.index(str(cur))
                except ValueError:
                    idx = 0
                new_idx = max(0, min(len(items) - 1, idx - delta))
                if "Button" in itype:
                    dpg.configure_item(tag, label=items[new_idx])
                else:
                    dpg.set_value(tag, items[new_idx])
                cb()
                return
        for tag, (mn, mx, cb) in list(getattr(self, '_scroll_ints', {}).items()):
            if dpg.does_item_exist(tag) and dpg.is_item_hovered(tag):
                try:
                    cur = int(dpg.get_value(tag))
                except (ValueError, TypeError):
                    cur = mn
                new_val = max(mn, min(mx, cur + delta))
                dpg.set_value(tag, str(new_val))
                if cb:
                    cb()
                return

    def _is_over_slots_panel(self, x_root: int, y_root: int) -> bool:
        try:
            mn = dpg.get_item_rect_min("slots_scroll")
            mx = dpg.get_item_rect_max("slots_scroll")
        except Exception:
            return False
        return mn[0] <= x_root <= mx[0] and mn[1] <= y_root <= mx[1]

    # ── Resize handle logic ───────────────────────────────────────────

    _resize_dragging = False
    _resize_start_y = 0
    _resize_start_h = 360

    def _resize_handle_click(self, sender, app_data):
        self._resize_dragging = True
        self._resize_start_y = dpg.get_mouse_pos(local=False)[1]
        try:
            self._resize_start_h = dpg.get_item_height("right_tabs_content")
        except Exception:
            self._resize_start_h = 360

    def _resize_handle_drag(self, sender, app_data):
        if not self._resize_dragging:
            return
        current_y = dpg.get_mouse_pos(local=False)[1]
        delta = current_y - self._resize_start_y
        new_h = max(80, self._resize_start_h + int(delta))
        max_h = dpg.get_viewport_height() - 200
        new_h = min(new_h, max_h)
        dpg.configure_item("right_tabs_content", height=new_h)

    def _resize_handle_release(self, sender, app_data):
        self._resize_dragging = False
        # Update base dimensions so viewport resize scales from the user-set height
        if dpg.does_item_exist("right_tabs_content"):
            self._base_tabs_height = dpg.get_item_height("right_tabs_content")
            self._base_vp_height = dpg.get_viewport_height()

    def _on_viewport_resize(self, sender=None, app_data=None):
        """Scale right panel contents when the viewport is resized."""
        vp_h = dpg.get_viewport_height()
        base_vp = getattr(self, "_base_vp_height", 600)
        base_tabs = getattr(self, "_base_tabs_height", 360)

        # Stretch the panel divider to fill the full viewport height
        if dpg.does_item_exist("panel_divider"):
            dpg.configure_item("panel_divider", height=vp_h)

        if base_vp <= 0 or not dpg.does_item_exist("right_tabs_content"):
            return
        new_h = max(80, int(base_tabs * vp_h / base_vp))
        max_h = vp_h - 200
        new_h = min(new_h, max_h)
        dpg.configure_item("right_tabs_content", height=new_h)
