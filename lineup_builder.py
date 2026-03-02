import customtkinter as ctk
import copy
import datetime
import re
import yaml
import json
import os
import tkinter as tk
from tkinter import messagebox
from iconipy import IconFactory
from date_time_picker import CTkDateTimePicker


def _make_icon(factory, name, size):
    """Return a CTkImage from an iconipy factory."""
    img = factory.asPil(name)
    return ctk.CTkImage(light_image=img, dark_image=img, size=(size, size))

class SlotUI(ctk.CTkFrame):
    def __init__(self, master, app_ref, name="", genre="", duration=60):
        super().__init__(master, fg_color="#1E293B", corner_radius=10, border_width=1, border_color="#334155")
        self.app_ref = app_ref
        
        self.name_var = ctk.StringVar(value=name)
        self.genre_var = ctk.StringVar(value=genre)
        self.duration_var = ctk.StringVar(value=str(duration))
        
        self.name_var.trace_add("write", self._on_name_change)
        self.genre_var.trace_add("write", lambda *args: self.app_ref._schedule_update())
        self.duration_var.trace_add("write", lambda *args: self.app_ref._schedule_update())
        
        self.grid_columnconfigure(1, weight=3)
        self.grid_columnconfigure(2, weight=2)
        self.grid_columnconfigure(3, weight=1)

        # Drag handle
        self.grip = ctk.CTkButton(
            self, text="", image=self.app_ref.icon_grip,
            width=28, height=40, cursor="fleur",
            fg_color="transparent", hover_color="#334155"
        )
        self.grip.grid(row=0, column=0, padx=(8, 4), pady=10)
        self.grip.bind("<ButtonPress-1>",   lambda e: self.app_ref._slot_drag_start(e, self))
        self.grip.bind("<B1-Motion>",       lambda e: self.app_ref._slot_drag_motion(e, self))
        self.grip.bind("<ButtonRelease-1>", lambda e: self.app_ref._slot_drag_end(e, self))
        
        self.name_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.name_frame.grid(row=0, column=1, padx=5, pady=10, sticky="ew")
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
        self.info_label.grid_remove()  # hidden until there's content

        btn_frame = ctk.CTkFrame(self.name_frame, fg_color="transparent")
        btn_frame.grid(row=0, column=1)

        self.save_dj_btn = ctk.CTkButton(btn_frame, text="", image=self.app_ref.icon_save, width=34, height=34,
                                         fg_color="#334155", hover_color="#475569", command=self.save_dj)
        self.save_dj_btn.pack(side="left", padx=(0, 2))
        
        self.del_dj_btn = ctk.CTkButton(btn_frame, text="", image=self.app_ref.icon_trash, width=34, height=34,
                                        fg_color="#7F1D1D", hover_color="#991B1B", command=self.delete_saved_dj)
        self.del_dj_btn.pack(side="left")

        self.genre_entry = ctk.CTkEntry(self, textvariable=self.genre_var, placeholder_text="Genre",
                                        fg_color="#0F172A", border_width=1, border_color="#334155", height=35)
        self.genre_entry.grid(row=0, column=2, padx=5, pady=10, sticky="ew")
        
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
        self.dur_menu.grid(row=0, column=3, padx=5, pady=10, sticky="ew")
        
        self.del_btn = ctk.CTkButton(self, text="", image=self.app_ref.icon_trash, width=34, height=34,
                                     command=self.delete_slot, fg_color="#7F1D1D", hover_color="#991B1B")
        self.del_btn.grid(row=0, column=4, padx=10, pady=10)
        
    def _on_name_change(self, *args):
        self.app_ref._schedule_update()
        self.update_dj_info()

    def update_dj_info(self):
        val = self.name_var.get().strip()
        dj = next((d for d in self.app_ref.saved_djs if d.get("name") == val), None)
        has_stream = bool(dj and dj.get("stream"))
        self.info_label.configure(text="🎙 Stream linked" if has_stream else "")
        if has_stream:
            self.info_label.grid()
        else:
            self.info_label.grid_remove()

    def save_dj(self):
        val = self.name_var.get().strip()
        if val and val.lower() not in [n.lower() for n in self.app_ref.get_dj_names()]:
            self.app_ref.saved_djs.append({"name": val, "stream": ""})
            self.app_ref._schedule_save_library()
            self.app_ref.refresh_dj_roster_ui()
            self.app_ref.after(0, self.app_ref._refresh_slot_combos)

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
                self.app_ref.after(0, self.app_ref._refresh_slot_combos)
                for slot in self.app_ref.slots:
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
    WINDOW_STATE_FILE = "window_state.json"

    def __init__(self):
        super().__init__()
        
        self.title("Lineup Builder")
        self.geometry("1150x850")
        self._restore_window_state()
        
        ctk.set_appearance_mode("dark")
        self.configure(fg_color="#0F172A")
        
        self.grid_columnconfigure(0, weight=1, uniform="group1")
        self.grid_columnconfigure(1, weight=1, uniform="group1")
        self.grid_rowconfigure(0, weight=1)
        
        # Load icons via iconipy (lucide icon set)
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
        self.icon_save          = _make_icon(_icons, "save",                  16)
        self.icon_copy          = _make_icon(_icons, "copy",                  16)

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

        # Drag-and-drop state
        self._drag_ghost = None
        self._slot_ghost = None
        self._drop_indicator = None
        # Debounce state
        self._update_job  = None
        self._roster_job  = None
        self._save_lib_job = None
        # DJ roster search
        self.dj_search_var = ctk.StringVar()

        self.setup_ui()
        self.add_initial_slots()
        self.update_output()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _restore_window_state(self):
        try:
            if os.path.exists(self.WINDOW_STATE_FILE):
                with open(self.WINDOW_STATE_FILE, "r") as f:
                    state = json.load(f)
                geo = state.get("geometry")
                if geo:
                    self.geometry(geo)
                if state.get("maximized"):
                    self.after(50, lambda: self.state("zoomed"))
        except Exception:
            pass

    def _on_close(self):
        try:
            maximized = self.state() == "zoomed"
            if not maximized:
                geo = self.geometry()
            else:
                # Save a reasonable size so it restores cleanly when un-maximised
                geo = f"{self.winfo_width()}x{self.winfo_height()}+{self.winfo_x()}+{self.winfo_y()}"
            with open(self.WINDOW_STATE_FILE, "w") as f:
                json.dump({"geometry": geo, "maximized": maximized}, f)
        except Exception:
            pass
        self.destroy()
        
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
        self.saved_djs = []
        for _d in raw_djs:
            if not isinstance(_d, dict):
                self.saved_djs.append({"name": _d, "stream": ""})
            elif "stream" not in _d:
                # Migrate old goggles/link fields → stream
                self.saved_djs.append({
                    "name": _d.get("name", ""),
                    "stream": _d.get("goggles", "") or _d.get("link", "")
                })
            else:
                self.saved_djs.append(_d)
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

        # Tabs for Editor / Saved Events
        self.left_tabs = ctk.CTkTabview(left_panel, fg_color="#1E293B", corner_radius=10, border_width=1, border_color="#334155")
        self.left_tabs.grid(row=0, column=0, sticky="nsew")
        
        self.left_tabs.add("Event")
        self.left_tabs.add("DJ Roster")
        
        # Make content expand within tabs
        self.left_tabs.tab("Event").grid_columnconfigure(0, weight=1)
        self.left_tabs.tab("Event").grid_rowconfigure(0, weight=1)
        self.left_tabs.tab("DJ Roster").grid_columnconfigure(0, weight=1)
        self.left_tabs.tab("DJ Roster").grid_rowconfigure(0, weight=0)
        self.left_tabs.tab("DJ Roster").grid_rowconfigure(1, weight=1)

        # Tab: Event
        # Scrollable unified frame
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
        
        # Vol Input
        vol_frame = ctk.CTkFrame(title_input_frame, fg_color="transparent")
        vol_frame.grid(row=0, column=1, padx=(0, 5))
        ctk.CTkLabel(vol_frame, text="Vol.", font=("Arial", 11, "bold"), text_color="#94A3B8").pack(side="left", padx=(0, 3))
        self.vol_entry = ctk.CTkEntry(
            vol_frame, 
            textvariable=self.event_vol_var,
            width=40,
            height=35,
            fg_color="#0F172A",
            border_color="#334155"
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

        # Date & Time (Unified)
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
        
        self.genre_entry = ctk.CTkEntry(genre_input_frame, textvariable=self.genre_entry_var, placeholder_text="Type and press Enter...", fg_color="#0F172A", border_width=1, border_color="#334155", height=35)
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

        # Saved genres expandable panel (hidden by default)
        self._genre_saved_panel = ctk.CTkFrame(genre_frame, fg_color="#0F172A", border_width=1, border_color="#334155", corner_radius=6)
        
        self.genre_tags_frame = ctk.CTkFrame(genre_frame, fg_color="transparent", height=1)
        self.genre_tags_frame.pack(fill="x", pady=(5, 0))
        
        self.refresh_genre_saved_panel()
        
        # Traces
        self.event_timestamp.trace_add("write", lambda *args: self._schedule_update())

        # Saved Events Section (formerly its own tab)
        ctk.CTkLabel(config_frame, text="SAVED EVENTS", font=("Arial", 11, "bold"), text_color="#818CF8").pack(anchor="w", padx=15, pady=(15, 5))
        
        saved_events_container = ctk.CTkFrame(config_frame, fg_color="transparent")
        saved_events_container.pack(fill="x", padx=15, pady=(0, 15))
        saved_events_container.grid_columnconfigure(0, weight=1)
        
        self.saved_events_scroll = ctk.CTkScrollableFrame(saved_events_container, fg_color="transparent", height=200)
        self.saved_events_scroll.grid(row=0, column=0, sticky="nsew")
        self.saved_events_scroll.grid_columnconfigure(0, weight=1)
        self._autohide_scrollbar(self.saved_events_scroll)
        self.refresh_saved_events_ui()

        # Tab: DJ Roster
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
        top_right.grid_propagate(False) # Prevent content from causing expansion
        top_right.grid_columnconfigure(0, weight=1)
        top_right.grid_rowconfigure(0, weight=1)

        self.right_tabs = ctk.CTkTabview(
            top_right,
            fg_color="#1E293B",
            corner_radius=10,
            border_width=1,
            border_color="#334155",
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
        
        ctk.CTkButton(slots_header, text="", image=self.icon_save, command=self.save_event_lineup, width=34, height=34,
                      fg_color="#059669", hover_color="#047857").pack(side="right", padx=(5, 0))
        
        ctk.CTkButton(slots_header, text="+ ADD DJ", command=self.add_slot, width=80, height=32,
                      fg_color="#4F46E5", hover_color="#4338CA", font=("Arial", 11, "bold")).pack(side="right", padx=(5, 0))
        
        dur_values = [str(x) for x in range(15, 121, 15)]
        self.master_dur_menu = ctk.CTkOptionMenu(
            slots_header, 
            values=dur_values,
            variable=self.master_duration,
            height=35,
            width=90,
            fg_color="#0F172A",
            button_color="#334155",
            button_hover_color="#475569",
            text_color="#CBD5E1",
            dropdown_fg_color="#1E293B",
            dropdown_text_color="#CBD5E1",
            dropdown_hover_color="#334155"
        )
        self.master_dur_menu.pack(side="right", padx=(0, 5))
        ctk.CTkLabel(slots_header, text="Default length:", font=("Arial", 11), text_color="#94A3B8").pack(side="right", padx=(10, 5))
        self.master_duration.trace_add("write", lambda *args: self.apply_master_duration())
        
        self.slots_scroll = ctk.CTkScrollableFrame(slots_container_frame, fg_color="transparent")
        self.slots_scroll.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 0))
        self._autohide_scrollbar(self.slots_scroll)

        # ---- Open Decks row (bottom of slots panel) ----
        od_row = ctk.CTkFrame(slots_container_frame, fg_color="#1A1B1E", corner_radius=8)
        od_row.grid(row=2, column=0, sticky="ew", padx=15, pady=(6, 12))

        self.od_toggle_btn = ctk.CTkCheckBox(
            od_row, text="OPEN DECKS", variable=self.include_od,
            command=self.toggle_od,
            font=("Arial", 11, "bold"),
            text_color="#94A3B8",
            fg_color="#4F46E5", hover_color="#4338CA",
            checkmark_color="#FFFFFF",
            border_color="#334155"
        )
        self.od_toggle_btn.pack(side="left", padx=(12, 16), pady=8)

        self.od_count_label = ctk.CTkLabel(od_row, text="Amount:", font=("Arial", 11), text_color="#475569")
        self.od_count_label.pack(side="left", padx=(0, 4))
        self.od_count_menu = ctk.CTkOptionMenu(
            od_row,
            values=[str(x) for x in range(1, 11)],
            variable=self.od_count,
            command=lambda _: self.update_output(),
            width=75, height=30,
            state="disabled",
            fg_color="#0F172A",
            button_color="#1E293B",
            button_hover_color="#334155",
            text_color="#475569",
            dropdown_fg_color="#1E293B",
            dropdown_text_color="#CBD5E1",
            dropdown_hover_color="#334155"
        )
        self.od_count_menu.pack(side="left", padx=(0, 16))

        self.od_dur_label = ctk.CTkLabel(od_row, text="Slot length:", font=("Arial", 11), text_color="#475569")
        self.od_dur_label.pack(side="left", padx=(0, 4))
        self.od_dur_menu = ctk.CTkOptionMenu(
            od_row,
            values=[str(x) for x in range(15, 121, 15)],
            variable=self.od_duration,
            command=lambda _: self.update_output(),
            width=85, height=30,
            state="disabled",
            fg_color="#0F172A",
            button_color="#1E293B",
            button_hover_color="#334155",
            text_color="#475569",
            dropdown_fg_color="#1E293B",
            dropdown_text_color="#CBD5E1",
            dropdown_hover_color="#334155"
        )
        self.od_dur_menu.pack(side="left", padx=(0, 8))
        # ------------------------------------------------

        # ==========================================
        # RIGHT PANEL (BOTTOM): Output Preview
        # ==========================================
        bot_right = ctk.CTkFrame(self, fg_color="#1E1F22", corner_radius=15, border_width=1, border_color="#334155")
        bot_right.grid(row=1, column=1, padx=(10, 20), pady=(10, 20), sticky="nsew")
        bot_right.grid_columnconfigure(0, weight=1)
        bot_right.grid_rowconfigure(1, weight=1)

        # Preview Header (single row)
        preview_header = ctk.CTkFrame(bot_right, fg_color="#2B2D31", corner_radius=0)
        preview_header.grid(row=0, column=0, sticky="ew")

        header_row = ctk.CTkFrame(preview_header, fg_color="transparent")
        header_row.pack(fill="x", padx=0, pady=10)

        self.format_btn = ctk.CTkButton(header_row, text="Discord", image=self.icon_discord,
                                        compound="left", command=self.toggle_format,
                                        fg_color="#1E293B", hover_color="#334155", border_width=1, border_color="#334155",
                                        text_color="#818CF8", width=110, height=35, font=("Arial", 11, "bold"))
        self.format_btn.pack(side="left", padx=(15, 4))

        self.plain_btn = ctk.CTkButton(header_row, text="Plain Text", image=self.icon_text,
                                       compound="left", command=self.set_plain_text,
                                       fg_color="transparent", hover_color="#334155", border_width=1, border_color="#334155",
                                       text_color="#94A3B8", width=110, height=35, font=("Arial", 11, "bold"))
        self.plain_btn.pack(side="left", padx=(0, 4))

        self.quest_btn = ctk.CTkButton(
            header_row, text="Quest", image=self.icon_quest, compound="left", command=self.set_quest_view,
            fg_color="transparent", hover_color="#334155", border_width=1, border_color="#334155",
            text_color="#94A3B8", width=110, height=35, font=("Arial", 11, "bold")
        )
        self.quest_btn.pack(side="left", padx=(0, 4))

        self.pc_btn = ctk.CTkButton(
            header_row, text="PC", image=self.icon_pc, compound="left", command=self.set_pc_view,
            fg_color="transparent", hover_color="#334155", border_width=1, border_color="#334155",
            text_color="#94A3B8", width=80, height=35, font=("Arial", 11, "bold")
        )
        self.pc_btn.pack(side="left")

        # Text Output
        output_container = ctk.CTkFrame(bot_right, fg_color="transparent")
        output_container.grid(row=1, column=0, sticky="nsew", padx=20, pady=20)
        output_container.grid_columnconfigure(0, weight=1)
        output_container.grid_rowconfigure(0, weight=1)

        self.output_text = ctk.CTkTextbox(output_container, fg_color="#313338", text_color="#DBDEE1",
                                          font=("Consolas", 14), wrap="word", border_width=1, border_color="#3F4147")
        self.output_text.grid(row=0, column=0, sticky="nsew")

        # Hover copy icon overlaid on textbox (top-right corner)
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
            
        self.left_tabs.set("Event")
        self.update_output()
        
    def delete_event_lineup(self, event_data):
        full_title = f"{event_data['title']} VOL.{event_data.get('vol', '')}" if event_data.get('vol', '').isdigit() else event_data['title']
        if messagebox.askyesno("Confirm Delete", f"Delete saved event '{full_title}'?"):
            self.saved_events.remove(event_data)
            self._save_events()
            self.refresh_saved_events_ui()

    def duplicate_event_lineup(self, event_data):
        dupe = copy.deepcopy(event_data)
        # Increment volume number by 1
        try:
            dupe["vol"] = str(int(dupe.get("vol", "0")) + 1)
        except (ValueError, TypeError):
            dupe["vol"] = ""
        dupe["created_at"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.saved_events.append(dupe)
        self.saved_events.sort(key=lambda e: e.get("created_at", ""), reverse=True)
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

        # add="+" on all three bindings preserves CTkScrollableFrame's internal
        # handlers: _fit_frame_dimensions_to_canvas (canvas → card width) and
        # scrollregion update (inner frame → scroll range). Replacing either one
        # breaks full-width cards or scrolling when content grows.
        sf._parent_canvas.bind("<Configure>", lambda e: _check(), add="+")
        sf._parent_frame.bind("<Configure>", lambda e: _check(), add="+")
        sf.bind("<Configure>", lambda e: _check(), add="+")

    def refresh_dj_roster_ui(self):
        # Keep roster sorted alphabetically
        self.saved_djs.sort(key=lambda d: re.sub(r'[^a-z]', '', d.get("name", "").lower()))
        query = self.dj_search_var.get().strip().lower()
        filtered = [
            (idx, dj) for idx, dj in enumerate(self.saved_djs)
            if not query or query in dj.get("name", "").lower()
        ]
        for widget in self.dj_roster_scroll.winfo_children():
            widget.destroy()
        if not self.saved_djs:
            ctk.CTkLabel(
                self.dj_roster_scroll,
                text="No DJs saved yet.\nSave a DJ from a slot or press + NEW DJ.",
                text_color="#94A3B8", justify="center"
            ).pack(pady=20)
            return
        if not filtered:
            ctk.CTkLabel(
                self.dj_roster_scroll,
                text="No DJs match your search.",
                text_color="#94A3B8", justify="center"
            ).pack(pady=20)
            return
        for idx, dj in filtered:
            self._build_dj_card(self.dj_roster_scroll, dj, idx)

    def _build_dj_card(self, parent, dj, idx):
        card = ctk.CTkFrame(parent, fg_color="#0F172A", border_width=1, border_color="#334155", corner_radius=8)
        card.pack(fill="x", pady=(0, 6))

        expanded = ctk.BooleanVar(value=False)

        # ── Header row ──
        header = ctk.CTkFrame(card, fg_color="transparent", cursor="hand2")
        header.pack(fill="x", padx=10, pady=8)

        grip_btn = ctk.CTkButton(
            header, text="", image=self.icon_grip,
            width=24, height=32, cursor="fleur",
            fg_color="transparent", hover_color="#334155"
        )
        grip_btn.pack(side="left", padx=(0, 6))

        name_lbl = ctk.CTkLabel(
            header, text=dj.get("name", "Unnamed DJ"),
            font=("Arial", 13, "bold"), text_color="#CBD5E1", cursor="hand2"
        )
        name_lbl.pack(side="left")

        arrow_btn = ctk.CTkButton(
            header, text="", image=self.icon_chevron_up,
            width=32, height=32, fg_color="#334155", hover_color="#475569",
            command=lambda: toggle()
        )
        arrow_btn.pack(side="right")

        # ── Body (collapsed by default) ──
        body = ctk.CTkFrame(card, fg_color="#1E293B", corner_radius=6)

        # Name field
        ctk.CTkLabel(body, text="NAME", font=("Arial", 10, "bold"), text_color="#94A3B8").pack(anchor="w", padx=10, pady=(10, 2))
        name_var = ctk.StringVar(value=dj.get("name", ""))
        ctk.CTkEntry(body, textvariable=name_var, fg_color="#0F172A", border_color="#334155", height=32).pack(fill="x", padx=10, pady=(0, 8))

        # Stream link field
        ctk.CTkLabel(body, text="🎙  STREAM LINK", font=("Arial", 10, "bold"), text_color="#94A3B8").pack(anchor="w", padx=10, pady=(0, 2))
        stream_var = ctk.StringVar(value=dj.get("stream", ""))
        ctk.CTkEntry(body, textvariable=stream_var,
                     placeholder_text="https://stream.vrcdn.live/live/...",
                     fg_color="#0F172A", border_color="#334155", height=32).pack(fill="x", padx=10, pady=(0, 8))

        # Save / Delete buttons
        btn_row = ctk.CTkFrame(body, fg_color="transparent")
        btn_row.pack(fill="x", padx=10, pady=(0, 10))
        ctk.CTkButton(
            btn_row, text="", image=self.icon_save, width=34, height=34,
            fg_color="#059669", hover_color="#047857",
            command=lambda: self._save_dj_card(idx, name_var, stream_var, name_lbl)
        ).pack(side="left", padx=(0, 6))
        ctk.CTkButton(
            btn_row, text="", image=self.icon_trash, width=34, height=34,
            fg_color="#7F1D1D", hover_color="#991B1B",
            command=lambda i=idx: self._delete_dj_from_roster(i)
        ).pack(side="left")

        def toggle(event=None):
            if expanded.get():
                body.pack_forget()
                arrow_btn.configure(image=self.icon_chevron_up)
                expanded.set(False)
            else:
                body.pack(fill="x", padx=6, pady=(0, 8))
                arrow_btn.configure(image=self.icon_chevron_down)
                expanded.set(True)

        header.bind("<Button-1>", toggle)
        name_lbl.bind("<Button-1>", toggle)

        # Drag-and-drop: grip handle only → add to lineup
        # Read name from label at drag time so renames are reflected
        for w in (grip_btn,):
            w.bind("<B1-Motion>",       lambda e: self._on_dj_drag(e, name_lbl.cget("text")))
            w.bind("<ButtonRelease-1>", lambda e: self._end_dj_drag(e, name_lbl.cget("text")))

    # ── Slot reorder drag-and-drop ────────────────────────────────────────────

    def _slot_drag_start(self, event, slot_ui):
        self._slot_ghost = None  # will be created on first motion

    def _slot_drag_motion(self, event, slot_ui):
        name = slot_ui.name_var.get().strip() or "(empty)"
        if self._slot_ghost is None:
            self._slot_ghost = tk.Toplevel(self)
            self._slot_ghost.overrideredirect(True)
            self._slot_ghost.attributes("-alpha", 0.80)
            self._slot_ghost.configure(bg="#4F46E5")
            tk.Label(self._slot_ghost, text=f"  {name}  ",
                     font=("Arial", 12, "bold"), fg="white", bg="#4F46E5",
                     padx=10, pady=5).pack()
        self._slot_ghost.geometry(f"+{event.x_root + 12}+{event.y_root + 8}")
        # Show a drop indicator line between slots
        self._update_drop_indicator(event.y_root)

    def _slot_drag_end(self, event, slot_ui):
        if self._slot_ghost:
            self._slot_ghost.destroy()
            self._slot_ghost = None
        if self._drop_indicator:
            self._drop_indicator.place_forget()
        if slot_ui not in self.slots:
            return
        target_idx = self._get_drop_index(event.y_root)
        src_idx = self.slots.index(slot_ui)
        if target_idx is not None and target_idx != src_idx:
            self.slots.pop(src_idx)
            # Adjust for removal
            if target_idx > src_idx:
                target_idx -= 1
            self.slots.insert(target_idx, slot_ui)
            self.refresh_slots()
            self.update_output()

    def _get_drop_index(self, y_root):
        """Return the insertion index closest to y_root."""
        for i, slot in enumerate(self.slots):
            try:
                sy = slot.winfo_rooty()
                sh = slot.winfo_height()
                if y_root < sy + sh // 2:
                    return i
            except Exception:
                pass
        return len(self.slots)

    def _update_drop_indicator(self, y_root):
        """Draw a thin colored line between slots at the drop position."""
        if self._drop_indicator is None:
            self._drop_indicator = tk.Frame(
                self.slots_scroll, bg="#818CF8", height=3, bd=0
            )
        idx = self._get_drop_index(y_root)
        try:
            if idx < len(self.slots):
                ref = self.slots[idx]
                ry = ref.winfo_rooty() - self.slots_scroll.winfo_rooty()
                self._drop_indicator.place(x=0, y=max(0, ry - 2), relwidth=1.0)
            else:
                ref = self.slots[-1]
                ry = ref.winfo_rooty() + ref.winfo_height() - self.slots_scroll.winfo_rooty()
                self._drop_indicator.place(x=0, y=ry, relwidth=1.0)
            self._drop_indicator.lift()
        except Exception:
            pass

    # ── DJ roster drag-and-drop ───────────────────────────────────────────

    def _on_dj_drag(self, event, dj_name):
        """Create or move the drag ghost on B1-Motion."""
        if self._drag_ghost is None:
            # Create ghost only once motion starts
            self._drag_ghost = tk.Toplevel(self)
            self._drag_ghost.overrideredirect(True)
            self._drag_ghost.attributes("-alpha", 0.88)
            self._drag_ghost.configure(bg="#4F46E5")
            tk.Label(
                self._drag_ghost, text=f"  {dj_name}  ",
                font=("Arial", 12, "bold"), fg="white", bg="#4F46E5",
                padx=12, pady=6
            ).pack()
            self._drag_ghost.lift()
        self._drag_ghost.geometry(f"+{event.x_root + 14}+{event.y_root + 10}")
        # Highlight drop target
        if self._is_over_slots_panel(event.x_root, event.y_root):
            self.slots_scroll.configure(fg_color="#1E3A5F")
        else:
            self.slots_scroll.configure(fg_color="transparent")

    def _end_dj_drag(self, event, dj_name):
        """Drop DJ into lineup if released over the slots panel."""
        was_dragging = self._drag_ghost is not None
        if self._drag_ghost is not None:
            self._drag_ghost.destroy()
            self._drag_ghost = None
        self.slots_scroll.configure(fg_color="transparent")
        if was_dragging and self._is_over_slots_panel(event.x_root, event.y_root):
            try:
                dur = int(self.master_duration.get())
            except ValueError:
                dur = 60
            self.add_slot(dj_name, "", dur)
            # Ensure the lineup tab is visible
            try:
                self.right_tabs.set("Lineup")
            except Exception:
                pass

    def _is_over_slots_panel(self, x_root, y_root):
        """Return True if screen coordinates are within self.slots_scroll."""
        try:
            sx = self.slots_scroll.winfo_rootx()
            sy = self.slots_scroll.winfo_rooty()
            sw = self.slots_scroll.winfo_width()
            sh = self.slots_scroll.winfo_height()
            return sx <= x_root <= sx + sw and sy <= y_root <= sy + sh
        except Exception:
            return False

    # ─────────────────────────────────────────────────────────────────────

    def _save_dj_card(self, idx, name_var, stream_var, name_lbl):
        new_name = name_var.get().strip()
        if not new_name:
            return
        old_name = self.saved_djs[idx].get("name", "")
        self.saved_djs[idx] = {
            "name": new_name,
            "stream": stream_var.get().strip()
        }
        self._save_library()
        name_lbl.configure(text=new_name)
        self.after(0, self._refresh_slot_combos)
        for slot in self.slots:
            if slot.name_var.get().strip() in (old_name, new_name):
                slot.update_dj_info()

    def _delete_dj_from_roster(self, idx):
        if idx < len(self.saved_djs):
            name = self.saved_djs[idx].get("name", "this DJ")
            if messagebox.askyesno("Confirm Delete", f"Remove '{name}' from the roster?"):
                self.saved_djs.pop(idx)
                self._save_library()
                self.refresh_dj_roster_ui()
                self.after(0, self._refresh_slot_combos)

    def add_new_dj_to_roster(self):
        """Open a modal popup to collect DJ details before adding to the roster."""
        popup = ctk.CTkToplevel(self)
        popup.title("New DJ")
        popup.geometry("380x240")
        popup.resizable(False, False)
        popup.configure(fg_color="#0F172A")
        popup.grab_set()  # modal
        popup.focus_force()

        # Center over main window
        self.update_idletasks()
        x = self.winfo_x() + (self.winfo_width()  - 380) // 2
        y = self.winfo_y() + (self.winfo_height() - 240) // 2
        popup.geometry(f"380x240+{x}+{y}")

        content = ctk.CTkFrame(popup, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=20, pady=16)
        content.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(content, text="NAME", font=("Arial", 10, "bold"), text_color="#94A3B8").grid(row=0, column=0, sticky="w", pady=(0, 2))
        name_var = ctk.StringVar()
        name_entry = ctk.CTkEntry(content, textvariable=name_var, height=34,
                                   fg_color="#1E293B", border_color="#334155")
        name_entry.grid(row=1, column=0, sticky="ew", pady=(0, 10))

        ctk.CTkLabel(content, text="🎙  STREAM LINK", font=("Arial", 10, "bold"), text_color="#94A3B8").grid(row=2, column=0, sticky="w", pady=(0, 2))
        stream_var = ctk.StringVar()
        ctk.CTkEntry(content, textvariable=stream_var, placeholder_text="https://stream.vrcdn.live/live/...",
                     height=34, fg_color="#1E293B", border_color="#334155").grid(row=3, column=0, sticky="ew", pady=(0, 14))

        btn_row = ctk.CTkFrame(content, fg_color="transparent")
        btn_row.grid(row=4, column=0, sticky="e")

        def _save():
            name = name_var.get().strip()
            if not name:
                name_entry.configure(border_color="#EF4444")
                return
            # Duplicate check
            if name.lower() in [d.get("name", "").lower() for d in self.saved_djs]:
                name_entry.configure(border_color="#EF4444")
                ctk.CTkLabel(content, text="Name already exists.",
                             font=("Arial", 10), text_color="#EF4444").grid(row=5, column=0, sticky="w")
                return
            self.saved_djs.append({"name": name, "stream": stream_var.get().strip()})
            self._save_library()
            self.refresh_dj_roster_ui()
            self.after(0, self._refresh_slot_combos)
            popup.destroy()

        ctk.CTkButton(btn_row, text="Cancel", width=80, height=32,
                      fg_color="#334155", hover_color="#475569", font=("Arial", 11, "bold"),
                      command=popup.destroy).pack(side="left", padx=(0, 8))
        ctk.CTkButton(btn_row, text="", image=self.icon_save, width=34, height=32,
                      fg_color="#059669", hover_color="#047857",
                      command=_save).pack(side="left")

        popup.bind("<Return>", lambda e: _save())
        popup.bind("<Escape>", lambda e: popup.destroy())
        name_entry.focus_set()

    def refresh_saved_events_ui(self):
        for widget in self.saved_events_scroll.winfo_children():
            widget.destroy()
            
        if not self.saved_events:
            ctk.CTkLabel(self.saved_events_scroll, text="No saved events yet.", text_color="#94A3B8").pack(pady=20)
            return
            
        for ev in self.saved_events:
            frame = ctk.CTkFrame(self.saved_events_scroll, fg_color="#0F172A", border_width=1, border_color="#334155", corner_radius=8)
            frame.pack(fill="x", pady=5)
            
            full_title = f"{ev['title']} VOL.{ev.get('vol', '')}" if ev.get('vol', '').isdigit() else ev['title']
            
            info_frame = ctk.CTkFrame(frame, fg_color="transparent")
            info_frame.pack(side="left", padx=10, pady=10, fill="x", expand=True)
            
            ctk.CTkLabel(info_frame, text=full_title, font=("Arial", 14, "bold"), text_color="#CBD5E1").pack(anchor="w")
            
            # Sub info
            slots_count = len(ev.get("slots", []))
            timestamp = ev.get("timestamp", "")
            saved_at = ev.get("created_at", "")[:16]  # "YYYY-MM-DD HH:MM"
            sub = f"{timestamp} • {slots_count} slots"
            if saved_at:
                sub += f"  │  saved {saved_at}"
            ctk.CTkLabel(info_frame, text=sub, font=("Arial", 11), text_color="#94A3B8").pack(anchor="w")
            
            btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
            btn_frame.pack(side="right", padx=10, pady=10)
            
            ctk.CTkButton(btn_frame, text="Load", width=60, height=32, fg_color="#3730A3", hover_color="#4338CA",
                          font=("Arial", 11, "bold"),
                          command=lambda e=ev: self.load_event_lineup(e)).pack(side="left", padx=2)

            ctk.CTkButton(btn_frame, text="", image=self.icon_copy, width=34, height=34, fg_color="#334155", hover_color="#475569",
                          command=lambda e=ev: self.duplicate_event_lineup(e)).pack(side="left", padx=2)
                          
            ctk.CTkButton(btn_frame, text="", image=self.icon_trash, width=34, height=34, fg_color="#7F1D1D", hover_color="#991B1B",
                          command=lambda e=ev: self.delete_event_lineup(e)).pack(side="left", padx=2)

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

    def _toggle_genre_panel(self):
        if self._genre_panel_expanded:
            self._genre_saved_panel.pack_forget()
            self.genre_arrow_btn.configure(image=self.icon_chevron_down)
            self._genre_panel_expanded = False
        else:
            self._genre_saved_panel.pack(fill="x", pady=(4, 0), before=self.genre_tags_frame)
            self.genre_arrow_btn.configure(image=self.icon_chevron_up)
            self._genre_panel_expanded = True

    def refresh_genre_saved_panel(self):
        for w in self._genre_saved_panel.winfo_children():
            w.destroy()
        if not self.saved_genres:
            ctk.CTkLabel(self._genre_saved_panel, text="No saved genres yet.",
                         text_color="#94A3B8", font=("Arial", 11)).pack(padx=10, pady=8)
            return
        for genre in self.saved_genres:
            row = ctk.CTkFrame(self._genre_saved_panel, fg_color="transparent")
            row.pack(fill="x", padx=8, pady=3)
            ctk.CTkLabel(row, text=genre, font=("Arial", 12), text_color="#CBD5E1").pack(side="left")
            ctk.CTkButton(row, text="Add", width=54, height=28,
                          fg_color="#3730A3", hover_color="#4338CA", font=("Arial", 10, "bold"),
                          command=lambda g=genre: self.add_genre(g)).pack(side="right")
            
    def add_genre(self, genre):
        genre = genre.strip()
        if genre.lower() not in [g.lower() for g in self.active_genres]:
            self.active_genres.append(genre)

        if genre.lower() not in [g.lower() for g in self.saved_genres]:
            self.saved_genres.append(genre)
            self._save_library()
            self.refresh_genre_saved_panel()
            
        self.refresh_genre_tags()
        self.update_output()

    def delete_saved_genre(self):
        val = self.genre_entry_var.get().strip()
        if val and val in self.saved_genres:
            if messagebox.askyesno("Confirm Delete", f"Remove '{val}' from saved genres?"):
                self.saved_genres.remove(val)
                self._save_library()
                self.genre_entry_var.set("")
                self.refresh_genre_saved_panel()
                
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
                                height=28, font=("Arial", 11, "bold"), width=50)
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

    def _reset_format_btns(self):
        """Set all four format buttons to their inactive style."""
        self.format_btn.configure(fg_color="transparent", text_color="#94A3B8")
        self.plain_btn.configure(fg_color="transparent", text_color="#94A3B8")
        self.quest_btn.configure(fg_color="transparent", text_color="#94A3B8")
        self.pc_btn.configure(fg_color="transparent", text_color="#94A3B8")

    def set_plain_text(self):
        self.output_format.set("local")
        self._reset_format_btns()
        self.plain_btn.configure(fg_color="#1E293B", text_color="#34D399")
        self.update_output()

    def toggle_format(self):
        self.output_format.set("discord")
        self._reset_format_btns()
        self.format_btn.configure(fg_color="#1E293B", text_color="#818CF8")
        self.update_output()

    def set_quest_view(self):
        self.output_format.set("quest")
        self._reset_format_btns()
        self.quest_btn.configure(fg_color="#1E293B", text_color="#34D399")
        self.update_output()

    def set_pc_view(self):
        self.output_format.set("pc")
        self._reset_format_btns()
        self.pc_btn.configure(fg_color="#1E293B", text_color="#818CF8")
        self.update_output()

    def _schedule_roster_refresh(self, delay: int = 120):
        """Debounce refresh_dj_roster_ui so rapid typing only triggers one rebuild."""
        if self._roster_job is not None:
            self.after_cancel(self._roster_job)
        self._roster_job = self.after(delay, self._run_scheduled_roster_refresh)

    def _run_scheduled_roster_refresh(self):
        self._roster_job = None
        self.refresh_dj_roster_ui()

    def _schedule_save_library(self, delay: int = 500):
        """Debounce _save_library so rapid mutations coalesce into one write."""
        if self._save_lib_job is not None:
            self.after_cancel(self._save_lib_job)
        self._save_lib_job = self.after(delay, self._run_scheduled_save_library)

    def _run_scheduled_save_library(self):
        self._save_lib_job = None
        self._save_library()

    def _refresh_slot_combos(self):
        """Update all slot name-entry dropdowns in one deferred pass."""
        names = self.get_dj_names()
        for slot in self.slots:
            slot.name_entry.configure(values=names)

    def _schedule_update(self, delay: int = 150):
        """Debounce update_output: cancel any pending rebuild and reschedule."""
        if self._update_job is not None:
            self.after_cancel(self._update_job)
        self._update_job = self.after(delay, self._run_scheduled_update)

    def _run_scheduled_update(self):
        self._update_job = None
        self.update_output()

    @staticmethod
    def _vrcdn_convert(link: str, fmt: str) -> str:
        """Return VRCDN link in the correct format for fmt ('quest' or 'pc').
        Non-VRCDN links are returned unchanged."""
        if not link:
            return link
        # Match either known VRCDN format and extract the stream key
        m = re.match(r'(?:https://stream\.vrcdn\.live/live/|rtspt://stream\.vrcdn\.live/live/)(.+?)(?:\.live\.ts)?$', link)
        if not m:
            return link  # not a VRCDN link – return as-is
        key = m.group(1)
        if fmt == "quest":
            return f"https://stream.vrcdn.live/live/{key}.live.ts"
        else:
            return f"rtspt://stream.vrcdn.live/live/{key}"

    def update_output(self):
        out_format = self.output_format.get()

        # ── Quest / PC link-only views ────────────────────────────────────
        if out_format in ("quest", "pc"):
            links = []
            for slot in self.slots:
                slot_name = slot.name_var.get().strip()
                if slot_name:
                    dj_info = next((d for d in self.saved_djs if d.get("name") == slot_name), None)
                    if dj_info and dj_info.get("stream"):
                        links.append(self._vrcdn_convert(dj_info["stream"], out_format))
            body = "```\n" + "\n".join(links) + "\n```" if links else ""
            self.output_text.configure(state="normal")
            self.output_text.delete("1.0", "end")
            self.output_text.insert("1.0", body)
            self.output_text.configure(state="disabled")
            return

        # ── Discord / Plain Text views ────────────────────────────────────
        lines = []
        
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
            lines.append(f"# <t:{event_unix}:F> (<t:{event_unix}:R>)")
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
                name_display = slot_name
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

    def _on_output_leave(self, event):
        """Hide the copy icon only when the pointer truly leaves both the textbox and the icon."""
        widget_under = self.winfo_containing(event.x_root, event.y_root)
        if widget_under is None:
            self.copy_icon_btn.place_forget()
            return
        # Allow children of CTkTextbox / CTkButton (internal frames/labels) to keep it visible
        w_str = str(widget_under)
        if str(self.copy_icon_btn) in w_str or str(self.output_text) in w_str:
            return
        self.copy_icon_btn.place_forget()

    def copy_template(self):
        text = self.output_text.get("1.0", "end-1c")
        self.clipboard_clear()
        self.clipboard_append(text)
        # Temp feedback on the overlay icon
        self.copy_icon_btn.configure(text="✓", fg_color="#059669", hover_color="#047857", text_color="#FFFFFF")
        self.after(1500, lambda: self.copy_icon_btn.configure(text="⎘", fg_color="#3F4147", hover_color="#4F46E5", text_color="#94A3B8"))

    def copy_quest_links(self):
        """Copy the current Quest link view to clipboard."""
        self.set_quest_view()
        self._copy_output_to_clipboard()

    def copy_pc_links(self):
        """Copy the current PC link view to clipboard."""
        self.set_pc_view()
        self._copy_output_to_clipboard()

    def _copy_output_to_clipboard(self):
        text = self.output_text.get("1.0", "end-1c")
        self.clipboard_clear()
        self.clipboard_append(text)

if __name__ == "__main__":
    app = App()
    app.mainloop()