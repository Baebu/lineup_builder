import customtkinter as ctk
from .date_time_picker import CTkDateTimePicker
from tkinter import messagebox


class UISetupMixin:
    """Builds the entire application UI and provides title management helpers."""

    def setup_ui(self):
        # Grid Layout
        self.grid_columnconfigure(0, weight=1, uniform="quad")
        self.grid_columnconfigure(1, weight=1, uniform="quad")
        self.grid_rowconfigure(0, weight=3, uniform="row")
        self.grid_rowconfigure(1, weight=2, uniform="row")

        # ==========================================
        # LEFT PANEL: Configuration & Settings
        # ==========================================
        left_panel = ctk.CTkFrame(self, fg_color="transparent")
        left_panel.grid(row=0, column=0, rowspan=2, padx=(20, 10), pady=(5, 20), sticky="nsew")
        left_panel.grid_columnconfigure(0, weight=1)
        left_panel.grid_rowconfigure(0, weight=1)

        self.left_tabs = ctk.CTkTabview(left_panel, fg_color="#1E293B", corner_radius=10, border_width=1, border_color="#334155")
        self.left_tabs.grid(row=0, column=0, sticky="nsew")

        self.left_tabs.add("Event")
        self.left_tabs.add("DJ Roster")

        self.left_tabs.tab("Event").grid_columnconfigure(0, weight=1)
        self.left_tabs.tab("Event").grid_rowconfigure(0, weight=1)
        self.left_tabs.tab("DJ Roster").grid_columnconfigure(0, weight=1)
        self.left_tabs.tab("DJ Roster").grid_rowconfigure(0, weight=0)
        self.left_tabs.tab("DJ Roster").grid_rowconfigure(1, weight=1)

        # ── Event tab ─────────────────────────────────────────────────────
        config_frame = ctk.CTkScrollableFrame(self.left_tabs.tab("Event"), fg_color="transparent")
        config_frame.grid(row=0, column=0, sticky="nsew")
        config_frame.grid_columnconfigure(0, weight=1)
        self._autohide_scrollbar(config_frame)

        ctk.CTkLabel(config_frame, text="EVENT CONFIGURATION", font=("Arial", 11, "bold"), text_color="#818CF8").pack(anchor="w", padx=15, pady=(5, 5))

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
        ctk.CTkButton(
            btn_frame, text="", image=self.icon_save, width=34, height=34,
            fg_color="#334155", hover_color="#475569",
            command=self.save_title
        ).pack(side="left", padx=(0, 2))
        ctk.CTkButton(
            btn_frame, text="", image=self.icon_trash, width=34, height=34,
            fg_color="#7F1D1D", hover_color="#991B1B",
            command=self.delete_saved_title
        ).pack(side="left")

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

        self._genre_panel_expanded = False
        self.genre_arrow_btn = ctk.CTkButton(
            genre_input_frame, text="", image=self.icon_chevron_down, width=34, height=34,
            fg_color="#334155", hover_color="#475569",
            command=self._toggle_genre_panel
        )
        self.genre_arrow_btn.grid(row=0, column=1)

        self.genre_del_btn = ctk.CTkButton(
            genre_input_frame, text="", image=self.icon_trash, width=34, height=34,
            fg_color="#7F1D1D", hover_color="#991B1B",
            command=self.delete_saved_genre
        )
        self.genre_del_btn.grid(row=0, column=2, padx=(5, 0))

        self._genre_saved_panel = ctk.CTkFrame(genre_frame, fg_color="#0F172A", border_width=1, border_color="#334155", corner_radius=6)

        self.genre_tags_frame = ctk.CTkFrame(genre_frame, fg_color="transparent", height=1)
        self.genre_tags_frame.pack(fill="x", pady=(5, 0))

        self.refresh_genre_saved_panel()

        self.event_timestamp.trace_add("write", lambda *args: self._schedule_update())

        # Saved Events section
        ctk.CTkLabel(config_frame, text="SAVED EVENTS", font=("Arial", 11, "bold"), text_color="#818CF8").pack(anchor="w", padx=15, pady=(15, 5))

        saved_events_container = ctk.CTkFrame(config_frame, fg_color="transparent")
        saved_events_container.pack(fill="x", padx=15, pady=(0, 15))
        saved_events_container.grid_columnconfigure(0, weight=1)

        self.saved_events_scroll = ctk.CTkScrollableFrame(saved_events_container, fg_color="transparent", height=200)
        self.saved_events_scroll.grid(row=0, column=0, sticky="nsew")
        self.saved_events_scroll.grid_columnconfigure(0, weight=1)
        self._autohide_scrollbar(self.saved_events_scroll)
        self.refresh_saved_events_ui()

        # ── DJ Roster tab ──────────────────────────────────────────────────
        dj_roster_tab = self.left_tabs.tab("DJ Roster")
        dj_roster_hdr = ctk.CTkFrame(dj_roster_tab, fg_color="transparent")
        dj_roster_hdr.grid(row=0, column=0, sticky="ew", padx=8, pady=(4, 0))
        ctk.CTkLabel(dj_roster_hdr, text="DJ ROSTER", font=("Arial", 11, "bold"), text_color="#818CF8").pack(side="left")
        ctk.CTkLabel(dj_roster_hdr, text="drag to add →", font=("Arial", 11, "bold"), text_color="#B9B9B9").pack(side="left", padx=(8, 0))
        ctk.CTkButton(
            dj_roster_hdr, text="+ NEW DJ", width=80, height=32,
            fg_color="#4F46E5", hover_color="#4338CA", font=("Arial", 11, "bold"),
            command=self.add_new_dj_to_roster
        ).pack(side="right")
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

        ctk.CTkButton(
            slots_header, text="", image=self.icon_save,
            command=self.save_event_lineup, width=34, height=34,
            fg_color="#059669", hover_color="#047857"
        ).pack(side="right", padx=(5, 0))

        ctk.CTkButton(
            slots_header, text="+ ADD DJ", command=self.add_slot,
            width=80, height=32, fg_color="#4F46E5", hover_color="#4338CA",
            font=("Arial", 11, "bold")
        ).pack(side="right", padx=(5, 0))

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

    # ── Scrollbar helper ──────────────────────────────────────────────────

    def _autohide_scrollbar(self, sf):
        """Hide the scrollbar on a CTkScrollableFrame when content fits."""
        def _check(event=None):
            sf.update_idletasks()
            bbox = sf._parent_canvas.bbox("all")
            if bbox is None:
                sf._scrollbar.grid_remove()
                return
            if bbox[3] - bbox[1] > sf._parent_canvas.winfo_height():
                sf._scrollbar.grid()
            else:
                sf._scrollbar.grid_remove()

        sf._parent_canvas.bind("<Configure>", lambda e: _check(), add="+")
        sf._parent_frame.bind("<Configure>", lambda e: _check(), add="+")
        sf.bind("<Configure>", lambda e: _check(), add="+")

    # ── Title management ──────────────────────────────────────────────────

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
