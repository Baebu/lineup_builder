import customtkinter as ctk
from .date_time_picker import CTkDateTimePicker
import tkinter as tk
from tkinter import messagebox
from . import theme as T


class UISetupMixin:
    """Builds the entire application UI and provides title management helpers."""

    def setup_ui(self):
        # Ensure theme-tracking lists exist even if load_settings() hasn't run yet
        for _attr in ("_accent_labels", "_primary_buttons", "_danger_buttons",
                      "_success_buttons", "_scrollable_frames"):
            self.__dict__.setdefault(_attr, [])

        # Grid Layout
        _lpw = self.settings.get("left_panel_width", 380)
        self.grid_columnconfigure(0, weight=0, minsize=_lpw)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ==========================================
        # LEFT PANEL: Configuration & Settings
        # ==========================================
        _lpw = self.settings.get("left_panel_width", 380)
        left_panel = ctk.CTkFrame(
            self, width=_lpw,
            fg_color=self.settings.get("panel_bg", T.PANEL_BG),
            corner_radius=T.PANEL_RADIUS,
            border_width=T.BORDER_W,
            border_color=self.settings.get("border_color", T.BORDER),
        )
        left_panel.grid(row=0, column=0, rowspan=2, padx=(4, 2), pady=(0, 4), sticky="nsew")
        left_panel.grid_propagate(False)
        left_panel.grid_columnconfigure(0, weight=1)
        left_panel.grid_rowconfigure(0, weight=1)
        self._left_panel = left_panel

        # ==========================================
        # RIGHT PANEL: Lineup & Output
        # ==========================================
        self.right_panel = ctk.CTkFrame(
            self,
            fg_color=T.PANEL_BG,
            corner_radius=T.PANEL_RADIUS,
            border_width=T.BORDER_W,
            border_color=T.BORDER,
        )
        self.right_panel.grid(row=0, column=1, padx=(2, 4), pady=(0, 4), sticky="nsew")
        self.right_panel.grid_propagate(False)
        self.right_panel.grid_columnconfigure(0, weight=1)
        self.right_panel.grid_rowconfigure(0, weight=2)
        self.right_panel.grid_rowconfigure(1, weight=0)

        self._create_left_tabs(left_panel)

        self.left_tabs.tab("Event").grid_columnconfigure(0, weight=1)
        self.left_tabs.tab("Event").grid_rowconfigure(0, weight=0)
        self.left_tabs.tab("Event").grid_rowconfigure(1, weight=0)
        self.left_tabs.tab("DJ Roster").grid_columnconfigure(0, weight=1)
        self.left_tabs.tab("DJ Roster").grid_rowconfigure(0, weight=0)
        self.left_tabs.tab("DJ Roster").grid_rowconfigure(1, weight=1)
        self.left_tabs.tab("Settings").grid_columnconfigure(0, weight=1)
        self.left_tabs.tab("Settings").grid_rowconfigure(0, weight=1)

        # Tabview is created in _create_left_tabs above

        # ── Event tab ─────────────────────────────────────────────────────
        _event_tab = self.left_tabs.tab("Event")

        # Shared header (always visible)
        config_header = ctk.CTkFrame(_event_tab, fg_color="transparent")
        config_header.grid(row=0, column=0, sticky="ew", padx=15, pady=(5, 5))
        self._event_header_lbl = ctk.CTkLabel(
            config_header, text="EVENT CONFIGURATION",
            font=("Arial", 11, "bold"), text_color=T.ACCENT
        )
        self._event_header_lbl.pack(side="left")
        self._accent_labels.append(self._event_header_lbl)
        ctk.CTkButton(
            config_header, text="\U0001F4CB Import", width=90, height=T.WIDGET_H_PILL,
            **T.BTN_SECONDARY,
            font=T.FONT_SMALL_BOLD, text_color=T.TEXT_SECONDARY,
            command=self.open_import_dialog,
        ).pack(side="right")
        _save_btn = ctk.CTkButton(
            config_header, text="💾 SAVE", width=80, height=T.WIDGET_H_PILL,
            fg_color=self.settings.get("success_color", T.SUCCESS),
            hover_color=self.settings.get("success_hover_color", T.SUCCESS_HOVER),
            font=T.FONT_SMALL_BOLD, text_color=T.TEXT_PRIMARY,
            command=self.save_event_lineup,
        )
        _save_btn.pack(side="right", padx=(0, 4))
        self._success_buttons.append(_save_btn)
        ctk.CTkButton(
            config_header, text="+ NEW", width=70, height=T.WIDGET_H_PILL,
            **T.BTN_SECONDARY,
            font=T.FONT_SMALL_BOLD, text_color=T.TEXT_PRIMARY,
            command=self.new_event,
        ).pack(side="right", padx=(0, 4))

        # ── Event config panel (default) ──────────────────────────────────
        config_frame = ctk.CTkFrame(_event_tab, fg_color="transparent")
        config_frame.grid(row=1, column=0, sticky="nsew")
        config_frame.grid_columnconfigure(0, weight=1)
        self._event_config_panel = config_frame

        config_grid = ctk.CTkFrame(config_frame, fg_color="transparent")
        config_grid.pack(fill="x", expand=False, padx=15, pady=0)
        config_grid.grid_columnconfigure((0, 1), weight=1)

        # Title
        title_frame = ctk.CTkFrame(config_grid, fg_color="transparent")
        title_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=5)
        ctk.CTkLabel(title_frame, text="EVENT TITLE", font=T.FONT_LABEL, text_color=T.TEXT_SECONDARY).pack(anchor="w")

        title_input_frame = ctk.CTkFrame(title_frame, fg_color="transparent")
        title_input_frame.pack(fill="x", pady=(2, 0))
        title_input_frame.grid_columnconfigure(0, weight=1)

        self.title_entry = ctk.CTkEntry(
            title_input_frame,
            textvariable=self.event_title_var,
            placeholder_text="Event title...",
            **T.ENTRY,
        )
        self.title_entry.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        self.event_title_var.trace_add("write", lambda *args: self._schedule_update())

        vol_frame = ctk.CTkFrame(title_input_frame, fg_color="transparent")
        vol_frame.grid(row=0, column=1, padx=(0, 5))
        ctk.CTkLabel(vol_frame, text="Vol.", font=T.FONT_BODY_BOLD, text_color=T.TEXT_SECONDARY).pack(side="left", padx=(0, 3))
        self.vol_entry = ctk.CTkEntry(
            vol_frame,
            textvariable=self.event_vol_var,
            width=40, **T.ENTRY,
        )
        self.vol_entry.pack(side="left")
        self.event_vol_var.trace_add("write", lambda *args: self._schedule_update())

        # Trigger auto-save when user commits the title (Enter or focus-out)
        def _on_title_commit(*_):
            if self.event_title_var.get().strip():
                self._auto_event_save()
        self.title_entry.bind("<Return>", _on_title_commit)
        self.title_entry.bind("<FocusOut>", _on_title_commit)

        # Date & Time
        timestamp_frame = ctk.CTkFrame(config_grid, fg_color="transparent")
        timestamp_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=5)
        ctk.CTkLabel(timestamp_frame, text="EVENT START TIMESTAMP", font=T.FONT_LABEL, text_color=T.TEXT_SECONDARY).pack(anchor="w")
        CTkDateTimePicker(timestamp_frame, variable=self.event_timestamp).pack(fill="x", pady=(2, 0))

        # Genres
        genre_frame = ctk.CTkFrame(config_grid, fg_color="transparent")
        genre_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=5)
        ctk.CTkLabel(genre_frame, text="GENRES (Press Enter to add)", font=T.FONT_LABEL, text_color=T.TEXT_SECONDARY).pack(anchor="w")

        genre_input_frame = ctk.CTkFrame(genre_frame, fg_color="transparent")
        genre_input_frame.pack(fill="x", pady=(2, 0))
        genre_input_frame.grid_columnconfigure(0, weight=1)

        self.genre_entry = ctk.CTkEntry(
            genre_input_frame, textvariable=self.genre_entry_var,
            placeholder_text="Type and press Enter...",
            **T.ENTRY,
        )
        self.genre_entry.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        self.genre_entry.bind("<Return>", self.add_genre_from_entry)

        ctk.CTkButton(
            genre_input_frame, text="", image=self.icon_edit, width=T.ICON_BTN_W, height=T.ICON_BTN_W,
            **T.BTN_SECONDARY,
            command=self.open_genre_editor
        ).grid(row=0, column=1, padx=(5, 0))

        self.genre_del_btn = ctk.CTkButton(
            genre_input_frame, text="", image=self.icon_trash, width=T.ICON_BTN_W, height=T.ICON_BTN_W,
            **T.BTN_DANGER,
            command=self.delete_saved_genre
        )
        self.genre_del_btn.grid(row=0, column=2, padx=(5, 0))
        self._danger_buttons.append(self.genre_del_btn)

        # ── Saved genres scroll container ─────────────────────────────
        ctk.CTkLabel(
            genre_frame,
            text="SAVED GENRES",
            font=("Arial", 10, "bold"),
            text_color=T.TEXT_MUTED,
            anchor="w",
        ).pack(fill="x", pady=(6, 0))

        self.genre_tags_frame = ctk.CTkScrollableFrame(
            genre_frame, fg_color="transparent", height=90
        )
        self.genre_tags_frame.pack(fill="x", pady=(2, 0))

        self.refresh_genre_tags()

        self.event_timestamp.trace_add("write", lambda *args: self._schedule_update())

        # ── Saved Events Section (under Event Config) ────────────────────
        _event_tab = self.left_tabs.tab("Event")
        ctk.CTkLabel(
            _event_tab, text="Saved Events",
            font=T.FONT_BODY_BOLD, text_color=self.settings.get("text_primary", T.TEXT_PRIMARY)
        ).grid(row=2, column=0, sticky="w", padx=15, pady=(0, 5))

        self.saved_events_scroll = ctk.CTkScrollableFrame(_event_tab, fg_color="transparent")
        self.saved_events_scroll.grid(row=3, column=0, sticky="nsew", padx=6, pady=(0, 6))
        self.saved_events_scroll.grid_columnconfigure(0, weight=1)
        self._autohide_scrollbar(self.saved_events_scroll)
        self.refresh_saved_events_ui()

        # Balance scrollable areas: give both equal vertical space expansion
        _event_tab.grid_rowconfigure(1, weight=0)  # Config panel
        _event_tab.grid_rowconfigure(3, weight=1)  # Saved events panel

        # ── DJ Roster tab ──────────────────────────────────────────────────
        dj_roster_tab = self.left_tabs.tab("DJ Roster")
        dj_roster_hdr = ctk.CTkFrame(dj_roster_tab, fg_color="transparent")
        dj_roster_hdr.grid(row=0, column=0, sticky="ew", padx=8, pady=(4, 0))
        _lbl = ctk.CTkLabel(dj_roster_hdr, text="DJ ROSTER", font=T.FONT_BODY_BOLD, text_color=T.ACCENT)
        _lbl.pack(side="left")
        self._accent_labels.append(_lbl)
        ctk.CTkLabel(dj_roster_hdr, text="drag to add →", font=T.FONT_BODY_BOLD, text_color=T.DRAG_HINT).pack(side="left", padx=(8, 0))
        _btn = ctk.CTkButton(
            dj_roster_hdr, text="+ NEW DJ", width=80, height=T.WIDGET_H_SM,
            **T.BTN_PRIMARY, font=T.FONT_BODY_BOLD,
            command=self.add_new_dj_to_roster
        )
        _btn.pack(side="right")
        self._primary_buttons.append(_btn)
        ctk.CTkButton(
            dj_roster_hdr, text="⬇ LINKS", width=80, height=T.WIDGET_H_SM,
            **T.BTN_SECONDARY, font=T.FONT_BODY_BOLD,
            command=self.open_dj_link_import
        ).pack(side="right", padx=(0, 6))
        ctk.CTkEntry(
            dj_roster_hdr, textvariable=self.dj_search_var,
            placeholder_text="Search…", height=T.WIDGET_H_SM, width=130,
            fg_color=T.CARD_BG, border_color=T.BORDER
        ).pack(side="right", padx=(0, 6))
        self.dj_search_var.trace_add("write", lambda *_: self._schedule_roster_refresh())

        self.dj_roster_scroll = ctk.CTkScrollableFrame(dj_roster_tab, fg_color="transparent")
        self.dj_roster_scroll.grid(row=1, column=0, sticky="nsew", padx=8, pady=(4, 6))
        self.dj_roster_scroll.grid_columnconfigure(0, weight=1)
        self._autohide_scrollbar(self.dj_roster_scroll)
        self.refresh_dj_roster_ui()

        # ── Settings tab ───────────────────────────────────────────────────
        settings_tab = self.left_tabs.tab("Settings")
        # Settings UI is built in _build_settings_tab() called at the end

        slots_container_frame = ctk.CTkFrame(self.right_panel, fg_color="transparent")
        slots_container_frame.grid(row=0, column=0, sticky="nsew")
        slots_container_frame.grid_rowconfigure(1, weight=1)
        slots_container_frame.grid_columnconfigure(0, weight=1)

        slots_header = ctk.CTkFrame(slots_container_frame, fg_color="transparent")
        slots_header.grid(row=0, column=0, sticky="ew", padx=15, pady=(10, 5))

        ctk.CTkLabel(
            slots_header, text="Lineup", 
            font=T.FONT_BODY_BOLD, text_color=self.settings.get("text_primary", T.TEXT_PRIMARY)
        ).pack(side="left")

        _btn = ctk.CTkButton(
            slots_header, text="+ ADD DJ", command=self.add_slot,
            width=80, height=T.WIDGET_H_SM, **T.BTN_PRIMARY,
            font=T.FONT_BODY_BOLD
        )
        _btn.pack(side="right", padx=(5, 0))
        self._primary_buttons.append(_btn)

        dur_values = [str(x) for x in range(15, 121, 15)]
        self.master_dur_menu = ctk.CTkOptionMenu(
            slots_header,
            values=dur_values,
            variable=self.master_duration,
            height=T.WIDGET_H, width=90,
            **T.OPTION_MENU,
        )
        self.master_dur_menu.pack(side="right", padx=(0, 5))
        ctk.CTkLabel(slots_header, text="Default length:", font=T.FONT_BODY, text_color=T.TEXT_SECONDARY).pack(side="right", padx=(10, 5))
        self.master_duration.trace_add("write", lambda *args: self.apply_master_duration())

        self.slots_scroll = ctk.CTkScrollableFrame(slots_container_frame, fg_color="transparent")
        self.slots_scroll.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 0))
        self._autohide_scrollbar(self.slots_scroll)

        # Open Decks row
        self._od_row = ctk.CTkFrame(
            slots_container_frame, 
            fg_color=self.settings.get("card_bg", T.CARD_BG), 
            corner_radius=T.CARD_RADIUS,
            border_width=T.BORDER_W,
            border_color=self.settings.get("border_color", T.BORDER)
        )
        self._od_row.grid(row=2, column=0, sticky="ew", padx=15, pady=(2, 0))
        od_row = self._od_row

        self.od_toggle_btn = ctk.CTkCheckBox(
            od_row, text="OPEN DECKS", variable=self.include_od,
            command=self.toggle_od,
            font=T.FONT_BODY_BOLD, text_color=T.TEXT_SECONDARY,
            fg_color=T.PRIMARY, hover_color=T.PRIMARY_HOVER,
            checkmark_color=T.WHITE, border_color=T.BORDER
        )
        self.od_toggle_btn.pack(side="left", padx=(12, 16), pady=8)

        self.od_count_label = ctk.CTkLabel(od_row, text="Amount:", font=T.FONT_BODY, text_color=T.TEXT_MUTED)
        self.od_count_label.pack(side="left", padx=(0, 4))
        self.od_count_menu = ctk.CTkOptionMenu(
            od_row,
            values=[str(x) for x in range(1, 11)],
            variable=self.od_count,
            command=lambda _: self.update_output(),
            width=75, height=30, state="disabled",
            **T.OPTION_MENU_DISABLED,
        )
        self.od_count_menu.pack(side="left", padx=(0, 16))

        self.od_dur_label = ctk.CTkLabel(od_row, text="Slot length:", font=T.FONT_BODY, text_color=T.TEXT_MUTED)
        self.od_dur_label.pack(side="left", padx=(0, 4))
        self.od_dur_menu = ctk.CTkOptionMenu(
            od_row,
            values=[str(x) for x in range(15, 121, 15)],
            variable=self.od_duration,
            command=lambda _: self.update_output(),
            width=85, height=30, state="disabled",
            **T.OPTION_MENU_DISABLED,
        )
        self.od_dur_menu.pack(side="left", padx=(0, 8))

        # ==========================================
        # LINEUP TAB (BOTTOM): Output Preview
        # ==========================================
        _lineup_tab = self.right_panel

        self._preview_header = ctk.CTkFrame(
            _lineup_tab,
            fg_color=self.settings.get("panel_bg", T.PANEL_BG),
            corner_radius=0,
        )
        preview_header = self._preview_header
        preview_header.grid(row=1, column=0, sticky="ew")

        out_lbl = ctk.CTkLabel(
            preview_header, text="Output", 
            font=T.FONT_BODY_BOLD, text_color=self.settings.get("text_primary", T.TEXT_PRIMARY)
        )
        out_lbl.pack(anchor="w", padx=15, pady=(4, 0))

        buttons_row = ctk.CTkFrame(preview_header, fg_color="transparent")
        buttons_row.pack(fill="x", padx=0, pady=(4, 4))

        self.format_btn = ctk.CTkButton(
            buttons_row, text="Discord", image=self.icon_discord, compound="left",
            command=self.toggle_format,
            fg_color="transparent", hover_color=T.BORDER, border_width=T.BORDER_W, border_color=T.BORDER,
            text_color=T.ACCENT, width=110, height=T.WIDGET_H, font=T.FONT_BODY_BOLD
        )
        self.format_btn.pack(side="left", padx=(15, 4))

        self.plain_btn = ctk.CTkButton(
            buttons_row, text="Plain Text", image=self.icon_text, compound="left",
            command=self.set_plain_text,
            fg_color="transparent", hover_color=T.BORDER, border_width=T.BORDER_W, border_color=T.BORDER,
            text_color=T.TEXT_SECONDARY, width=110, height=T.WIDGET_H, font=T.FONT_BODY_BOLD
        )
        self.plain_btn.pack(side="left", padx=(0, 4))

        self.quest_btn = ctk.CTkButton(
            buttons_row, text="Quest", image=self.icon_quest, compound="left",
            command=self.set_quest_view,
            fg_color="transparent", hover_color=T.BORDER, border_width=T.BORDER_W, border_color=T.BORDER,
            text_color=T.TEXT_SECONDARY, width=110, height=T.WIDGET_H, font=T.FONT_BODY_BOLD
        )
        self.quest_btn.pack(side="left", padx=(0, 4))

        self.pc_btn = ctk.CTkButton(
            buttons_row, text="PC", image=self.icon_pc, compound="left",
            command=self.set_pc_view,
            fg_color="transparent", hover_color=T.BORDER, border_width=T.BORDER_W, border_color=T.BORDER,
            text_color=T.TEXT_SECONDARY, width=80, height=T.WIDGET_H, font=T.FONT_BODY_BOLD
        )
        self.pc_btn.pack(side="left")

        def _toggle_times():
            self.names_only.set(not self.names_only.get())
            self.update_output()

        self._times_toggle_btn = ctk.CTkButton(
            buttons_row, text="Times on",
            command=_toggle_times,
            fg_color="transparent", hover_color=T.BORDER,
            text_color=T.TEXT_SECONDARY, width=76, height=T.WIDGET_H,
            font=T.FONT_SMALL_BOLD, border_width=T.BORDER_W, border_color=T.BORDER
        )
        self._times_toggle_btn.pack(side="right", padx=(0, 15))

        def _sync_times_btn(*_):
            if self.names_only.get():
                self._times_toggle_btn.configure(text="Times off", text_color=T.ERROR)
            else:
                self._times_toggle_btn.configure(text="Times on", text_color=T.TEXT_SECONDARY)
        self.names_only.trace_add("write", _sync_times_btn)

        output_container = ctk.CTkFrame(_lineup_tab, fg_color="transparent")
        output_container.grid(row=2, column=0, sticky="nsew", padx=12, pady=(0, 12))
        output_container.grid_columnconfigure(0, weight=1)
        output_container.grid_rowconfigure(0, weight=1)
        _lineup_tab.grid_rowconfigure(2, weight=1)

        self.output_text = ctk.CTkTextbox(
            output_container,
            fg_color=self.settings.get("card_bg", T.CARD_BG),
            text_color=self.settings.get("text_primary", T.TEXT_PRIMARY),
            font=("Consolas", self.settings.get("output_font_size", 14)),
            wrap="word", border_width=T.BORDER_W,
            border_color=self.settings.get("border_color", T.BORDER),
            corner_radius=T.CARD_RADIUS,
        )
        self.output_text.grid(row=0, column=0, sticky="nsew")

        self.copy_icon_btn = ctk.CTkButton(
            output_container, text="⎘", command=self.copy_template,
            width=32, height=32, corner_radius=6,
            fg_color=self.settings.get("border_color", T.BORDER),
            hover_color=self.settings.get("primary_color", T.PRIMARY),
            text_color=self.settings.get("text_secondary", T.TEXT_SECONDARY), font=("Arial", 15)
        )
        self.copy_icon_btn.place_forget()
        self.output_text.bind("<Enter>", lambda e: self.copy_icon_btn.place(relx=1.0, rely=0.0, x=-10, y=10, anchor="ne"))
        self.output_text.bind("<Leave>", self._on_output_leave)
        self.copy_icon_btn.bind("<Enter>", lambda e: self.copy_icon_btn.place(relx=1.0, rely=0.0, x=-10, y=10, anchor="ne"))
        self.copy_icon_btn.bind("<Leave>", self._on_output_leave)

        self._build_settings_tab()
        self.apply_theme()

    # ── Scrollbar helper ──────────────────────────────────────────────────

    def _autohide_scrollbar(self, sf: ctk.CTkScrollableFrame) -> None:
        """
        Hide the scrollbar on a CTkScrollableFrame when the content height
        is less than or equal to the visible canvas height.
        """
        frames = self.__dict__.setdefault("_scrollable_frames", [])
        if sf not in frames:
            frames.append(sf)

        pending_job = [None]

        def schedule_check(event=None):
            if pending_job[0] is not None:
                return  # already scheduled

            def do_check():
                pending_job[0] = None
                sf.update_idletasks()

                bbox = sf._parent_canvas.bbox("all")
                if bbox is None:
                    sf._scrollbar.grid_remove()
                    return

                content_height = bbox[3] - bbox[1]
                visible_height = sf._parent_canvas.winfo_height()

                if content_height > visible_height:
                    sf._scrollbar.grid()
                else:
                    sf._scrollbar.grid_remove()

            pending_job[0] = sf.after(80, do_check)

        sf._parent_canvas.bind("<Configure>", lambda e: schedule_check(), add="+")
        sf._parent_frame.bind("<Configure>", lambda e: schedule_check(), add="+")
        sf.bind("<Configure>", lambda e: schedule_check(), add="+")

    # ── UI Component Helpers ─────────────────────────────────────────────

    def _create_left_tabs(self, left_panel: ctk.CTkFrame) -> None:
        # Left panel tabview
        self.left_tabs = ctk.CTkTabview(
            left_panel,
            fg_color="transparent",
            bg_color="transparent",
            segmented_button_fg_color=self.settings.get("panel_bg", T.PANEL_BG),
            segmented_button_unselected_color=self.settings.get("panel_bg", T.PANEL_BG),
            segmented_button_selected_color=self.settings.get("border_color", T.BORDER),
        )
        self.left_tabs.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        self.left_tabs.add("Event")
        self.left_tabs.add("DJ Roster")
        self.left_tabs.add("Settings")

    def _create_scrollable_frame(
        self,
        parent,
        *,
        row: int = 0,
        column: int = 0,
        padx=0,
        pady=0,
        sticky: str = "nsew",
        autohide: bool = True,
    ) -> ctk.CTkScrollableFrame:
        sf = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        sf.grid(row=row, column=column, sticky=sticky, padx=padx, pady=pady)
        sf.grid_columnconfigure(0, weight=1)

        if autohide:
            self._autohide_scrollbar(sf)

        return sf

    def _create_scroll_containers(self, _event_tab, _saved_outer, dj_roster_tab,
                                  slots_container_frame, settings_tab, genre_popup_win) -> None:
        # Event configuration scroll
        self._event_config_panel = self._create_scrollable_frame(
            _event_tab,
            row=1,
            column=0,
            sticky="nsew",
        )

        # Saved events list scroll
        self.saved_events_scroll = self._create_scrollable_frame(
            _saved_outer,
            row=0,
            column=0,
            sticky="nsew",
        )

        # DJ roster scroll
        self.dj_roster_scroll = self._create_scrollable_frame(
            dj_roster_tab,
            row=1,
            column=0,
            padx=8,
            pady=(4, 6),
            sticky="nsew",
        )

        # Lineup slots scroll
        self.slots_scroll = self._create_scrollable_frame(
            slots_container_frame,
            row=1,
            column=0,
            padx=10,
            pady=(0, 0),
            sticky="nsew",
        )

        # Settings scroll
        self.settings_scroll = self._create_scrollable_frame(
            settings_tab,
            row=0,
            column=0,
            sticky="nsew",
        )

        # Genre editor popup scroll (uses pack instead of grid)
        self.genre_editor_scroll = ctk.CTkScrollableFrame(genre_popup_win, fg_color="transparent")
        self.genre_editor_scroll.pack(fill="both", expand=True, padx=12, pady=(4, 12))
        self.genre_editor_scroll.grid_columnconfigure(0, weight=1)

    def _is_over_slots_panel(self, x_root: int, y_root: int) -> bool:
        """Return True if screen coordinates are within self.slots_scroll."""
        try:
            sx = self.slots_scroll.winfo_rootx()
            sy = self.slots_scroll.winfo_rooty()
            sw = self.slots_scroll.winfo_width()
            sh = self.slots_scroll.winfo_height()
        except Exception:
            return False

        return sx <= x_root <= sx + sw and sy <= y_root <= sy + sh

    def _enable_roster_wheel_scroll(self, roster_body: ctk.CTkFrame) -> None:
        """Forward mouse wheel events from children to the DJ roster scroll canvas."""
        roster_canvas = self.dj_roster_scroll._parent_canvas

        def _forward_scroll(e):
            roster_canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")

        def _bind_recursive(widget):
            widget.bind("<MouseWheel>", _forward_scroll, add="+")
            for child in widget.winfo_children():
                _bind_recursive(child)

        _bind_recursive(roster_body)

