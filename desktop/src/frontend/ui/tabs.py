import dearpygui.dearpygui as dpg

from ..styling.fonts import styled_text, HEADER, LABEL, MUTED, Icon
from .widgets import add_primary_button, add_icon_button, section
from .date_time_picker import add_datetime_row

class TabsBuilderMixin:
    _SOCIAL_FIELDS =[
        ("TIMELINE",   "https://vrc.tl/event/"),
        ("VRCPOP",     "https://vrcpop.com/event/"),
        ("X",          "https://x.com/"),
        ("IG",         "https://www.instagram.com/p/"),
    ]

    _CLUB_LINK_FIELDS =[
        ("DISCORD",    "https://discord.gg/"),
        ("VRC GROUP",  "https://vrc.group/"),
    ]

    def _build_event_tab(self):
        with dpg.child_window(tag="event_tab_inner", border=False,
                              autosize_x=True, height=-1):
            # ── Header row ────────────────────────────────────────────────────
            with dpg.table(header_row=False, borders_innerH=False,
                           borders_innerV=False, borders_outerH=False,
                           borders_outerV=False, pad_outerX=False):
                dpg.add_table_column(width_stretch=True)
                dpg.add_table_column(width_stretch=True)
                with dpg.table_row():
                    dpg.add_button(label="+ New", width=-1,
                                   callback=lambda: self.new_event())
                    add_primary_button("Load", tag="load_event_btn", width=-1,
                                       callback=lambda: self._toggle_saved_events_drawer())

            # ── Saved events drawer (inline, hidden by default) ─────────
            with dpg.child_window(tag="saved_events_drawer", height=200,
                                  border=True, autosize_x=True, show=False):
                with dpg.child_window(tag="saved_events_scroll", height=-1,
                                      border=False, autosize_x=True):
                    pass  # populated by refresh_saved_events_ui()
            self._saved_events_drawer_open = False

            dpg.add_separator()

            # ── DETAILS section ───────────────────────────────────────
            with section(self, "evt_config", "DETAILS"):
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

                    # ── Start ─────────────────────────────────────────────────
                    with dpg.table_row():
                        styled_text("   START", LABEL)
                        add_datetime_row(
                            "event_timestamp_input", self.event_timestamp,
                            callback=lambda s, a, u=None: self._schedule_update(),
                        )

                # ── Post-table tag wiring ─────────────────────────────────
                self.event_title_var._tag = "event_title_input"
                self.event_vol_var._tag   = "event_vol_input"
                self._register_scroll_int("event_vol_input", min_val=1,
                                          on_change=lambda: self._schedule_update())
                self.group_name_var._tag  = "group_name_input"
                self.collab_with_var._tag = "collab_with_input"

            # ── GENRES section ────────────────────────────────────────────
            with section(self, "evt_genres", "GENRES"):
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
                dpg.bind_item_handler_registry("genre_entry", "genre_entry_hr")
                with dpg.child_window(tag="genre_tags_frame", height=90,
                                      border=False, autosize_x=True):
                    pass  # populated by refresh_genre_tags()

            # ── LINKS section ─────────────────────────────────────────────
            with section(self, "evt_links", "LINKS"):
                _LABEL_W = 62
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
                                user_data=label,
                                callback=lambda s, a, u: self._on_social_link_changed(u),
                            )
                    for label, hint in self._CLUB_LINK_FIELDS:
                        tag_key = label.replace(' ', '_')
                        p = self.persistent_links.get(label, {})
                        with dpg.table_row():
                            styled_text(f"   {label}", LABEL)
                            dpg.add_input_text(
                                tag=f"group_link_{tag_key}",
                                default_value=(p.get("link", "")
                                               if isinstance(p, dict) else ""),
                                hint=hint, width=-1,
                                callback=lambda s, a, u=label: (
                                    self._on_club_link_changed(u)),
                            )

            # ── IMAGE section ─────────────────────────────────────────────
            with section(self, "evt_image", "IMAGE"):
                import os
                _img_path = getattr(self, "discord_embed_image", "")
                
                # Display selected image if available
                if _img_path and os.path.exists(_img_path):
                    # Create/update texture
                    tex_tag = "embed_image_tex"
                    img_tag = "embed_image_display"
                    
                    # Remove existing image display
                    if dpg.does_item_exist(img_tag):
                        dpg.delete_item(img_tag)
                    if dpg.does_item_exist(tex_tag):
                        dpg.delete_item(tex_tag)
                    
                    try:
                        from PIL import Image
                        img = Image.open(_img_path)
                        
                        # Handle different image modes
                        if img.mode == 'P':  # Palette mode
                            img = img.convert('RGBA')
                        elif img.mode == 'RGB':
                            img = img.convert('RGBA')
                        elif img.mode != 'RGBA':
                            img = img.convert('RGBA')
                        
                        # Resize to fit nicely (max 150px height, maintain aspect ratio)
                        max_height = 150
                        aspect_ratio = img.width / img.height
                        new_width = int(max_height * aspect_ratio)
                        new_height = max_height
                        if new_width > 300:  # Max width
                            new_width = 300
                            new_height = int(new_width / aspect_ratio)
                        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                        
                        # Convert to DPG format (RGBA float values 0-1)
                        pixels = []
                        for pixel in img.getdata():
                            if len(pixel) == 4:  # RGBA
                                pixels.extend([pixel[0] / 255.0, pixel[1] / 255.0, pixel[2] / 255.0, pixel[3] / 255.0])
                            elif len(pixel) == 3:  # RGB
                                pixels.extend([pixel[0] / 255.0, pixel[1] / 255.0, pixel[2] / 255.0, 1.0])
                        
                        with dpg.texture_registry():
                            dpg.add_static_texture(new_width, new_height, pixels, tag=tex_tag)
                        
                        # Display the image
                        dpg.add_image(tex_tag, tag=img_tag)
                        dpg.add_spacer(height=8)
                    except Exception as e:
                        log.debug(f"Failed to load image {_img_path}: {e}")
                        styled_text(f"   Failed to load image: {os.path.basename(_img_path)}", ERROR)
                
                # Image selection controls
                with dpg.table(header_row=False, borders_innerH=False,
                               borders_innerV=False, borders_outerH=False,
                               borders_outerV=False, pad_outerX=False):
                    dpg.add_table_column(width_stretch=True)
                    dpg.add_table_column(width_fixed=True)
                    with dpg.table_row():
                        _img_label = os.path.basename(_img_path) if _img_path else "Select Image..."
                        if len(_img_label) > 28:
                            _img_label = _img_label[:25] + "..."
                        add_primary_button(
                            _img_label, tag="embed_image_browse_btn", width=-1,
                            callback=lambda: self._browse_embed_image(),
                        )
                        dpg.add_button(
                            tag="embed_image_clear_btn", label="X", width=35,
                            callback=lambda: self._clear_embed_image(),
                        )

            # ── DISCORD section ───────────────────────────────────────
            with section(self, "evt_discord", "DISCORD"):
                with dpg.group(horizontal=True):
                    styled_text("  Bot", LABEL)
                    dpg.add_spacer(width=4)
                    styled_text("  Not connected", MUTED, tag="discord_status_text")

                with dpg.table(header_row=False, borders_innerH=False,
                               borders_innerV=False, borders_outerH=False,
                               borders_outerV=False, pad_outerX=False):
                    for _ in range(2):
                        dpg.add_table_column()
                    with dpg.table_row():
                        add_primary_button(
                            "Connect", tag="discord_connect_btn", width=-1,
                            callback=lambda: self._connect_discord_bot(),
                        )
                        dpg.add_button(
                            tag="discord_disconnect_btn", label="Disconnect", width=-1,
                            callback=lambda: self._disconnect_discord_bot(),
                        )

                # ── Configure drawer (hidden by default) ────────────
                add_primary_button(
                    "Configure", tag="discord_settings_btn", width=-1,
                    callback=lambda: self._toggle_discord_settings_drawer(),
                )
                with dpg.child_window(tag="discord_settings_drawer", height=220,
                                      border=True, autosize_x=True, show=False):
                    self._build_discord_settings_drawer()

                dpg.add_spacer(height=4)

                # ── Server select ──────────────────────────────────────
                styled_text("  Server", LABEL)
                dpg.add_combo(
                    tag="discord_ping_server",
                    items=[], default_value="",
                    width=-1,
                    callback=lambda s, a, u=None: self._on_server_selected(),
                )

                # ── Channel select ─────────────────────────────────────
                styled_text("  Channel", LABEL)
                dpg.add_combo(
                    tag="discord_channel",
                    items=[], default_value="",
                    width=-1,
                    callback=lambda s, a, u=None: self._save_discord_channel(),
                )

                # ── Role to Ping ───────────────────────────────────────
                styled_text("  Role to Ping", LABEL)
                dpg.add_combo(
                    tag="discord_ping_roles",
                    items=["None"], default_value="None",
                    width=-1,
                    callback=lambda s, a, u=None: self._save_discord_ping_roles(),
                )

                # ── Post button ────────────────────────────────────────
                add_primary_button(
                    "Post to Discord", tag="discord_post_btn", width=-1,
                    callback=lambda: self._confirm_post_to_discord(),
                )

        self.refresh_genre_tags()

    def _build_dj_roster_tab(self):
        add_primary_button("+ New DJ", tag="new_dj_btn", width=-1,
                           callback=lambda: self.add_new_dj_to_roster())
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