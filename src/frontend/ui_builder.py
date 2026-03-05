"""
Module: ui_builder.py
Purpose: Builds the entire application UI layout (Dear PyGui).
Architecture: Mixin for App class.
"""
import dearpygui.dearpygui as dpg

from . import theme as T
from .date_time_picker import add_datetime_row
from .fonts import Icon


class UISetupMixin:
    """Builds the entire application UI and provides helpers."""

    def setup_ui(self):
        with dpg.window(tag="primary_window", no_title_bar=True, no_resize=True,
                        no_move=True, no_scrollbar=True,
                        no_scroll_with_mouse=True):
            with dpg.table(header_row=False, resizable=True, borders_innerV=True,
                           scrollX=False, scrollY=False):
                dpg.add_table_column(init_width_or_weight=380.0, width_fixed=True)
                dpg.add_table_column()
                with dpg.table_row():
                    with dpg.child_window(border=False, no_scrollbar=True):
                        self._build_left_panel()
                    with dpg.child_window(border=False, no_scrollbar=True):
                        self._build_right_panel()

        dpg.set_primary_window("primary_window", True)
        self._build_settings_tab()
        self.apply_theme()

    # ── Left panel ────────────────────────────────────────────────────────

    def _build_left_panel(self):
        with dpg.tab_bar(tag="left_tabs"):
            with dpg.tab(label="Event", tag="Event"):
                self._build_event_tab()
            with dpg.tab(label="DJ Roster", tag="DJ Roster"):
                self._build_dj_roster_tab()
            with dpg.tab(label="Settings", tag="Settings"):
                with dpg.child_window(tag="settings_scroll", height=-1,
                                      border=False, autosize_x=True):
                    pass  # populated by _build_settings_tab()

    def _build_event_tab(self):
        # ── Header row ────────────────────────────────────────────────────
        dpg.add_text("EVENT CONFIGURATION", color=T.DPG_ACCENT)
        with dpg.table(header_row=False, borders_innerH=False, borders_innerV=True,
                       borders_outerH=False, borders_outerV=False, pad_outerX=False):
            dpg.add_table_column()
            dpg.add_table_column()
            dpg.add_table_column()
            with dpg.table_row():
                dpg.add_button(label=Icon.PASTE + " Import", width=-1,
                               callback=lambda: self.open_import_dialog())
                dpg.add_button(label=Icon.SAVE + " Save", width=-1,
                               callback=lambda: self.save_event_lineup())
                dpg.add_button(label=Icon.ADD + " New", width=-1,
                               callback=lambda: self.new_event())
        dpg.add_separator()

        # ── Event title + vol ─────────────────────────────────────────────
        dpg.add_text("EVENT TITLE", color=T.DPG_TEXT_SECONDARY)
        with dpg.group(horizontal=True):
            dpg.add_input_text(
                tag="event_title_input",
                default_value=self.event_title_var.get(),
                hint="Event title...", width=-70,
                callback=lambda s, a: self._schedule_update(),
            )
            dpg.add_text("Vol.")
            dpg.add_input_text(
                tag="event_vol_input",
                default_value=self.event_vol_var.get(),
                width=55,
                callback=lambda s, a: self._schedule_update(),
            )
        self.event_title_var._tag = "event_title_input"
        self.event_vol_var._tag   = "event_vol_input"

        # ── Timestamp ─────────────────────────────────────────────────────
        dpg.add_text("EVENT START TIMESTAMP", color=T.DPG_TEXT_SECONDARY)
        add_datetime_row(
            "event_timestamp_input", self.event_timestamp,
            callback=lambda s, a: self._schedule_update(),
        )
        dpg.add_separator()

        # ── Genres ────────────────────────────────────────────────────────
        dpg.add_text("GENRES (Press Enter to add)", color=T.DPG_TEXT_SECONDARY)
        with dpg.group(horizontal=True):
            dpg.add_input_text(
                tag="genre_entry",
                default_value=self.genre_entry_var.get(),
                hint="Type and press Enter...", width=-85,
                on_enter=True,
                callback=lambda s, a: self.add_genre_from_entry(),
            )
        with dpg.table(header_row=False, borders_innerH=False, borders_innerV=True,
                       borders_outerH=False, borders_outerV=False, pad_outerX=False):
            dpg.add_table_column()
            dpg.add_table_column()
            with dpg.table_row():
                dpg.add_button(label=Icon.EDIT + " Edit Genres", width=-1,
                               callback=lambda: self.open_genre_editor())
                dpg.add_button(label=Icon.DELETE + " Delete Genre", width=-1,
                               callback=lambda: self.delete_saved_genre())
        self.genre_entry_var._tag = "genre_entry"

        dpg.add_text("SAVED GENRES", color=T.DPG_TEXT_MUTED)
        with dpg.child_window(tag="genre_tags_frame", height=90,
                              border=False, autosize_x=True):
            pass  # populated by refresh_genre_tags()
        dpg.add_separator()

        # ── Saved Events ──────────────────────────────────────────────────
        dpg.add_text("Saved Events", color=T.DPG_TEXT_PRIMARY)
        with dpg.child_window(tag="saved_events_scroll", height=-1,
                              border=False, autosize_x=True):
            pass  # populated by refresh_saved_events_ui()

        self.refresh_genre_tags()
        self.refresh_saved_events_ui()

    def _build_dj_roster_tab(self):
        with dpg.group(horizontal=True):
            dpg.add_text("DJ ROSTER", color=T.DPG_ACCENT)
            dpg.add_text(" drag to add →", color=T.DPG_DRAG_HINT)
        dpg.add_input_text(
            tag="dj_search_input",
            default_value=self.dj_search_var.get(),
            hint="Search...", width=-1,
            callback=lambda s, a: self._schedule_roster_refresh(),
        )
        self.dj_search_var._tag = "dj_search_input"
        with dpg.table(header_row=False, borders_innerH=False, borders_innerV=True,
                       borders_outerH=False, borders_outerV=False, pad_outerX=False):
            dpg.add_table_column()
            dpg.add_table_column()
            with dpg.table_row():
                dpg.add_button(label=Icon.ADD + " New DJ", width=-1,
                               callback=lambda: self.add_new_dj_to_roster())
                dpg.add_button(label=Icon.DOWNLOAD + " Links", width=-1,
                               callback=lambda: self.open_dj_link_import())
        with dpg.child_window(tag="dj_roster_scroll", height=-1,
                              border=False, autosize_x=True):
            pass  # populated by refresh_dj_roster_ui()
        self.refresh_dj_roster_ui()

    # ── Right panel ───────────────────────────────────────────────────────

    def _build_right_panel(self):
        # ── Lineup header ─────────────────────────────────────────────────
        with dpg.group(horizontal=True):
            dpg.add_text("Lineup", color=T.DPG_TEXT_PRIMARY)
            dpg.add_text("Default length:", color=T.DPG_TEXT_SECONDARY)
            dur_values = [str(x) for x in range(15, 121, 15)]
            dpg.add_combo(
                tag="master_dur_combo",
                items=dur_values,
                default_value=self.master_duration.get(),
                width=80,
                callback=lambda s, a: self.apply_master_duration(),
            )
            self.master_duration._tag = "master_dur_combo"
            dpg.add_button(label=Icon.ADD + " Add DJ", width=90,
                           callback=lambda: self.add_slot())

        # ── Slots scroll area ─────────────────────────────────────────────
        with dpg.child_window(tag="slots_scroll", height=320,
                              border=True, autosize_x=True):
            pass  # populated by slot_manager

        # ── Open Decks row ────────────────────────────────────────────────
        with dpg.group(horizontal=True):
            dpg.add_checkbox(
                tag="od_toggle", label="OPEN DECKS",
                default_value=self.include_od.get(),
                callback=lambda s, a: self.toggle_od(),
            )
            self.include_od._tag = "od_toggle"
            dpg.add_text("  Amount:", color=T.DPG_TEXT_MUTED)
            dpg.add_combo(
                tag="od_count_combo",
                items=[str(x) for x in range(1, 11)],
                default_value=self.od_count.get(),
                width=75, enabled=False,
                callback=lambda s, a: self.update_output(),
            )
            self.od_count._tag = "od_count_combo"
            dpg.add_text("  Slot length:", color=T.DPG_TEXT_MUTED)
            dpg.add_combo(
                tag="od_dur_combo",
                items=[str(x) for x in range(15, 121, 15)],
                default_value=self.od_duration.get(),
                width=85, enabled=False,
                callback=lambda s, a: self.update_output(),
            )
            self.od_duration._tag = "od_dur_combo"
        dpg.add_separator()

        # ── Output preview ────────────────────────────────────────────────
        dpg.add_text("Output", color=T.DPG_TEXT_PRIMARY)
        with dpg.table(header_row=False, borders_innerH=False, borders_innerV=True,
                       borders_outerH=False, borders_outerV=False, pad_outerX=False):
            for _ in range(5):
                dpg.add_table_column()
            with dpg.table_row():
                dpg.add_button(tag="fmt_discord", label=Icon.CHAT + " Discord", width=-1,
                               callback=lambda: self.toggle_format())
                dpg.add_button(tag="fmt_plain",   label=Icon.NOTES + " Plain",   width=-1,
                               callback=lambda: self.set_plain_text())
                dpg.add_button(tag="fmt_quest",   label=Icon.VR + " Quest",      width=-1,
                               callback=lambda: self.set_quest_view())
                dpg.add_button(tag="fmt_pc",      label=Icon.COMPUTER + " PC",   width=-1,
                               callback=lambda: self.set_pc_view())
                dpg.add_button(tag="fmt_times",   label=Icon.SCHEDULE + " Times on", width=-1,
                               callback=lambda: self._toggle_times())

        dpg.add_input_text(
            tag="output_text",
            multiline=True, readonly=True,
            width=-1, height=-1,
        )

    # ── Helpers ───────────────────────────────────────────────────────────

    def _toggle_times(self):
        self.names_only.set(not self.names_only.get())
        label = Icon.SCHEDULE + " Times off" if self.names_only.get() else Icon.SCHEDULE + " Times on"
        if dpg.does_item_exist("fmt_times"):
            dpg.configure_item("fmt_times", label=label)
        self.update_output()

    def _is_over_slots_panel(self, x_root: int, y_root: int) -> bool:
        try:
            mn = dpg.get_item_rect_min("slots_scroll")
            mx = dpg.get_item_rect_max("slots_scroll")
        except Exception:
            return False
        return mn[0] <= x_root <= mx[0] and mn[1] <= y_root <= mx[1]



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
            fg_color=T.CARD_BG, border_color=T.BORDER, corner_radius=6
        ).pack(side="right", padx=(0, 6))
        self.dj_search_var.trace_add("write", lambda *_: self._schedule_roster_refresh())

        self.dj_roster_scroll = self._create_scrollable_frame(
            dj_roster_tab, row=1, column=0, padx=8, pady=(4, 6), sticky="nsew"
        )
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

        dur_values =[str(x) for x in range(15, 121, 15)]
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

        self.slots_scroll = self._create_scrollable_frame(
            slots_container_frame, row=1, column=0, padx=10, pady=(0, 0), sticky="nsew"
        )

        # Open Decks row
        self._od_row = ctk.CTkFrame(
            slots_container_frame, 
            fg_color=self.settings.get("card_bg", T.CARD_BG), 
            corner_radius=T.CARD_RADIUS,
            border_width=T.BORDER_W,
            border_color=self.settings.get("border_color", T.BORDER)
        )
        self._od_row.grid(row=2, column=0, sticky="ew", padx=15, pady=(6, 6))
        od_row = self._od_row

        self.od_toggle_btn = ctk.CTkCheckBox(
            od_row, text="OPEN DECKS", variable=self.include_od,
            command=self.toggle_od,
            font=T.FONT_BODY_BOLD, text_color=T.TEXT_SECONDARY,
            fg_color=T.PRIMARY, hover_color=T.PRIMARY_HOVER,
            checkmark_color=T.WHITE, border_color=T.BORDER, corner_radius=6
        )
        self.od_toggle_btn.pack(side="left", padx=(16, 16), pady=12)

        self.od_count_label = ctk.CTkLabel(od_row, text="Amount:", font=T.FONT_BODY, text_color=T.TEXT_MUTED)
        self.od_count_label.pack(side="left", padx=(0, 6))
        self.od_count_menu = ctk.CTkOptionMenu(
            od_row,
            values=[str(x) for x in range(1, 11)],
            variable=self.od_count,
            command=lambda _: self.update_output(),
            width=75, height=30, state="disabled",
            **T.OPTION_MENU_DISABLED,
        )
        self.od_count_menu.pack(side="left", padx=(0, 20))

        self.od_dur_label = ctk.CTkLabel(od_row, text="Slot length:", font=T.FONT_BODY, text_color=T.TEXT_MUTED)
        self.od_dur_label.pack(side="left", padx=(0, 6))
        self.od_dur_menu = ctk.CTkOptionMenu(
            od_row,
            values=[str(x) for x in range(15, 121, 15)],
            variable=self.od_duration,
            command=lambda _: self.update_output(),
            width=85, height=30, state="disabled",
            **T.OPTION_MENU_DISABLED,
        )
        self.od_dur_menu.pack(side="left", padx=(0, 16))

        # ==========================================
        # LINEUP TAB (BOTTOM): Output Preview
        # ==========================================
        _lineup_tab = self.right_panel

        self._preview_header = ctk.CTkFrame(
            _lineup_tab,
            fg_color="transparent",
            corner_radius=0,
        )
        preview_header = self._preview_header
        preview_header.grid(row=1, column=0, sticky="ew")

        out_lbl = ctk.CTkLabel(
            preview_header, text="Output", 
            font=T.FONT_BODY_BOLD, text_color=self.settings.get("text_primary", T.TEXT_PRIMARY)
        )
        out_lbl.pack(anchor="w", padx=10, pady=(0, 0))

        buttons_row = ctk.CTkFrame(preview_header, fg_color="transparent", corner_radius=0)
        buttons_row.pack(fill="x", padx=0, pady=(0, 4))

        self.format_btn = ctk.CTkButton(
            buttons_row, text="Discord", image=self.icon_discord, compound="left",
            command=self.toggle_format, corner_radius=6,
            fg_color="transparent", hover_color=T.BORDER, border_width=T.BORDER_W, border_color=T.BORDER,
            text_color=T.ACCENT, width=105, height=T.WIDGET_H, font=T.FONT_BODY_BOLD
        )
        self.format_btn.pack(side="left", padx=(15, 4))

        self.plain_btn = ctk.CTkButton(
            buttons_row, text="Plain Text", image=self.icon_text, compound="left",
            command=self.set_plain_text, corner_radius=6,
            fg_color="transparent", hover_color=T.BORDER, border_width=T.BORDER_W, border_color=T.BORDER,
            text_color=T.TEXT_SECONDARY, width=105, height=T.WIDGET_H, font=T.FONT_BODY_BOLD
        )
        self.plain_btn.pack(side="left", padx=(0, 4))

        self.quest_btn = ctk.CTkButton(
            buttons_row, text="Quest", image=self.icon_quest, compound="left",
            command=self.set_quest_view, corner_radius=6,
            fg_color="transparent", hover_color=T.BORDER, border_width=T.BORDER_W, border_color=T.BORDER,
            text_color=T.TEXT_SECONDARY, width=105, height=T.WIDGET_H, font=T.FONT_BODY_BOLD
        )
        self.quest_btn.pack(side="left", padx=(0, 4))

        self.pc_btn = ctk.CTkButton(
            buttons_row, text="PC", image=self.icon_pc, compound="left",
            command=self.set_pc_view, corner_radius=6,
            fg_color="transparent", hover_color=T.BORDER, border_width=T.BORDER_W, border_color=T.BORDER,
            text_color=T.TEXT_SECONDARY, width=80, height=T.WIDGET_H, font=T.FONT_BODY_BOLD
        )
        self.pc_btn.pack(side="left")

        def _toggle_times():
            self.names_only.set(not self.names_only.get())
            self.update_output()

        self._times_toggle_btn = ctk.CTkButton(
            buttons_row, text="Times on",
            command=_toggle_times, corner_radius=6,
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
            text_color=self.settings.get("text_primary", T.TEXT_PRIMARY),
            font=("Consolas", self.settings.get("output_font_size", 14)),
            wrap="word", border_width=T.BORDER_W,
            border_color=self.settings.get("border_color", T.BORDER),
            corner_radius=T.CARD_RADIUS,
            scrollbar_button_color=self.settings.get("scrollbar_color", T.SCROLLBAR),
            scrollbar_button_hover_color=self.settings.get("scrollbar_color", T.SCROLLBAR)
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

