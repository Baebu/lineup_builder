import customtkinter as ctk
import datetime
import yaml
import os
from tkinter import messagebox
from date_time_picker import CTkDateTimePicker

class SlotUI(ctk.CTkFrame):
    def __init__(self, master, app_ref, name="", genre="", duration=60):
        super().__init__(master, fg_color="#1E293B", corner_radius=10, border_width=1, border_color="#334155")
        self.app_ref = app_ref
        
        self.name_var = ctk.StringVar(value=name)
        self.genre_var = ctk.StringVar(value=genre)
        self.duration_var = ctk.StringVar(value=str(duration))
        
        self.name_var.trace_add("write", self._on_name_change)
        self.genre_var.trace_add("write", lambda *args: self.app_ref.update_output())
        self.duration_var.trace_add("write", lambda *args: self.app_ref.update_output())
        
        self.grid_columnconfigure(2, weight=3)
        self.grid_columnconfigure(3, weight=2)
        self.grid_columnconfigure(4, weight=1)
        
        self.up_btn = ctk.CTkButton(self, text="↑", width=30, height=30, command=self.move_up,
                                    fg_color="#334155", hover_color="#475569")
        self.up_btn.grid(row=0, column=0, padx=(10, 2), pady=10)
        
        self.down_btn = ctk.CTkButton(self, text="↓", width=30, height=30, command=self.move_down,
                                      fg_color="#334155", hover_color="#475569")
        self.down_btn.grid(row=0, column=1, padx=(2, 10), pady=10)
        
        self.name_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.name_frame.grid(row=0, column=2, padx=5, pady=10, sticky="ew")
        self.name_frame.grid_columnconfigure(0, weight=1)

        self.name_entry = ctk.CTkComboBox(self.name_frame, variable=self.name_var, values=self.app_ref.get_dj_names(),
                                          fg_color="#0F172A", border_width=1, border_color="#334155", 
                                          height=35, button_color="#334155", button_hover_color="#475569",
                                          dropdown_fg_color="#1E293B", dropdown_text_color="#CBD5E1",
                                          dropdown_hover_color="#334155", command=lambda v: (self.app_ref.update_output(), self.update_dj_info()))
        self.name_entry.grid(row=0, column=0, sticky="ew", padx=(0, 5))

        self.info_label = ctk.CTkLabel(
            self.name_frame, text="", font=("Arial", 10), text_color="#475569", anchor="w"
        )
        self.info_label.grid(row=1, column=0, columnspan=2, sticky="ew", padx=(2, 5), pady=(0, 3))

        btn_frame = ctk.CTkFrame(self.name_frame, fg_color="transparent")
        btn_frame.grid(row=0, column=1)

        self.save_dj_btn = ctk.CTkButton(btn_frame, text="Save", width=40, height=35,
                                         fg_color="#334155", hover_color="#475569", command=self.save_dj)
        self.save_dj_btn.pack(side="left", padx=(0, 2))
        
        self.del_dj_btn = ctk.CTkButton(btn_frame, text="🗑️", width=35, height=35, font=("Arial", 15),
                                        fg_color="#7F1D1D", hover_color="#991B1B", command=self.delete_saved_dj)
        self.del_dj_btn.pack(side="left")

        self.genre_entry = ctk.CTkEntry(self, textvariable=self.genre_var, placeholder_text="Genre",
                                        fg_color="#0F172A", border_width=1, border_color="#334155", height=35)
        self.genre_entry.grid(row=0, column=3, padx=5, pady=10, sticky="ew")
        
        # Duration Dropdown (15-120 mins)
        dur_values = [str(x) for x in range(15, 121, 15)]
        if self.duration_var.get() not in dur_values:
             dur_values.append(self.duration_var.get())
             dur_values.sort(key=lambda x: int(x))
             
        self.dur_menu = ctk.CTkOptionMenu(
            self, 
            values=dur_values,
            variable=self.duration_var,
            width=90,
            height=35,
            fg_color="#0F172A",
            button_color="#334155",
            button_hover_color="#475569",
            text_color="#CBD5E1",
            dropdown_fg_color="#1E293B",
            dropdown_text_color="#CBD5E1",
            dropdown_hover_color="#334155",
            command=self.on_duration_change
        )
        self.dur_menu.grid(row=0, column=4, padx=5, pady=10, sticky="ew")
        
        self.del_btn = ctk.CTkButton(self, text="×", width=30, height=30, command=self.delete_slot,
                                     fg_color="#EF4444", hover_color="#DC2626")
        self.del_btn.grid(row=0, column=5, padx=10, pady=10)
        
    def _on_name_change(self, *args):
        self.app_ref.update_output()
        self.update_dj_info()

    def update_dj_info(self):
        val = self.name_var.get().strip()
        dj = next((d for d in self.app_ref.saved_djs if d.get("name") == val), None)
        parts = []
        if dj:
            if dj.get("goggles"):
                parts.append(f"🥽 {dj['goggles']}")
            if dj.get("link"):
                parts.append(f"💻 {dj['link']}")
        self.info_label.configure(text="   ".join(parts))

    def save_dj(self):
        val = self.name_var.get().strip()
        if val and val.lower() not in [n.lower() for n in self.app_ref.get_dj_names()]:
            self.app_ref.saved_djs.append({"name": val, "goggles": "", "link": ""})
            self.app_ref._save_library()
            self.app_ref.refresh_dj_roster_ui()
            for slot in self.app_ref.slots:
                slot.name_entry.configure(values=self.app_ref.get_dj_names())

    def delete_saved_dj(self):
        val = self.name_var.get().strip()
        names = self.app_ref.get_dj_names()
        if val and val in names:
            if messagebox.askyesno("Confirm Delete", f"Remove '{val}' from saved DJs?"):
                idx = names.index(val)
                self.app_ref.saved_djs.pop(idx)
                self.app_ref._save_library()
                self.name_var.set("")
                self.app_ref.refresh_dj_roster_ui()
                for slot in self.app_ref.slots:
                    slot.name_entry.configure(values=self.app_ref.get_dj_names())
                    if slot.name_var.get() == val:
                        slot.name_var.set("")

    def on_duration_change(self, choice):
        # Triggered when dropdown changes
        self.app_ref.update_output()
        
    def move_up(self):
        self.app_ref.move_slot(self, -1)
        
    def move_down(self):
        self.app_ref.move_slot(self, 1)
        
    def delete_slot(self):
        self.app_ref.delete_slot(self)

class App(ctk.CTk):
    LIBRARY_FILE = "lineup_library.yaml"
    EVENTS_FILE  = "lineup_events.yaml"

    def __init__(self):
        super().__init__()
        
        self.title("Lineup Builder")
        self.geometry("1280x920")
        
        ctk.set_appearance_mode("dark")
        self.configure(fg_color="#0F172A")
        
        self.grid_columnconfigure(0, weight=1, uniform="group1")
        self.grid_columnconfigure(1, weight=1, uniform="group1")
        self.grid_rowconfigure(0, weight=1)
        
        # Load saved data
        self.load_data()
        
        # Initialize with today's date at 20:00
        now = datetime.datetime.now()
        self.event_timestamp = ctk.StringVar(value=f"{now.strftime('%Y-%m-%d')} 20:00")
        
        self.event_title_var = ctk.StringVar(value="")
        self.event_vol_var = ctk.StringVar(value="")
        
        self.master_duration = ctk.StringVar(value="60")
        
        self.active_genres = []
        self.genre_entry_var = ctk.StringVar()
        self.genre_dropdown_var = ctk.StringVar(value="")
        
        self.names_only = ctk.BooleanVar(value=False)
        self.output_format = ctk.StringVar(value="discord") # 'discord' or 'local'
        
        self.include_od = ctk.BooleanVar(value=False)
        self.od_duration = ctk.StringVar(value="30")
        self.od_count = ctk.StringVar(value="4")
        
        self.slots = []
        
        self.setup_ui()
        self.add_initial_slots()
        self.update_output()
        
    def load_data(self):
        # ── Library: titles, DJs, genres ─────────────────────────────────
        lib = {}
        for src in [self.LIBRARY_FILE, "lineup_data.yaml"]:
            if os.path.exists(src):
                try:
                    with open(src, 'r') as f:
                        lib = yaml.safe_load(f) or {}
                    break
                except Exception as e:
                    print(f"Error loading {src}: {e}")
        self.saved_titles = lib.get('titles', [])
        raw_djs = lib.get('djs', [])
        self.saved_djs = [
            d if isinstance(d, dict) else {"name": d, "goggles": "", "link": ""}
            for d in raw_djs
        ]
        self.saved_genres = lib.get('genres', [])

        # ── Events ───────────────────────────────────────────────────────
        evts = {}
        for src in [self.EVENTS_FILE, "lineup_data.yaml"]:
            if os.path.exists(src):
                try:
                    with open(src, 'r') as f:
                        evts = yaml.safe_load(f) or {}
                    break
                except Exception as e:
                    print(f"Error loading {src}: {e}")
        raw_events = evts.get('events', [])
        # Sort by created_at descending (most recent first)
        self.saved_events = sorted(
            raw_events, key=lambda e: e.get('created_at', ''), reverse=True
        )

    def save_data(self):
        self._save_library()
        self._save_events()

    def _save_library(self):
        data = {'titles': self.saved_titles, 'djs': self.saved_djs, 'genres': self.saved_genres}
        try:
            with open(self.LIBRARY_FILE, 'w') as f:
                yaml.dump(data, f, allow_unicode=True)
        except Exception as e:
            print(f"Error saving {self.LIBRARY_FILE}: {e}")

    def _save_events(self):
        try:
            with open(self.EVENTS_FILE, 'w') as f:
                yaml.dump({'events': self.saved_events}, f, allow_unicode=True)
        except Exception as e:
            print(f"Error saving {self.EVENTS_FILE}: {e}")

    def setup_ui(self):
        # ── Main grid: 2 cols × 3 rows ────────────────────────────────────
        self.grid_columnconfigure(0, weight=2)   # left  ~40 %
        self.grid_columnconfigure(1, weight=3)   # right ~60 %
        self.grid_rowconfigure(0, weight=0)      # header (fixed)
        self.grid_rowconfigure(1, weight=3)      # middle (main content)
        self.grid_rowconfigure(2, weight=1)      # preview (bottom)

        # ══════════════════════════════════════════════════════════════════
        # HEADER
        # ══════════════════════════════════════════════════════════════════
        header = ctk.CTkFrame(self, fg_color="#1E293B", corner_radius=0,
                              border_width=1, border_color="#334155", height=68)
        header.grid(row=0, column=0, columnspan=2, sticky="ew")
        header.grid_propagate(False)
        header.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(header, text="🎛  Lineup Builder",
                     font=("Arial", 15, "bold"), text_color="#818CF8"
                     ).grid(row=0, column=0, padx=(20, 24), sticky="w")

        ev_sel = ctk.CTkFrame(header, fg_color="transparent")
        ev_sel.grid(row=0, column=1, sticky="w")
        ctk.CTkLabel(ev_sel, text="Current event:",
                     font=("Arial", 11), text_color="#94A3B8"
                     ).pack(side="left", padx=(0, 8))
        self.event_selector_var = ctk.StringVar(value="")
        self.event_selector_combo = ctk.CTkComboBox(
            ev_sel,
            variable=self.event_selector_var,
            values=["-- No saved events --"],
            width=310, height=36,
            fg_color="#0F172A", border_color="#334155",
            button_color="#334155", button_hover_color="#475569",
            dropdown_fg_color="#1E293B", dropdown_text_color="#CBD5E1",
            dropdown_hover_color="#334155",
            command=self._load_event_by_selector,
        )
        self.event_selector_combo.pack(side="left")

        ctk.CTkButton(
            header, text="💾  Save Event", command=self.save_event_lineup,
            fg_color="#059669", hover_color="#047857",
            font=("Arial", 11, "bold"), height=36, width=140,
        ).grid(row=0, column=2, padx=(10, 20))

        # ══════════════════════════════════════════════════════════════════
        # LEFT COLUMN: Event Details + Open Decks
        # ══════════════════════════════════════════════════════════════════
        left_col = ctk.CTkScrollableFrame(self, fg_color="transparent",
                                          corner_radius=0, border_width=0)
        left_col.grid(row=1, column=0, sticky="nsew", padx=(20, 10), pady=15)
        left_col.grid_columnconfigure(0, weight=1)
        self._autohide_scrollbar(left_col)

        # ── Panel: Event Details ──────────────────────────────────────────
        ev_panel = ctk.CTkFrame(left_col, fg_color="#1E293B", corner_radius=10,
                                border_width=1, border_color="#334155")
        ev_panel.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(ev_panel, text="EVENT DETAILS",
                     font=("Arial", 11, "bold"), text_color="#818CF8"
                     ).pack(anchor="w", padx=15, pady=(12, 0))

        inner = ctk.CTkFrame(ev_panel, fg_color="transparent")
        inner.pack(fill="x", padx=15, pady=(8, 14))
        inner.grid_columnconfigure(0, weight=1)

        # Title
        ctk.CTkLabel(inner, text="EVENT TITLE",
                     font=("Arial", 9, "bold"), text_color="#94A3B8"
                     ).grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 2))

        title_row = ctk.CTkFrame(inner, fg_color="transparent")
        title_row.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(0, 10))
        title_row.grid_columnconfigure(0, weight=1)

        self.title_combo = ctk.CTkComboBox(
            title_row, variable=self.event_title_var,
            values=self.saved_titles, height=35,
            fg_color="#0F172A", border_color="#334155",
            button_color="#334155", button_hover_color="#475569",
            dropdown_fg_color="#1E293B", dropdown_text_color="#CBD5E1",
            dropdown_hover_color="#334155",
            command=lambda v: self.update_output(),
        )
        self.title_combo.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        self.event_title_var.trace_add("write", lambda *args: self.update_output())

        vol_frame = ctk.CTkFrame(title_row, fg_color="transparent")
        vol_frame.grid(row=0, column=1)
        ctk.CTkLabel(vol_frame, text="Vol.",
                     font=("Arial", 11, "bold"), text_color="#94A3B8"
                     ).pack(side="left", padx=(0, 3))
        self.vol_entry = ctk.CTkEntry(
            vol_frame, textvariable=self.event_vol_var,
            width=48, height=35, fg_color="#0F172A", border_color="#334155",
        )
        self.vol_entry.pack(side="left", padx=(0, 5))
        self.event_vol_var.trace_add("write", lambda *args: self.update_output())

        t_btn = ctk.CTkFrame(title_row, fg_color="transparent")
        t_btn.grid(row=0, column=2)
        ctk.CTkButton(t_btn, text="Save", width=50, height=35,
                      fg_color="#334155", hover_color="#475569",
                      command=self.save_title).pack(side="left", padx=(0, 2))
        ctk.CTkButton(t_btn, text="🗑️", width=35, height=35,
                      font=("Arial", 15), fg_color="#7F1D1D", hover_color="#991B1B",
                      command=self.delete_saved_title).pack(side="left")

        # Start time
        ctk.CTkLabel(inner, text="START TIME",
                     font=("Arial", 9, "bold"), text_color="#94A3B8"
                     ).grid(row=2, column=0, columnspan=3, sticky="w", pady=(0, 2))
        dt_wrap = ctk.CTkFrame(inner, fg_color="transparent")
        dt_wrap.grid(row=3, column=0, columnspan=3, sticky="ew", pady=(0, 10))
        dt_wrap.grid_columnconfigure(0, weight=1)
        CTkDateTimePicker(dt_wrap, variable=self.event_timestamp).grid(row=0, column=0, sticky="ew")
        self.event_timestamp.trace_add("write", lambda *args: self.update_output())

        # Genres
        ctk.CTkLabel(inner, text="GENRES  (Press Enter to add)",
                     font=("Arial", 9, "bold"), text_color="#94A3B8"
                     ).grid(row=4, column=0, columnspan=3, sticky="w", pady=(0, 2))

        genre_row = ctk.CTkFrame(inner, fg_color="transparent")
        genre_row.grid(row=5, column=0, columnspan=3, sticky="ew", pady=(0, 6))
        genre_row.grid_columnconfigure(0, weight=1)

        self.genre_entry = ctk.CTkEntry(
            genre_row, textvariable=self.genre_entry_var,
            placeholder_text="Type and press Enter…",
            fg_color="#0F172A", border_width=1, border_color="#334155", height=35,
        )
        self.genre_entry.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        self.genre_entry.bind("<Return>", self.add_genre_from_entry)

        self.genre_dropdown = ctk.CTkOptionMenu(
            genre_row,
            values=["---"] + self.saved_genres if self.saved_genres else ["---"],
            variable=self.genre_dropdown_var,
            width=35, height=35, dynamic_resizing=False,
            fg_color="#334155", button_color="#334155", button_hover_color="#475569",
            dropdown_fg_color="#1E293B", dropdown_text_color="#CBD5E1",
            dropdown_hover_color="#334155",
            command=self.add_genre_from_dropdown,
        )
        self.genre_dropdown.grid(row=0, column=1)

        ctk.CTkButton(
            genre_row, text="🗑️", width=35, height=35, font=("Arial", 15),
            fg_color="#7F1D1D", hover_color="#991B1B",
            command=self.delete_saved_genre,
        ).grid(row=0, column=2, padx=(5, 0))

        self.genre_tags_frame = ctk.CTkFrame(inner, fg_color="transparent", height=1)
        self.genre_tags_frame.grid(row=6, column=0, columnspan=3, sticky="ew", pady=(0, 8))

        # Output format
        ctk.CTkLabel(inner, text="OUTPUT FORMAT",
                     font=("Arial", 9, "bold"), text_color="#94A3B8"
                     ).grid(row=7, column=0, columnspan=3, sticky="w", pady=(4, 2))

        fmt_row = ctk.CTkFrame(inner, fg_color="transparent")
        fmt_row.grid(row=8, column=0, columnspan=3, sticky="w", pady=(0, 10))

        self.format_btn = ctk.CTkButton(
            fmt_row, text="Discord Mode", command=self.toggle_format,
            fg_color="#1E293B", hover_color="#334155", border_width=1,
            border_color="#334155", text_color="#818CF8", width=120, height=32,
        )
        self.format_btn.pack(side="left", padx=(0, 5))

        self.plain_btn = ctk.CTkButton(
            fmt_row, text="Plain Text", command=self.set_plain_text,
            fg_color="transparent", hover_color="#334155", border_width=1,
            border_color="#334155", text_color="#94A3B8", width=100, height=32,
        )
        self.plain_btn.pack(side="left")

        # Minimalist mode
        ctk.CTkSwitch(
            inner, text="Minimalist Mode (Names Only)",
            variable=self.names_only, command=self.update_output,
            progress_color="#4F46E5", text_color="#CBD5E1",
            font=("Arial", 12, "bold"),
        ).grid(row=9, column=0, columnspan=3, sticky="w", pady=(4, 4))

        # ── Panel: Open Decks ─────────────────────────────────────────────
        od_panel = ctk.CTkFrame(left_col, fg_color="#1E293B", corner_radius=10,
                                border_width=1, border_color="#334155")
        od_panel.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(od_panel, text="OPEN DECKS",
                     font=("Arial", 11, "bold"), text_color="#818CF8"
                     ).pack(anchor="w", padx=15, pady=(12, 0))

        od_inner = ctk.CTkFrame(od_panel, fg_color="transparent")
        od_inner.pack(fill="x", padx=15, pady=(8, 14))

        self.od_toggle_btn = ctk.CTkCheckBox(
            od_inner, text="Enable open decks",
            variable=self.include_od, command=self.toggle_od,
            font=("Arial", 12, "bold"), text_color="#CBD5E1",
            fg_color="#4F46E5", hover_color="#4338CA",
            checkmark_color="#FFFFFF", border_color="#334155",
        )
        self.od_toggle_btn.pack(anchor="w", pady=(0, 12))

        od_fields = ctk.CTkFrame(od_inner, fg_color="transparent")
        od_fields.pack(fill="x")
        od_fields.grid_columnconfigure((0, 1), weight=1)

        od_left = ctk.CTkFrame(od_fields, fg_color="transparent")
        od_left.grid(row=0, column=0, sticky="w", padx=(0, 10))
        self.od_count_label = ctk.CTkLabel(od_left, text="Amount:", font=("Arial", 11), text_color="#475569")
        self.od_count_label.pack(anchor="w", pady=(0, 2))
        self.od_count_menu = ctk.CTkOptionMenu(
            od_left, values=[str(x) for x in range(1, 11)],
            variable=self.od_count, command=lambda _: self.update_output(),
            width=90, height=32, state="disabled",
            fg_color="#0F172A", button_color="#1E293B", button_hover_color="#334155",
            text_color="#475569", dropdown_fg_color="#1E293B",
            dropdown_text_color="#CBD5E1", dropdown_hover_color="#334155",
        )
        self.od_count_menu.pack(anchor="w")

        od_right = ctk.CTkFrame(od_fields, fg_color="transparent")
        od_right.grid(row=0, column=1, sticky="w")
        self.od_dur_label = ctk.CTkLabel(od_right, text="Slot length (min):", font=("Arial", 11), text_color="#475569")
        self.od_dur_label.pack(anchor="w", pady=(0, 2))
        self.od_dur_menu = ctk.CTkOptionMenu(
            od_right, values=[str(x) for x in range(15, 121, 15)],
            variable=self.od_duration, command=lambda _: self.update_output(),
            width=90, height=32, state="disabled",
            fg_color="#0F172A", button_color="#1E293B", button_hover_color="#334155",
            text_color="#475569", dropdown_fg_color="#1E293B",
            dropdown_text_color="#CBD5E1", dropdown_hover_color="#334155",
        )
        self.od_dur_menu.pack(anchor="w")

        # ══════════════════════════════════════════════════════════════════
        # RIGHT COLUMN: Lineup (top) + DJ Roster (bottom)
        # ══════════════════════════════════════════════════════════════════
        right_col = ctk.CTkFrame(self, fg_color="transparent")
        right_col.grid(row=1, column=1, sticky="nsew", padx=(10, 20), pady=15)
        right_col.grid_columnconfigure(0, weight=1)
        right_col.grid_rowconfigure(0, weight=3)
        right_col.grid_rowconfigure(1, weight=2)

        # ── Lineup slots ──────────────────────────────────────────────────
        lineup_frame = ctk.CTkFrame(right_col, fg_color="#1E293B", corner_radius=10,
                                    border_width=1, border_color="#334155")
        lineup_frame.grid(row=0, column=0, sticky="nsew", pady=(0, 10))
        lineup_frame.grid_columnconfigure(0, weight=1)
        lineup_frame.grid_rowconfigure(1, weight=1)

        lineup_hdr = ctk.CTkFrame(lineup_frame, fg_color="transparent")
        lineup_hdr.grid(row=0, column=0, sticky="ew", padx=15, pady=12)

        ctk.CTkLabel(lineup_hdr, text="LINEUP SLOTS",
                     font=("Arial", 11, "bold"), text_color="#818CF8").pack(side="left")

        ctk.CTkButton(
            lineup_hdr, text="+ ADD DJ", command=self.add_slot,
            fg_color="#4F46E5", hover_color="#4338CA",
            font=("Arial", 11, "bold"), width=90, height=32,
        ).pack(side="right", padx=(5, 0))

        dur_values = [str(x) for x in range(15, 121, 15)]
        self.master_dur_menu = ctk.CTkOptionMenu(
            lineup_hdr, values=dur_values, variable=self.master_duration,
            height=32, width=90,
            fg_color="#0F172A", button_color="#334155", button_hover_color="#475569",
            text_color="#CBD5E1", dropdown_fg_color="#1E293B",
            dropdown_text_color="#CBD5E1", dropdown_hover_color="#334155",
        )
        self.master_dur_menu.pack(side="right", padx=(0, 5))
        ctk.CTkLabel(lineup_hdr, text="Default length:",
                     font=("Arial", 11), text_color="#94A3B8").pack(side="right", padx=(10, 5))
        self.master_duration.trace_add("write", lambda *args: self.apply_master_duration())

        self.slots_scroll = ctk.CTkScrollableFrame(lineup_frame, fg_color="transparent")
        self.slots_scroll.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self._autohide_scrollbar(self.slots_scroll)

        # ── DJ Roster ─────────────────────────────────────────────────────
        roster_frame = ctk.CTkFrame(right_col, fg_color="#1E293B", corner_radius=10,
                                    border_width=1, border_color="#334155")
        roster_frame.grid(row=1, column=0, sticky="nsew")
        roster_frame.grid_columnconfigure(0, weight=1)
        roster_frame.grid_rowconfigure(1, weight=1)

        dj_hdr = ctk.CTkFrame(roster_frame, fg_color="transparent")
        dj_hdr.grid(row=0, column=0, sticky="ew", padx=15, pady=10)
        ctk.CTkLabel(dj_hdr, text="DJ ROSTER",
                     font=("Arial", 11, "bold"), text_color="#818CF8").pack(side="left")
        ctk.CTkButton(
            dj_hdr, text="+ NEW DJ", command=self.add_new_dj_to_roster,
            fg_color="#4F46E5", hover_color="#4338CA",
            font=("Arial", 11, "bold"), width=85, height=30,
        ).pack(side="right")

        self.dj_roster_scroll = ctk.CTkScrollableFrame(roster_frame, fg_color="transparent")
        self.dj_roster_scroll.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self.dj_roster_scroll.grid_columnconfigure(0, weight=1)
        self._autohide_scrollbar(self.dj_roster_scroll)
        self.refresh_dj_roster_ui()

        # ══════════════════════════════════════════════════════════════════
        # BOTTOM: Live preview (full width)
        # ══════════════════════════════════════════════════════════════════
        preview = ctk.CTkFrame(self, fg_color="#1E1F22", corner_radius=12,
                               border_width=1, border_color="#334155")
        preview.grid(row=2, column=0, columnspan=2, sticky="nsew",
                     padx=20, pady=(0, 20))
        preview.grid_propagate(False)
        preview.grid_columnconfigure(0, weight=1)
        preview.grid_rowconfigure(1, weight=1)

        prev_hdr = ctk.CTkFrame(preview, fg_color="#2B2D31", height=52, corner_radius=0)
        prev_hdr.grid(row=0, column=0, sticky="ew")
        prev_hdr.pack_propagate(False)

        dots_frame = ctk.CTkFrame(prev_hdr, fg_color="transparent")
        dots_frame.pack(side="left", padx=15, pady=18)
        for dot_color in ["#EF4444", "#F59E0B", "#10B981"]:
            ctk.CTkFrame(dots_frame, width=11, height=11, corner_radius=6,
                         fg_color=dot_color).pack(side="left", padx=2)
        ctk.CTkLabel(dots_frame, text="LIVE TEXT PREVIEW",
                     font=("Arial", 10, "bold"), text_color="#94A3B8"
                     ).pack(side="left", padx=12)

        self.copy_btn = ctk.CTkButton(
            prev_hdr, text="COPY TEMPLATE", command=self.copy_template,
            fg_color="#4F46E5", hover_color="#4338CA",
            font=("Arial", 11, "bold"), height=32,
        )
        self.copy_btn.pack(side="right", padx=15, pady=10)

        out_wrap = ctk.CTkFrame(preview, fg_color="transparent")
        out_wrap.grid(row=1, column=0, sticky="nsew", padx=15, pady=(8, 12))
        out_wrap.grid_columnconfigure(0, weight=1)
        out_wrap.grid_rowconfigure(0, weight=1)

        self.output_text = ctk.CTkTextbox(
            out_wrap, fg_color="#313338", text_color="#DBDEE1",
            font=("Consolas", 13), wrap="word",
            border_width=1, border_color="#3F4147",
        )
        self.output_text.grid(row=0, column=0, sticky="nsew")

        # ── Removed: old left-panel tabs and right-panel bot_right. ───────
        # Saved Events are now accessible via the header "Current event" dropdown.
        # Initialise the dropdown with any already-loaded events.
        self.refresh_saved_events_ui()

    def save_event_lineup(self):
        title = self.event_title_var.get().strip()
        vol = self.event_vol_var.get().strip()
        if not title:
            messagebox.showwarning("Missing Title", "Please set an Event Title before saving the lineup.")
            return
            
        full_title = f"{title} VOL.{vol}" if vol.isdigit() else title
        
        event_data = {
            "title": title,
            "vol": vol,
            "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "timestamp": self.event_timestamp.get(),
            "master_duration": self.master_duration.get(),
            "genres": self.active_genres.copy(),
            "names_only": self.names_only.get(),
            "include_od": self.include_od.get(),
            "od_duration": self.od_duration.get(),
            "od_count": self.od_count.get(),
            "slots": []
        }
        
        for slot in self.slots:
            event_data["slots"].append({
                "name": slot.name_var.get().strip(),
                "genre": slot.genre_var.get().strip(),
                "duration": slot.duration_var.get()
            })
            
        # Check if updating existing or adding new
        existing_idx = None
        for i, ev in enumerate(self.saved_events):
            saved_full_title = f"{ev['title']} VOL.{ev['vol']}" if ev.get('vol', '').isdigit() else ev['title']
            if saved_full_title == full_title:
                existing_idx = i
                break
                
        if existing_idx is not None:
            if messagebox.askyesno("Update Event", f"'{full_title}' already exists. Overwrite?"):
                self.saved_events[existing_idx] = event_data
            else:
                return
        else:
            self.saved_events.append(event_data)

        self.saved_events.sort(key=lambda e: e.get('created_at', ''), reverse=True)
        self._save_events()
        self.refresh_saved_events_ui()
        messagebox.showinfo("Success", f"Event '{full_title}' saved successfully!")

    def load_event_lineup(self, event_data):
        self.event_title_var.set(event_data.get("title", ""))
        self.event_vol_var.set(event_data.get("vol", ""))
        self.event_timestamp.set(event_data.get("timestamp", ""))
        self.master_duration.set(event_data.get("master_duration", "60"))
        
        self.active_genres = event_data.get("genres", []).copy()
        self.refresh_genre_tags()
        
        self.names_only.set(event_data.get("names_only", False))
        self.include_od.set(event_data.get("include_od", False))
        self.od_duration.set(event_data.get("od_duration", "30"))
        self.od_count.set(event_data.get("od_count", "4"))
        self.toggle_od()
        
        # Clear existing slots
        for slot in self.slots:
            slot.destroy()
        self.slots.clear()
        
        # Add saved slots
        for slot_data in event_data.get("slots", []):
            self.add_slot(slot_data.get("name", ""), slot_data.get("genre", ""), int(slot_data.get("duration", 60)))
            
        self.update_output()
        
    def delete_event_lineup(self, event_data):
        full_title = f"{event_data['title']} VOL.{event_data.get('vol', '')}" if event_data.get('vol', '').isdigit() else event_data['title']
        if messagebox.askyesno("Confirm Delete", f"Delete saved event '{full_title}'?"):
            self.saved_events.remove(event_data)
            self._save_events()
            self.refresh_saved_events_ui()

    def get_dj_names(self):
        return [d["name"] for d in self.saved_djs]

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
        sf._parent_canvas.bind("<Configure>", lambda e: _check())
        sf._parent_frame.bind("<Configure>", lambda e: _check())
        sf.bind("<Configure>", lambda e: _check())

    def refresh_dj_roster_ui(self):
        for widget in self.dj_roster_scroll.winfo_children():
            widget.destroy()
        if not self.saved_djs:
            ctk.CTkLabel(
                self.dj_roster_scroll,
                text="No DJs saved yet.\nSave a DJ from a slot or press + NEW DJ.",
                text_color="#94A3B8", justify="center"
            ).pack(pady=20)
            return
        for idx, dj in enumerate(self.saved_djs):
            self._build_dj_card(self.dj_roster_scroll, dj, idx)

    def _build_dj_card(self, parent, dj, idx):
        card = ctk.CTkFrame(parent, fg_color="#0F172A", border_width=1, border_color="#334155", corner_radius=8)
        card.pack(fill="x", pady=(0, 6))

        expanded = ctk.BooleanVar(value=False)

        # ── Header row ──
        header = ctk.CTkFrame(card, fg_color="transparent", cursor="hand2")
        header.pack(fill="x", padx=10, pady=8)

        name_lbl = ctk.CTkLabel(
            header, text=dj.get("name", "Unnamed DJ"),
            font=("Arial", 13, "bold"), text_color="#CBD5E1", cursor="hand2"
        )
        name_lbl.pack(side="left")

        arrow_lbl = ctk.CTkLabel(header, text="▶", font=("Arial", 10), text_color="#475569", cursor="hand2")
        arrow_lbl.pack(side="right")

        # ── Body (collapsed by default) ──
        body = ctk.CTkFrame(card, fg_color="#1E293B", corner_radius=6)

        # Name field
        ctk.CTkLabel(body, text="NAME", font=("Arial", 9, "bold"), text_color="#94A3B8").pack(anchor="w", padx=10, pady=(10, 2))
        name_var = ctk.StringVar(value=dj.get("name", ""))
        ctk.CTkEntry(body, textvariable=name_var, fg_color="#0F172A", border_color="#334155", height=32).pack(fill="x", padx=10, pady=(0, 8))

        # Goggles field
        ctk.CTkLabel(body, text="🥽  LINE", font=("Arial", 9, "bold"), text_color="#94A3B8").pack(anchor="w", padx=10, pady=(0, 2))
        goggles_var = ctk.StringVar(value=dj.get("goggles", ""))
        ctk.CTkEntry(body, textvariable=goggles_var, placeholder_text="e.g.  Vinyl Specialist · Techno",
                     fg_color="#0F172A", border_color="#334155", height=32).pack(fill="x", padx=10, pady=(0, 8))

        # Link field
        ctk.CTkLabel(body, text="💻  LINK", font=("Arial", 9, "bold"), text_color="#94A3B8").pack(anchor="w", padx=10, pady=(0, 2))
        link_var = ctk.StringVar(value=dj.get("link", ""))
        ctk.CTkEntry(body, textvariable=link_var, placeholder_text="https://soundcloud.com/...",
                     fg_color="#0F172A", border_color="#334155", height=32).pack(fill="x", padx=10, pady=(0, 8))

        # Save / Delete buttons
        btn_row = ctk.CTkFrame(body, fg_color="transparent")
        btn_row.pack(fill="x", padx=10, pady=(0, 10))
        ctk.CTkButton(
            btn_row, text="💾 Save", width=80, height=30,
            fg_color="#059669", hover_color="#047857", font=("Arial", 11, "bold"),
            command=lambda: self._save_dj_card(idx, name_var, goggles_var, link_var, name_lbl)
        ).pack(side="left", padx=(0, 6))
        ctk.CTkButton(
            btn_row, text="🗑️", width=45, height=30, font=("Arial", 14),
            fg_color="#7F1D1D", hover_color="#991B1B",
            command=lambda i=idx: self._delete_dj_from_roster(i)
        ).pack(side="left")

        def toggle(event=None):
            if expanded.get():
                body.pack_forget()
                arrow_lbl.configure(text="▶")
                expanded.set(False)
            else:
                body.pack(fill="x", padx=6, pady=(0, 8))
                arrow_lbl.configure(text="▼")
                expanded.set(True)

        header.bind("<Button-1>", toggle)
        name_lbl.bind("<Button-1>", toggle)
        arrow_lbl.bind("<Button-1>", toggle)

    def _save_dj_card(self, idx, name_var, goggles_var, link_var, name_lbl):
        new_name = name_var.get().strip()
        if not new_name:
            return
        old_name = self.saved_djs[idx].get("name", "")
        self.saved_djs[idx] = {
            "name": new_name,
            "goggles": goggles_var.get().strip(),
            "link": link_var.get().strip()
        }
        self._save_library()
        name_lbl.configure(text=new_name)
        for slot in self.slots:
            slot.name_entry.configure(values=self.get_dj_names())
            if slot.name_var.get().strip() in (old_name, new_name):
                slot.update_dj_info()

    def _delete_dj_from_roster(self, idx):
        if idx < len(self.saved_djs):
            name = self.saved_djs[idx].get("name", "this DJ")
            if messagebox.askyesno("Confirm Delete", f"Remove '{name}' from the roster?"):
                self.saved_djs.pop(idx)
                self._save_library()
                self.refresh_dj_roster_ui()
                for slot in self.slots:
                    slot.name_entry.configure(values=self.get_dj_names())

    def add_new_dj_to_roster(self):
        self.saved_djs.append({"name": "New DJ", "goggles": "", "link": ""})
        self._save_library()
        self.refresh_dj_roster_ui()

    def refresh_saved_events_ui(self):
        """Update the header event-selector dropdown with the current saved events list."""
        if not hasattr(self, 'event_selector_combo'):
            return  # called before UI is built (first load_data call)
        if not self.saved_events:
            self.event_selector_combo.configure(values=["-- No saved events --"])
            self.event_selector_var.set("")
            return
        labels = []
        for ev in self.saved_events:
            full = f"{ev['title']} VOL.{ev.get('vol', '')}" if ev.get('vol', '').isdigit() else ev['title']
            ts = ev.get('timestamp', '')[:10]
            labels.append(f"{full}  [{ts}]")
        self.event_selector_combo.configure(values=labels)
        if self.event_selector_var.get() not in labels:
            self.event_selector_var.set("")

    def _load_event_by_selector(self, choice: str):
        """Load the event matching the dropdown selection."""
        for ev in self.saved_events:
            full = f"{ev['title']} VOL.{ev.get('vol', '')}" if ev.get('vol', '').isdigit() else ev['title']
            ts = ev.get('timestamp', '')[:10]
            label = f"{full}  [{ts}]"
            if label == choice:
                self.load_event_lineup(ev)
                return

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

    def add_initial_slots(self):
        self.add_slot("", "", int(self.master_duration.get()))

    def apply_master_duration(self):
        val = self.master_duration.get()
        for slot in self.slots:
            slot.duration_var.set(val)
        self.update_output()
        
    def add_genre_from_entry(self, event=None):
        val = self.genre_entry_var.get().strip()
        if val:
            self.add_genre(val)
            self.genre_entry_var.set("")
            
    def add_genre_from_dropdown(self, choice):
        if choice and choice != "Saved Genres" and choice != "---":
            self.add_genre(choice)
        self.genre_dropdown_var.set("")
        
    def add_genre(self, genre):
        genre = genre.strip()
        if genre.lower() not in [g.lower() for g in self.active_genres]:
            self.active_genres.append(genre)

        if genre.lower() not in [g.lower() for g in self.saved_genres]:
            self.saved_genres.append(genre)
            self._save_library()
            self.genre_dropdown.configure(values=["---"] + self.saved_genres)
            
        self.refresh_genre_tags()
        self.update_output()

    def delete_saved_genre(self):
        val = self.genre_entry_var.get().strip()
        if val and val in self.saved_genres:
            if messagebox.askyesno("Confirm Delete", f"Remove '{val}' from saved genres?"):
                self.saved_genres.remove(val)
                self._save_library()
                self.genre_entry_var.set("")
                self.genre_dropdown.configure(values=["---"] + self.saved_genres if self.saved_genres else ["---"])
                
    def remove_genre(self, genre):
        if genre in self.active_genres:
            self.active_genres.remove(genre)
        self.refresh_genre_tags()
        self.update_output()
        
    def refresh_genre_tags(self):
        for widget in self.genre_tags_frame.winfo_children():
            widget.destroy()
            
        current_row = 0
        current_col = 0
        for genre in self.active_genres:
            btn = ctk.CTkButton(self.genre_tags_frame, text=f"{genre} ✕", 
                                command=lambda g=genre: self.remove_genre(g),
                                fg_color="#3730A3", hover_color="#DC2626", 
                                height=24, font=("Arial", 11), width=50)
            btn.grid(row=current_row, column=current_col, padx=2, pady=2)
            current_col += 1
            if current_col > 3: # max 4 per row
                current_col = 0
                current_row += 1

    def add_slot(self, name="", genre="", duration=60):
        slot = SlotUI(self.slots_scroll, self, name, genre, duration)
        self.slots.append(slot)
        self.refresh_slots()
        self.update_output()
        
    def refresh_slots(self):
        for child in self.slots_scroll.winfo_children():
            child.pack_forget()
            
        for slot in self.slots:
            slot.pack(fill="x", pady=5)
            
    def move_slot(self, slot_ui, direction):
        idx = self.slots.index(slot_ui)
        new_idx = idx + direction
        if 0 <= new_idx < len(self.slots):
            self.slots[idx], self.slots[new_idx] = self.slots[new_idx], self.slots[idx]
            self.refresh_slots()
            self.update_output()

    def delete_slot(self, slot_ui):
        if slot_ui in self.slots:
            slot_ui.destroy()
            self.slots.remove(slot_ui)
            self.update_output()

    def toggle_od(self):
        if self.include_od.get():
            self.od_dur_label.configure(text_color="#94A3B8")
            self.od_count_label.configure(text_color="#94A3B8")
            self.od_dur_menu.configure(state="normal", text_color="#FFFFFF", button_color="#334155")
            self.od_count_menu.configure(state="normal", text_color="#FFFFFF", button_color="#334155")
        else:
            self.od_dur_label.configure(text_color="#475569")
            self.od_count_label.configure(text_color="#475569")
            self.od_dur_menu.configure(state="disabled", text_color="#475569", button_color="#1E293B")
            self.od_count_menu.configure(state="disabled", text_color="#475569", button_color="#1E293B")
        self.update_output()

    def set_plain_text(self):
        self.output_format.set("local")
        self.format_btn.configure(fg_color="transparent", text_color="#94A3B8")
        self.plain_btn.configure(fg_color="#1E293B", text_color="#34D399")
        self.update_output()

    def toggle_format(self):
        # This is now the "Discord Mode" button action
        self.output_format.set("discord")
        self.format_btn.configure(fg_color="#1E293B", text_color="#818CF8")
        self.plain_btn.configure(fg_color="transparent", text_color="#94A3B8")
        self.update_output()

    def update_output(self):
        lines = []
        out_format = self.output_format.get()
        
        event_title = self.event_title_var.get().strip()
        event_vol = self.event_vol_var.get().strip()
        
        if event_title:
            title_display = f"{event_title} VOL.{event_vol}" if event_vol.isdigit() else event_title
            if out_format == 'discord':
                lines.append(f"# {title_display}")
            else:
                lines.append(f"{title_display}")
                
        try:
            event_start_obj = datetime.datetime.strptime(self.event_timestamp.get(), "%Y-%m-%d %H:%M")
        except ValueError:
            event_start_obj = datetime.datetime.now()
            
        if out_format == 'discord':
            event_unix = int(event_start_obj.timestamp())
            lines.append(f"<t:{event_unix}:F> (<t:{event_unix}:R>)")
        else:
            # Get local timezone name
            local_tz = datetime.datetime.now().astimezone().tzname()
            # Try to shorten it if it's long (e.g. "Pacific Standard Time" -> "PST")
            if sum(1 for c in local_tz if c.isupper()) >= 3:
                local_tz = "".join([c for c in local_tz if c.isupper()])
            
            lines.append(f"{event_start_obj.strftime('%Y-%m-%d @ %H:%M')} ({local_tz})")
            
        # Genres Section
        if self.active_genres:
            genres_str = " // ".join(self.active_genres)
            if out_format == 'discord':
                lines.append(f"## {genres_str}")
            else:
                lines.append(f"{genres_str}")
            
        if out_format == 'discord':
            lines.append("### LINEUP")
        else:
            lines.append("LINEUP")
        
        current_pointer = event_start_obj
        names_only = self.names_only.get()
        
        for idx, slot in enumerate(self.slots, start=1):
            try:
                duration = int(slot.duration_var.get())
            except ValueError:
                duration = 0
                
            slot_name = slot.name_var.get().strip()
            slot_genre = slot.genre_var.get().strip()
            
            if slot_name:
                name_display = f"{idx} - {slot_name}"
            else:
                name_display = f"{idx}"
            
            if names_only:
                lines.append(f"• {name_display}")
            else:
                if out_format == 'discord':
                    unix = int(current_pointer.timestamp())
                    time_display = f"<t:{unix}:t>"
                    genre_str = f" ({slot_genre})" if slot_genre else ""
                    lines.append(f"{time_display} | **{name_display}**{genre_str}")
                else:
                    time_display = current_pointer.strftime('%H:%M')
                    genre_str = f" ({slot_genre})" if slot_genre else ""
                    lines.append(f"{time_display} | {name_display}{genre_str}")
                # Emit roster info lines if DJ is in the library
                if slot_name:
                    dj_info = next((d for d in self.saved_djs if d.get("name") == slot_name), None)
                    if dj_info:
                        if dj_info.get("goggles"):
                            lines.append(f"    🥽 {dj_info['goggles']}")
                        if dj_info.get("link"):
                            link = dj_info['link']
                            lines.append(f"    💻 {('<' + link + '>') if out_format == 'discord' else link}")

            current_pointer += datetime.timedelta(minutes=duration)
            
        if self.include_od.get():
            if out_format == 'discord':
                lines.append("\n### OPEN DECKS")
            else:
                lines.append("\nOPEN DECKS")
                
            try:
                od_count = int(self.od_count.get())
                od_dur = int(self.od_duration.get())
            except ValueError:
                od_count = 0
                od_dur = 0
                
            for i in range(od_count):
                if out_format == 'discord':
                    unix = int(current_pointer.timestamp())
                    time_display = f"<t:{unix}:t>"
                else:
                    time_display = current_pointer.strftime('%H:%M')
                lines.append(f"{time_display} | Slot {i+1}: [Available]")
                current_pointer += datetime.timedelta(minutes=od_dur)
                
        self.output_text.configure(state="normal")
        self.output_text.delete("1.0", "end")
        self.output_text.insert("1.0", "\n".join(lines))
        self.output_text.configure(state="disabled")

    def copy_template(self):
        text = self.output_text.get("1.0", "end-1c")
        self.clipboard_clear()
        self.clipboard_append(text)
        
        # Temp feedback
        self.copy_btn.configure(text="COPIED!", fg_color="#059669", hover_color="#047857")
        self.after(2000, lambda: self.copy_btn.configure(text="COPY TEMPLATE", fg_color="#4F46E5", hover_color="#4338CA"))

if __name__ == "__main__":
    app = App()
    app.mainloop()