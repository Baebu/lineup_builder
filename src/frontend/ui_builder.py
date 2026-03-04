import customtkinter as ctk
from .date_time_picker import CTkDateTimePicker
from tkinter import messagebox


class UISetupMixin:
    """Builds the entire application UI and provides title management helpers."""

    def setup_ui(self):
        # Ensure theme-tracking lists exist even if load_settings() hasn't run yet
        for _attr in ("_accent_labels", "_primary_buttons", "_danger_buttons",
                      "_success_buttons", "_scrollable_frames"):
            self.__dict__.setdefault(_attr, [])

        # Grid Layout
        self.grid_columnconfigure(0, weight=0, minsize=320)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=3, uniform="row")
        self.grid_rowconfigure(1, weight=2, uniform="row")

        # ==========================================
        # LEFT PANEL: Configuration & Settings
        # ==========================================
        left_panel = ctk.CTkFrame(self, fg_color="transparent", width=320)
        left_panel.grid(row=0, column=0, rowspan=2, padx=(20, 10), pady=(5, 20), sticky="nsew")
        left_panel.grid_propagate(False)
        left_panel.grid_columnconfigure(0, weight=1)
        left_panel.grid_rowconfigure(0, weight=1)

        self.left_tabs = ctk.CTkTabview(left_panel, fg_color="#1E293B", corner_radius=10, border_width=1, border_color="#334155")
        self.left_tabs.grid(row=0, column=0, sticky="nsew")

        self.left_tabs.add("Event")
        self.left_tabs.add("DJ Roster")
        self.left_tabs.add("Settings")

        self.left_tabs.tab("Event").grid_columnconfigure(0, weight=1)
        self.left_tabs.tab("Event").grid_rowconfigure(0, weight=0)
        self.left_tabs.tab("Event").grid_rowconfigure(1, weight=1)
        self.left_tabs.tab("DJ Roster").grid_columnconfigure(0, weight=1)
        self.left_tabs.tab("DJ Roster").grid_rowconfigure(0, weight=0)
        self.left_tabs.tab("DJ Roster").grid_rowconfigure(1, weight=1)
        self.left_tabs.tab("Settings").grid_columnconfigure(0, weight=1)
        self.left_tabs.tab("Settings").grid_rowconfigure(0, weight=1)

        # ── Event tab ─────────────────────────────────────────────────────
        _event_tab = self.left_tabs.tab("Event")

        # Shared header (always visible)
        config_header = ctk.CTkFrame(_event_tab, fg_color="transparent")
        config_header.grid(row=0, column=0, sticky="ew", padx=15, pady=(5, 5))
        self._event_header_lbl = ctk.CTkLabel(
            config_header, text="EVENT CONFIGURATION",
            font=("Arial", 11, "bold"), text_color="#818CF8"
        )
        self._event_header_lbl.pack(side="left")
        self._accent_labels.append(self._event_header_lbl)
        ctk.CTkButton(
            config_header, text="\U0001F4CB Import", width=90, height=26,
            fg_color="#334155", hover_color="#475569",
            font=("Arial", 10, "bold"), text_color="#94A3B8",
            command=self.open_import_dialog,
        ).pack(side="right")
        ctk.CTkButton(
            config_header, text="+ NEW", width=70, height=26,
            fg_color="#334155", hover_color="#475569",
            font=("Arial", 10, "bold"), text_color="#CBD5E1",
            command=self.new_event,
        ).pack(side="right", padx=(0, 4))
        self._saved_panel_btn = ctk.CTkButton(
            config_header, text="Saved", width=70, height=26,
            fg_color="#059669", hover_color="#047857",
            font=("Arial", 10, "bold"), text_color="#FFFFFF",
            command=self._toggle_event_panel,
        )
        self._saved_panel_btn.pack(side="right", padx=(0, 4))

        # ── Event config panel (default) ──────────────────────────────────
        config_frame = ctk.CTkScrollableFrame(_event_tab, fg_color="transparent")
        config_frame.grid(row=1, column=0, sticky="nsew")
        config_frame.grid_columnconfigure(0, weight=1)
        self._autohide_scrollbar(config_frame)
        self._event_config_panel = config_frame

        config_grid = ctk.CTkFrame(config_frame, fg_color="transparent")
        config_grid.pack(fill="x", expand=False, padx=15, pady=(0, 15))
        config_grid.grid_columnconfigure((0, 1), weight=1)

        # Title
        title_frame = ctk.CTkFrame(config_grid, fg_color="transparent")
        title_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=5)
        ctk.CTkLabel(title_frame, text="EVENT TITLE", font=("Arial", 9, "bold"), text_color="#94A3B8").pack(anchor="w")

        title_input_frame = ctk.CTkFrame(title_frame, fg_color="transparent")
        title_input_frame.pack(fill="x", pady=(2, 0))
        title_input_frame.grid_columnconfigure(0, weight=1)

        self.title_combo = ctk.CTkComboBox(
            title_input_frame,
            variable=self.event_title_var,
            values=self.saved_titles,
            height=35,
            fg_color="#0F172A",
            border_color="#334155",
            button_color="#334155",
            button_hover_color="#475569",
            dropdown_fg_color="#1E293B",
            dropdown_text_color="#CBD5E1",
            dropdown_hover_color="#334155",
            command=lambda v: self.update_output()
        )
        self.title_combo.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        self.event_title_var.trace_add("write", lambda *args: self._schedule_update())

        vol_frame = ctk.CTkFrame(title_input_frame, fg_color="transparent")
        vol_frame.grid(row=0, column=1, padx=(0, 5))
        ctk.CTkLabel(vol_frame, text="Vol.", font=("Arial", 11, "bold"), text_color="#94A3B8").pack(side="left", padx=(0, 3))
        self.vol_entry = ctk.CTkEntry(
            vol_frame,
            textvariable=self.event_vol_var,
            width=40, height=35,
            fg_color="#0F172A", border_color="#334155"
        )
        self.vol_entry.pack(side="left")
        self.event_vol_var.trace_add("write", lambda *args: self._schedule_update())

        btn_frame = ctk.CTkFrame(title_input_frame, fg_color="transparent")
        btn_frame.grid(row=0, column=2)
        _btn = ctk.CTkButton(
            btn_frame, text="", image=self.icon_trash, width=34, height=34,
            fg_color="#7F1D1D", hover_color="#991B1B",
            command=self.delete_saved_title
        )
        _btn.pack(side="left")
        self._danger_buttons.append(_btn)

        # Trigger auto-save when user commits the title (Enter or focus-out)
        def _on_title_commit(*_):
            if self.event_title_var.get().strip():
                self._auto_event_save()
        self.title_combo._entry.bind("<Return>", _on_title_commit)
        self.title_combo._entry.bind("<FocusOut>", _on_title_commit)

        # Date & Time
        timestamp_frame = ctk.CTkFrame(config_grid, fg_color="transparent")
        timestamp_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=5)
        ctk.CTkLabel(timestamp_frame, text="EVENT START TIMESTAMP", font=("Arial", 9, "bold"), text_color="#94A3B8").pack(anchor="w")
        CTkDateTimePicker(timestamp_frame, variable=self.event_timestamp).pack(fill="x", pady=(2, 0))

        # Genres
        genre_frame = ctk.CTkFrame(config_grid, fg_color="transparent")
        genre_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=5)
        ctk.CTkLabel(genre_frame, text="GENRES (Press Enter to add)", font=("Arial", 9, "bold"), text_color="#94A3B8").pack(anchor="w")

        genre_input_frame = ctk.CTkFrame(genre_frame, fg_color="transparent")
        genre_input_frame.pack(fill="x", pady=(2, 0))
        genre_input_frame.grid_columnconfigure(0, weight=1)

        self.genre_entry = ctk.CTkEntry(
            genre_input_frame, textvariable=self.genre_entry_var,
            placeholder_text="Type and press Enter...",
            fg_color="#0F172A", border_width=1, border_color="#334155", height=35
        )
        self.genre_entry.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        self.genre_entry.bind("<Return>", self.add_genre_from_entry)

        ctk.CTkButton(
            genre_input_frame, text="", image=self.icon_edit, width=34, height=34,
            fg_color="#334155", hover_color="#475569",
            command=self.open_genre_editor
        ).grid(row=0, column=1, padx=(5, 0))

        self.genre_del_btn = ctk.CTkButton(
            genre_input_frame, text="", image=self.icon_trash, width=34, height=34,
            fg_color="#7F1D1D", hover_color="#991B1B",
            command=self.delete_saved_genre
        )
        self.genre_del_btn.grid(row=0, column=2, padx=(5, 0))
        self._danger_buttons.append(self.genre_del_btn)

        # ── Collapsible genre drawer ────────────────────────────────────
        self._genre_drawer_open = True

        drawer_hdr = ctk.CTkFrame(genre_frame, fg_color="transparent")
        drawer_hdr.pack(fill="x", pady=(6, 0))
        drawer_hdr.grid_columnconfigure(0, weight=1)

        self._genre_drawer_chevron = ctk.CTkLabel(
            drawer_hdr, text="▾  SAVED GENRES",
            font=("Arial", 10, "bold"), text_color="#475569",
            cursor="hand2", anchor="w",
        )
        self._genre_drawer_chevron.grid(row=0, column=0, sticky="w")
        self._genre_drawer_chevron.bind("<Button-1>", lambda e: self._toggle_genre_drawer())

        import tkinter as tk
        _BTN_ROW_H = 28  # button height (26) + pady (1+1)
        _DRAWER_H = _BTN_ROW_H * 2

        _drawer_outer = ctk.CTkFrame(genre_frame, fg_color="transparent", height=_DRAWER_H)
        _drawer_outer.pack(fill="x", pady=(2, 0))
        _drawer_outer.pack_propagate(False)
        self._genre_drawer_body = _drawer_outer

        _canvas = tk.Canvas(
            _drawer_outer, height=_DRAWER_H, bd=0, highlightthickness=0,
            bg="#1E293B",
        )
        _scrollbar = ctk.CTkScrollbar(
            _drawer_outer, orientation="vertical", command=_canvas.yview,
            button_color="#334155", button_hover_color="#475569", width=10,
        )
        _canvas.configure(yscrollcommand=_scrollbar.set)
        _scrollbar.pack(side="right", fill="y")
        _canvas.pack(side="left", fill="both", expand=True)

        self.genre_tags_frame = ctk.CTkFrame(_canvas, fg_color="transparent")
        _canvas_window = _canvas.create_window((0, 0), window=self.genre_tags_frame, anchor="nw")
        self._genre_canvas_window = _canvas_window

        def _on_canvas_resize(event):
            _canvas.itemconfig(_canvas_window, width=event.width)
        _canvas.bind("<Configure>", _on_canvas_resize)

        # Mouse-wheel scrolling — bind directly to canvas; focus it on hover
        _canvas.bind("<Enter>", lambda e: _canvas.focus_set())
        _canvas.bind("<MouseWheel>", lambda e: _canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))

        self._genre_canvas = _canvas  # keep ref for reflow width queries

        self.refresh_genre_tags()

        self.event_timestamp.trace_add("write", lambda *args: self._schedule_update())

        # ── Saved events panel (alt view, hidden by default) ──────────────
        _saved_outer = ctk.CTkFrame(_event_tab, fg_color="transparent")
        _saved_outer.grid_columnconfigure(0, weight=1)
        _saved_outer.grid_rowconfigure(0, weight=1)
        self._event_saved_panel = _saved_outer

        self.saved_events_scroll = ctk.CTkScrollableFrame(_saved_outer, fg_color="transparent")
        self.saved_events_scroll.grid(row=0, column=0, sticky="nsew")
        self.saved_events_scroll.grid_columnconfigure(0, weight=1)
        self._autohide_scrollbar(self.saved_events_scroll)
        self.refresh_saved_events_ui()

        # ── DJ Roster tab ──────────────────────────────────────────────────
        dj_roster_tab = self.left_tabs.tab("DJ Roster")
        dj_roster_hdr = ctk.CTkFrame(dj_roster_tab, fg_color="transparent")
        dj_roster_hdr.grid(row=0, column=0, sticky="ew", padx=8, pady=(4, 0))
        _lbl = ctk.CTkLabel(dj_roster_hdr, text="DJ ROSTER", font=("Arial", 11, "bold"), text_color="#818CF8")
        _lbl.pack(side="left")
        self._accent_labels.append(_lbl)
        ctk.CTkLabel(dj_roster_hdr, text="drag to add →", font=("Arial", 11, "bold"), text_color="#B9B9B9").pack(side="left", padx=(8, 0))
        _btn = ctk.CTkButton(
            dj_roster_hdr, text="+ NEW DJ", width=80, height=32,
            fg_color="#4F46E5", hover_color="#4338CA", font=("Arial", 11, "bold"),
            command=self.add_new_dj_to_roster
        )
        _btn.pack(side="right")
        self._primary_buttons.append(_btn)
        ctk.CTkEntry(
            dj_roster_hdr, textvariable=self.dj_search_var,
            placeholder_text="Search…", height=32, width=130,
            fg_color="#0F172A", border_color="#334155"
        ).pack(side="right", padx=(0, 6))
        self.dj_search_var.trace_add("write", lambda *_: self._schedule_roster_refresh())

        self.dj_roster_scroll = ctk.CTkScrollableFrame(dj_roster_tab, fg_color="transparent")
        self.dj_roster_scroll.grid(row=1, column=0, sticky="nsew", padx=8, pady=(4, 6))
        self.dj_roster_scroll.grid_columnconfigure(0, weight=1)
        self._autohide_scrollbar(self.dj_roster_scroll)
        self.refresh_dj_roster_ui()

        # ==========================================
        # RIGHT PANEL (TOP): Lineup
        # ==========================================
        top_right = ctk.CTkFrame(self, fg_color="transparent")
        top_right.grid(row=0, column=1, padx=(10, 20), pady=(5, 10), sticky="nsew")
        top_right.grid_propagate(False)
        top_right.grid_columnconfigure(0, weight=1)
        top_right.grid_rowconfigure(0, weight=1)

        self.right_tabs = ctk.CTkTabview(
            top_right, fg_color="#1E293B", corner_radius=10, border_width=1, border_color="#334155"
        )
        self.right_tabs.grid(row=0, column=0, sticky="nsew")
        self.right_tabs.add("Lineup")
        self.right_tabs.tab("Lineup").grid_columnconfigure(0, weight=1)
        self.right_tabs.tab("Lineup").grid_rowconfigure(0, weight=1)

        slots_container_frame = ctk.CTkFrame(self.right_tabs.tab("Lineup"), fg_color="transparent")
        slots_container_frame.grid(row=0, column=0, sticky="nsew")
        slots_container_frame.grid_rowconfigure(1, weight=1)
        slots_container_frame.grid_columnconfigure(0, weight=1)

        slots_header = ctk.CTkFrame(slots_container_frame, fg_color="transparent")
        slots_header.grid(row=0, column=0, sticky="ew", padx=15, pady=(2, 10))

        _btn = ctk.CTkButton(
            slots_header, text="+ ADD DJ", command=self.add_slot,
            width=80, height=32, fg_color="#4F46E5", hover_color="#4338CA",
            font=("Arial", 11, "bold")
        )
        _btn.pack(side="right", padx=(5, 0))
        self._primary_buttons.append(_btn)

        dur_values = [str(x) for x in range(15, 121, 15)]
        self.master_dur_menu = ctk.CTkOptionMenu(
            slots_header,
            values=dur_values,
            variable=self.master_duration,
            height=35, width=90,
            fg_color="#0F172A", button_color="#334155", button_hover_color="#475569",
            text_color="#CBD5E1",
            dropdown_fg_color="#1E293B", dropdown_text_color="#CBD5E1", dropdown_hover_color="#334155"
        )
        self.master_dur_menu.pack(side="right", padx=(0, 5))
        ctk.CTkLabel(slots_header, text="Default length:", font=("Arial", 11), text_color="#94A3B8").pack(side="right", padx=(10, 5))
        self.master_duration.trace_add("write", lambda *args: self.apply_master_duration())

        self.slots_scroll = ctk.CTkScrollableFrame(slots_container_frame, fg_color="transparent")
        self.slots_scroll.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 0))
        self._autohide_scrollbar(self.slots_scroll)

        # Open Decks row
        od_row = ctk.CTkFrame(slots_container_frame, fg_color="#1A1B1E", corner_radius=8)
        od_row.grid(row=2, column=0, sticky="ew", padx=15, pady=(6, 12))

        self.od_toggle_btn = ctk.CTkCheckBox(
            od_row, text="OPEN DECKS", variable=self.include_od,
            command=self.toggle_od,
            font=("Arial", 11, "bold"), text_color="#94A3B8",
            fg_color="#4F46E5", hover_color="#4338CA",
            checkmark_color="#FFFFFF", border_color="#334155"
        )
        self.od_toggle_btn.pack(side="left", padx=(12, 16), pady=8)

        self.od_count_label = ctk.CTkLabel(od_row, text="Amount:", font=("Arial", 11), text_color="#475569")
        self.od_count_label.pack(side="left", padx=(0, 4))
        self.od_count_menu = ctk.CTkOptionMenu(
            od_row,
            values=[str(x) for x in range(1, 11)],
            variable=self.od_count,
            command=lambda _: self.update_output(),
            width=75, height=30, state="disabled",
            fg_color="#0F172A", button_color="#1E293B", button_hover_color="#334155",
            text_color="#475569",
            dropdown_fg_color="#1E293B", dropdown_text_color="#CBD5E1", dropdown_hover_color="#334155"
        )
        self.od_count_menu.pack(side="left", padx=(0, 16))

        self.od_dur_label = ctk.CTkLabel(od_row, text="Slot length:", font=("Arial", 11), text_color="#475569")
        self.od_dur_label.pack(side="left", padx=(0, 4))
        self.od_dur_menu = ctk.CTkOptionMenu(
            od_row,
            values=[str(x) for x in range(15, 121, 15)],
            variable=self.od_duration,
            command=lambda _: self.update_output(),
            width=85, height=30, state="disabled",
            fg_color="#0F172A", button_color="#1E293B", button_hover_color="#334155",
            text_color="#475569",
            dropdown_fg_color="#1E293B", dropdown_text_color="#CBD5E1", dropdown_hover_color="#334155"
        )
        self.od_dur_menu.pack(side="left", padx=(0, 8))

        # ==========================================
        # RIGHT PANEL (BOTTOM): Output Preview
        # ==========================================
        bot_right = ctk.CTkFrame(self, fg_color="#1E1F22", corner_radius=15, border_width=1, border_color="#334155")
        bot_right.grid(row=1, column=1, padx=(10, 20), pady=(10, 20), sticky="nsew")
        bot_right.grid_columnconfigure(0, weight=1)
        bot_right.grid_rowconfigure(1, weight=1)

        preview_header = ctk.CTkFrame(bot_right, fg_color="#2B2D31", corner_radius=0)
        preview_header.grid(row=0, column=0, sticky="ew")

        header_row = ctk.CTkFrame(preview_header, fg_color="transparent")
        header_row.pack(fill="x", padx=0, pady=10)

        self.format_btn = ctk.CTkButton(
            header_row, text="Discord", image=self.icon_discord, compound="left",
            command=self.toggle_format,
            fg_color="#1E293B", hover_color="#334155", border_width=1, border_color="#334155",
            text_color="#818CF8", width=110, height=35, font=("Arial", 11, "bold")
        )
        self.format_btn.pack(side="left", padx=(15, 4))

        self.plain_btn = ctk.CTkButton(
            header_row, text="Plain Text", image=self.icon_text, compound="left",
            command=self.set_plain_text,
            fg_color="transparent", hover_color="#334155", border_width=1, border_color="#334155",
            text_color="#94A3B8", width=110, height=35, font=("Arial", 11, "bold")
        )
        self.plain_btn.pack(side="left", padx=(0, 4))

        self.quest_btn = ctk.CTkButton(
            header_row, text="Quest", image=self.icon_quest, compound="left",
            command=self.set_quest_view,
            fg_color="transparent", hover_color="#334155", border_width=1, border_color="#334155",
            text_color="#94A3B8", width=110, height=35, font=("Arial", 11, "bold")
        )
        self.quest_btn.pack(side="left", padx=(0, 4))

        self.pc_btn = ctk.CTkButton(
            header_row, text="PC", image=self.icon_pc, compound="left",
            command=self.set_pc_view,
            fg_color="transparent", hover_color="#334155", border_width=1, border_color="#334155",
            text_color="#94A3B8", width=80, height=35, font=("Arial", 11, "bold")
        )
        self.pc_btn.pack(side="left")

        def _toggle_times():
            self.names_only.set(not self.names_only.get())
            self.update_output()

        self._times_toggle_btn = ctk.CTkButton(
            header_row, text="Times on",
            command=_toggle_times,
            fg_color="transparent", hover_color="#334155",
            text_color="#94A3B8", width=76, height=35,
            font=("Arial", 10, "bold"), border_width=1, border_color="#334155"
        )
        self._times_toggle_btn.pack(side="right", padx=(0, 15))

        def _sync_times_btn(*_):
            if self.names_only.get():
                self._times_toggle_btn.configure(text="Times off", text_color="#EF4444")
            else:
                self._times_toggle_btn.configure(text="Times on", text_color="#94A3B8")
        self.names_only.trace_add("write", _sync_times_btn)

        output_container = ctk.CTkFrame(bot_right, fg_color="transparent")
        output_container.grid(row=1, column=0, sticky="nsew", padx=20, pady=20)
        output_container.grid_columnconfigure(0, weight=1)
        output_container.grid_rowconfigure(0, weight=1)

        self.output_text = ctk.CTkTextbox(
            output_container, fg_color="#313338", text_color="#DBDEE1",
            font=("Consolas", 14), wrap="word", border_width=1, border_color="#3F4147"
        )
        self.output_text.grid(row=0, column=0, sticky="nsew")

        self.copy_icon_btn = ctk.CTkButton(
            output_container, text="⎘", command=self.copy_template,
            width=32, height=32, corner_radius=6,
            fg_color="#3F4147", hover_color="#4F46E5",
            text_color="#94A3B8", font=("Arial", 15)
        )
        self.copy_icon_btn.place_forget()
        self.output_text.bind("<Enter>", lambda e: self.copy_icon_btn.place(relx=1.0, rely=0.0, x=-10, y=10, anchor="ne"))
        self.output_text.bind("<Leave>", self._on_output_leave)
        self.copy_icon_btn.bind("<Enter>", lambda e: self.copy_icon_btn.place(relx=1.0, rely=0.0, x=-10, y=10, anchor="ne"))
        self.copy_icon_btn.bind("<Leave>", self._on_output_leave)

        self._build_settings_tab()
        self.apply_theme()

    # ── Scrollbar helper ──────────────────────────────────────────────────

    def _autohide_scrollbar(self, sf):
        """Hide the scrollbar on a CTkScrollableFrame when content fits."""
        frames = self.__dict__.setdefault("_scrollable_frames", [])
        if sf not in frames:
            frames.append(sf)

        _check_job = [None]

        def _check(event=None):
            if _check_job[0] is not None:
                return  # already scheduled
            def _do():
                _check_job[0] = None
                sf.update_idletasks()
                bbox = sf._parent_canvas.bbox("all")
                if bbox is None:
                    sf._scrollbar.grid_remove()
                    return
                if bbox[3] - bbox[1] > sf._parent_canvas.winfo_height():
                    sf._scrollbar.grid()
                else:
                    sf._scrollbar.grid_remove()
            _check_job[0] = sf.after(80, _do)

        sf._parent_canvas.bind("<Configure>", lambda e: _check(), add="+")
        sf._parent_frame.bind("<Configure>", lambda e: _check(), add="+")
        sf.bind("<Configure>", lambda e: _check(), add="+")

    # ── Title management ──────────────────────────────────────────────────

    def _toggle_event_panel(self):
        """Switch the Event tab between the config editor and saved events list."""
        config_visible = self._event_config_panel.winfo_ismapped()
        if config_visible:
            self._event_config_panel.grid_remove()
            self._event_saved_panel.grid(row=1, column=0, sticky="nsew", padx=6, pady=(0, 6))
            self._event_header_lbl.configure(text="SAVED EVENTS")
            self._saved_panel_btn.configure(text="← Edit", fg_color="#334155", hover_color="#475569", text_color="#CBD5E1")
        else:
            self._event_saved_panel.grid_remove()
            self._event_config_panel.grid(row=1, column=0, sticky="nsew")
            self._event_header_lbl.configure(text="EVENT CONFIGURATION")
            self._saved_panel_btn.configure(text="Saved", fg_color="#059669", hover_color="#047857", text_color="#FFFFFF")

    def save_title(self):
        val = self.event_title_var.get().strip()
        if val and val.lower() not in [t.lower() for t in self.saved_titles]:
            self.saved_titles.append(val)
            self._save_library()
            self.title_combo.configure(values=self.saved_titles)

    def delete_saved_title(self):
        val = self.event_title_var.get().strip()
        if val and val in self.saved_titles:
            if messagebox.askyesno("Confirm Delete", f"Remove '{val}' from saved titles?"):
                self.saved_titles.remove(val)
                self._save_library()
                self.event_title_var.set("")
                self.title_combo.configure(values=self.saved_titles)
