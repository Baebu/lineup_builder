"""
Module: ui_builder.py
Purpose: Builds the entire application UI layout (Dear PyGui).
Architecture: Mixin for App class.
"""
from datetime import datetime, timedelta

import dearpygui.dearpygui as dpg

from . import theme as T
from .date_time_picker import add_datetime_row
from .fonts import styled_text, bind_icon_font, Icon, HEADER, LABEL, BODY, MUTED, HINT
from .widgets import add_icon_button, add_primary_button



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

    # ── Left panel ────────────────────────────────────────────────────────

    def _build_left_panel(self):
        with dpg.tab_bar(tag="left_tabs"):
            with dpg.tab(label="Event", tag="Event"):
                self._build_event_tab()
            with dpg.tab(label="Roster", tag="Roster"):
                self._build_dj_roster_tab()
            with dpg.tab(label="Settings", tag="Settings"):
                with dpg.child_window(tag="settings_scroll", height=-1,
                                      border=False, autosize_x=True):
                    pass  # populated by _build_settings_tab()

    def _build_event_tab(self):
        with dpg.child_window(tag="event_tab_inner", border=False,
                              autosize_x=True, height=-1):
            # ── Header row ────────────────────────────────────────────────────
            styled_text("   EVENT CONFIGURATION", HEADER)
            with dpg.table(header_row=False, borders_innerH=False, borders_innerV=False,
                           borders_outerH=False, borders_outerV=False, pad_outerX=False):
                dpg.add_table_column()
                dpg.add_table_column()
                with dpg.table_row():
                    dpg.add_button(label="+ New", width=-1,
                                   callback=lambda: self.new_event())
                    add_primary_button("Save", tag="save_event_btn", width=-1, callback=lambda: self.save_event_lineup())
            dpg.add_separator()

            # ── Event title + vol ─────────────────────────────────────────────
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
            self.event_title_var._tag = "event_title_input"
            self.event_vol_var._tag   = "event_vol_input"
            self._register_scroll_int("event_vol_input", min_val=1,
                                      on_change=lambda: self._schedule_update())

            # ── Timestamp ─────────────────────────────────────────────────────
            styled_text("   START", LABEL)
            add_datetime_row(
                "event_timestamp_input", self.event_timestamp,
                callback=lambda s, a, u=None: self._schedule_update(),
            )

            # ── Genres ────────────────────────────────────────────────────────
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

            # ── Saved Events ──────────────────────────────────────────────────
            styled_text("   SAVED EVENTS", HEADER)
            with dpg.child_window(tag="saved_events_scroll", height=-1,
                                  border=False, autosize_x=True):
                pass  # populated by refresh_saved_events_ui()

        self.refresh_genre_tags()
        self.refresh_saved_events_ui()

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

    # ── Social links popup ──────────────────────────────────────────

    _SOCIAL_FIELDS = [
        ("TIMELINE",   "https://vrc.tl/event/"),
        ("VRCPOP",     "https://vrcpop.com/event/"),
        ("X",          "https://x.com/"),
        ("IG",         "https://www.instagram.com/p/"),
        ("DISCORD",    "https://discord.gg/"),
        ("VRC GROUP",  "https://vrc.group/"),
    ]

    def _open_social_links_popup(self):
        win_tag = "social_links_win"
        if dpg.does_item_exist(win_tag):
            dpg.focus_item(win_tag)
            return

        links = getattr(self, "social_links", {})
        persistent = getattr(self, "persistent_links", {})
        _PERSISTENT_KEYS = {"DISCORD", "VRC GROUP"}

        with dpg.window(
            tag=win_tag, label="Social Links", modal=True,
            no_resize=True, no_scrollbar=True, autosize=True,
            on_close=lambda: dpg.delete_item(win_tag),
        ):
            styled_text("  Links included in the Discord output below the genres.",
                        MUTED, wrap=340)
            dpg.add_spacer(height=4)

            input_tags = {}
            checkbox_tags = {}
            for label, hint in self._SOCIAL_FIELDS:
                styled_text(f"  {label}", LABEL)
                tag = f"social_input_{label.replace(' ', '_')}"
                # Pre-fill: use persistent link when enabled, otherwise event-specific
                p = persistent.get(label, {})
                default_val = (p.get("link", "") if p.get("enabled") else "") or links.get(label, "")
                dpg.add_input_text(
                    tag=tag,
                    default_value=default_val,
                    hint=hint,
                    width=340,
                )
                input_tags[label] = tag
                if label in _PERSISTENT_KEYS:
                    cb_tag = f"social_persist_{label.replace(' ', '_')}"
                    dpg.add_checkbox(
                        tag=cb_tag,
                        label="Use for all events",
                        default_value=bool(p.get("enabled", False)),
                    )
                    checkbox_tags[label] = cb_tag

            dpg.add_spacer(height=6)

            def _save_and_close():
                self.social_links = {
                    label: dpg.get_value(input_tags[label]).strip()
                    for label in input_tags
                }
                for key, cb_tag in checkbox_tags.items():
                    self.persistent_links[key] = {
                        "link": dpg.get_value(input_tags[key]).strip(),
                        "enabled": dpg.get_value(cb_tag),
                    }
                self.save_settings()
                self._schedule_update()
                if dpg.does_item_exist(win_tag):
                    dpg.delete_item(win_tag)

            def _clear_all():
                for t in input_tags.values():
                    dpg.set_value(t, "")

            with dpg.group(horizontal=True):
                _apply_btn = dpg.add_button(
                    label="Apply", width=160, callback=lambda: _save_and_close()
                )
                dpg.bind_item_theme(_apply_btn, "primary_btn_theme")
                dpg.add_button(
                    label="Clear All", width=80,
                    callback=lambda: _clear_all(),
                )
                dpg.add_button(
                    label="Cancel", width=80,
                    callback=lambda: dpg.delete_item(win_tag),
                )

    # ── Right panel ───────────────────────────────────────────────────────

    def _build_right_panel(self):
        # ── Tab bar (only controls the top section) ───────────────────────
        with dpg.tab_bar(tag="right_tabs"):
            with dpg.tab(label="Lineup"):
                # ── Row 1: default length + add DJ ────────────────────
                with dpg.group(horizontal=True):
                    dur_values = [str(x) for x in range(15, 121, 15)]
                    styled_text("   TIMESLOTS  ", HEADER)
                    dpg.add_spacer(width=10)

                # ── Slots scroll area ─────────────────────────────────────
                with dpg.child_window(tag="slots_scroll", height=320,
                                      border=True, autosize_x=True,
                                      payload_type="DJ_CARD",
                                      drop_callback=lambda s, a, u=None: self._drop_dj_on_lineup(s, a)):
                    pass  # populated by slot_manager

                # ── Draggable resize handle ───────────────────────────────
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

            with dpg.tab(label="Discord"):
                dpg.add_spacer(height=4)

                with dpg.group(horizontal=True):
                    styled_text("  DISCORD BOT", HEADER)
                    add_icon_button(
                        Icon.SETTINGS, tag="discord_settings_btn",
                        callback=lambda: self._open_discord_settings(),
                    )

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

                dpg.add_spacer(height=8)
                styled_text("  EMBED IMAGE", HEADER)
                with dpg.group(horizontal=True):
                    dpg.add_input_text(
                        tag="embed_image_input",
                        default_value=getattr(self, "discord_embed_image", ""),
                        hint="Paste image URL or path...",
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

                dpg.add_spacer(height=8)
                styled_text("  POST OUTPUT", HEADER)
                with dpg.group(horizontal=True):
                    add_primary_button(
                        "Post to Events", tag="discord_post_events_btn",
                        callback=lambda: self._post_to_discord("events"),
                    )
                    add_primary_button(
                        "Post to Popup", tag="discord_post_popup_btn",
                        callback=lambda: self._post_to_discord("popup"),
                    )
                    add_primary_button(
                        "Post to Signups", tag="discord_post_signups_btn",
                        callback=lambda: self._post_to_discord("signups"),
                    )

                dpg.add_spacer(height=8)
                styled_text("  SCHEDULE POST", HEADER)
                with dpg.group(horizontal=True):
                    dpg.add_input_text(
                        tag="discord_schedule_datetime",
                        default_value="",
                        hint="YYYY-MM-DD HH:MM",
                        width=-50,
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
                    width=-1,
                )
                add_primary_button(
                    "Schedule", tag="discord_schedule_btn", width=-1,
                    callback=lambda: self._schedule_discord_post(),
                )
                dpg.add_spacer(height=4)
                styled_text("  PENDING", LABEL)
                dpg.add_group(tag="discord_scheduled_list")

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

        dpg.add_input_text(
            tag="output_text",
            multiline=True, readonly=True,
            width=-11, height=-30,
        )

        with dpg.table(header_row=False, borders_innerH=False, borders_innerV=False,
                       borders_outerH=False, borders_outerV=False, pad_outerX=False):
            for _ in range(2):
                dpg.add_table_column()
            with dpg.table_row():
                dpg.add_button(tag="social_links_btn", label="Social Links", width=-1,
                               callback=lambda: self._open_social_links_popup())
                add_icon_button(Icon.COPY, tag="copy_output_btn", width=-1, height=20, is_primary=True, callback=lambda: self._copy_output())

    # ── Helpers ───────────────────────────────────────────────────────────

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

    def _open_discord_settings(self):
        """Open a popup with all Discord configuration fields."""
        win_tag = "discord_settings_win"
        if dpg.does_item_exist(win_tag):
            dpg.focus_item(win_tag)
            return

        channels = getattr(self, "discord_channels", {})

        with dpg.window(
            tag=win_tag, label="Discord Settings",
            modal=True, autosize=True, no_resize=True, no_scrollbar=True,
            on_close=lambda: dpg.delete_item(win_tag),
        ):
            styled_text("  BOT CONFIGURATION", HEADER)
            dpg.add_spacer(height=4)

            styled_text("  Client ID", LABEL)
            dpg.add_input_text(
                tag="discord_client_id",
                default_value=getattr(self, "discord_client_id", ""),
                hint="Application Client ID...",
                width=360,
                callback=lambda s, a, u=None: self._save_discord_credentials(),
            )
            dpg.add_spacer(height=2)
            styled_text("  Bot Token", LABEL)
            dpg.add_input_text(
                tag="discord_bot_token",
                default_value=getattr(self, "discord_bot_token", ""),
                hint="Paste bot token here...",
                password=True,
                width=360,
                callback=lambda s, a, u=None: self._save_bot_token(),
            )

            dpg.add_spacer(height=4)
            add_primary_button(
                "Invite Bot to Server", width=360,
                callback=lambda: self._invite_discord_bot(),
            )

            dpg.add_spacer(height=8)
            styled_text("  CHANNELS", HEADER)
            dpg.add_spacer(height=4)

            # Channel combos — populated when bot is connected
            styled_text("  Events Channel", LABEL)
            dpg.add_combo(
                tag="discord_events_channel",
                items=[], default_value=self._channel_display(channels.get("events", "")),
                width=360,
                callback=lambda s, a, u=None: self._save_discord_channels(),
            )
            styled_text("  Popup Channel", LABEL)
            dpg.add_combo(
                tag="discord_popup_channel",
                items=[], default_value=self._channel_display(channels.get("popup", "")),
                width=360,
                callback=lambda s, a, u=None: self._save_discord_channels(),
            )
            styled_text("  Signups Channel", LABEL)
            dpg.add_combo(
                tag="discord_signups_channel",
                items=[], default_value=self._channel_display(channels.get("signups", "")),
                width=360,
                callback=lambda s, a, u=None: self._save_discord_channels(),
            )

            dpg.add_spacer(height=4)
            add_primary_button(
                "Refresh Channels", tag="discord_refresh_channels_btn", width=360,
                callback=lambda: self._fetch_discord_channels(),
            )

            dpg.add_spacer(height=8)
            dpg.add_button(
                label="Close", width=360,
                callback=lambda: dpg.delete_item(win_tag),
            )

        # Auto-fetch channels if bot is already connected
        if self._discord_service.is_running:
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
        from .types import DPGVar
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

    def _refresh_schedule_list_ui(self):
        """Rebuild the pending-posts list in the Discord tab."""
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
        from .types import DPGVar  # noqa: F401
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
    _resize_start_h = 320

    def _resize_handle_click(self, sender, app_data):
        self._resize_dragging = True
        self._resize_start_y = dpg.get_mouse_pos(local=False)[1]
        try:
            self._resize_start_h = dpg.get_item_height("slots_scroll")
        except Exception:
            self._resize_start_h = 320

    def _resize_handle_drag(self, sender, app_data):
        if not self._resize_dragging:
            return
        current_y = dpg.get_mouse_pos(local=False)[1]
        delta = current_y - self._resize_start_y
        new_h = max(80, self._resize_start_h + int(delta))
        max_h = dpg.get_viewport_height() - 200
        new_h = min(new_h, max_h)
        dpg.configure_item("slots_scroll", height=new_h)

    def _resize_handle_release(self, sender, app_data):
        self._resize_dragging = False
