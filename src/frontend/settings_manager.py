import json
import os
from tkinter import colorchooser

import customtkinter as ctk

SETTINGS_FILE = "settings.json"
DEFAULT_SETTINGS = {
    # Output preview
    "output_font_size": 14,
    # Interactive colors
    "accent_color":    "#818CF8",   # section headers / highlights
    "primary_color":   "#4F46E5",   # main action buttons
    "danger_color":    "#7F1D1D",   # delete / destructive buttons
    "success_color":   "#059669",   # save / confirm buttons
    # Structural colors
    "panel_bg":        "#1E293B",   # panels, tabviews, cards in foreground
    "card_bg":         "#0F172A",   # deep cards, input field backgrounds
    "border_color":    "#334155",   # all borders, secondary button backgrounds
    "hover_color":     "#475569",   # general hover state
    "scrollbar_color": "#475569",   # scrollbar thumb
}

# All widget attributes that carry color values and should be walked
_COLOR_ATTRS = [
    "fg_color", "border_color", "hover_color",
    "button_color", "button_hover_color",
    "dropdown_fg_color", "dropdown_hover_color",
    "progress_color", "scrollbar_color",
]

BUILTIN_PRESETS = [
    {
        "name": "Default (Indigo)",
        "settings": dict(DEFAULT_SETTINGS),
    },
    {
        "name": "Emerald",
        "settings": {
            **DEFAULT_SETTINGS,
            "accent_color":  "#34D399",
            "primary_color": "#059669",
            "success_color": "#047857",
            "danger_color":  "#7F1D1D",
            "panel_bg":      "#1A2E24",
            "card_bg":       "#0D1F18",
            "border_color":  "#1F4D36",
            "hover_color":   "#2D6E4E",
            "scrollbar_color": "#2D6E4E",
        },
    },
    {
        "name": "Rose",
        "settings": {
            **DEFAULT_SETTINGS,
            "accent_color":  "#FB7185",
            "primary_color": "#E11D48",
            "success_color": "#059669",
            "danger_color":  "#7F1D1D",
            "panel_bg":      "#2D1B22",
            "card_bg":       "#1A0F14",
            "border_color":  "#4C1D30",
            "hover_color":   "#6D2840",
            "scrollbar_color": "#6D2840",
        },
    },
    {
        "name": "Slate (Mono)",
        "settings": {
            **DEFAULT_SETTINGS,
            "accent_color":  "#94A3B8",
            "primary_color": "#475569",
            "success_color": "#64748B",
            "danger_color":  "#7F1D1D",
            "panel_bg":      "#1E293B",
            "card_bg":       "#0F172A",
            "border_color":  "#334155",
            "hover_color":   "#475569",
            "scrollbar_color": "#475569",
        },
    },
]


class SettingsMixin:
    """Manages application settings: persistence, theme application, and Settings UI tab."""

    # ── Init & persistence ────────────────────────────────────────────────

    def load_settings(self):
        """Load settings from JSON, falling back to defaults. Must be called before setup_ui."""
        self.settings = dict(DEFAULT_SETTINGS)
        self.user_presets: list = []
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE) as f:
                    data = json.load(f)
                self.settings.update(
                    {k: v for k, v in data.items() if k in DEFAULT_SETTINGS}
                )
                self.user_presets = data.get("user_presets", [])
            except Exception:
                pass

        # Tracks the last-applied color for each key so repeated changes chain
        self._applied_settings: dict = dict(self.settings)

        # Explicit widget reference lists (for colors that need precise control)
        self._accent_labels:   list = []
        self._primary_buttons: list = []
        self._danger_buttons:  list = []
        self._success_buttons: list = []
        self._scrollable_frames: list = []

    def save_settings(self):
        try:
            with open(SETTINGS_FILE, "w") as f:
                json.dump({**self.settings, "user_presets": self.user_presets}, f, indent=2)
        except Exception as e:
            print(f"Error saving settings: {e}")

    # ── Theme application ─────────────────────────────────────────────────

    @staticmethod
    def _clean_list(lst: list) -> list:
        alive = []
        for w in lst:
            try:
                if w.winfo_exists():
                    alive.append(w)
            except Exception:
                pass
        return alive

    def _recolor_widgets(self, root, old: str, new: str):
        """Walk the full widget tree under *root* and replace every occurrence
        of *old* color with *new* across all color attributes."""
        if old.upper() == new.upper():
            return
        stack = list(root.winfo_children())
        while stack:
            w = stack.pop()
            for attr in _COLOR_ATTRS:
                try:
                    cur = w.cget(attr)
                    if isinstance(cur, str) and cur.upper() == old.upper():
                        w.configure(**{attr: new})
                except Exception:
                    pass
            try:
                stack.extend(w.winfo_children())
            except Exception:
                pass

    def apply_theme(self):
        """Apply current settings to all widgets. Uses the last-applied values
        as 'from' colors so chained changes work correctly."""
        applied = self._applied_settings

        # ── Recursive structural color walk ───────────────────────────────
        for key in ("panel_bg", "card_bg", "border_color", "hover_color"):
            old = applied.get(key, DEFAULT_SETTINGS[key])
            new = self.settings[key]
            self._recolor_widgets(self, old, new)

        # ── Explicit registered lists ─────────────────────────────────────
        self._accent_labels   = self._clean_list(self._accent_labels)
        self._primary_buttons = self._clean_list(self._primary_buttons)
        self._danger_buttons  = self._clean_list(self._danger_buttons)
        self._success_buttons = self._clean_list(self._success_buttons)
        self._scrollable_frames = self._clean_list(self._scrollable_frames)

        accent  = self.settings["accent_color"]
        primary = self.settings["primary_color"]
        danger  = self.settings["danger_color"]
        success = self.settings["success_color"]

        for lbl in self._accent_labels:
            try:
                lbl.configure(text_color=accent)
            except Exception:
                pass

        for btn in self._primary_buttons:
            try:
                btn.configure(fg_color=primary)
            except Exception:
                pass

        for btn in self._danger_buttons:
            try:
                btn.configure(fg_color=danger)
            except Exception:
                pass

        for btn in self._success_buttons:
            try:
                btn.configure(fg_color=success)
            except Exception:
                pass

        # ── Scrollbars ────────────────────────────────────────────────────
        old_sb = applied.get("scrollbar_color", DEFAULT_SETTINGS["scrollbar_color"])
        new_sb = self.settings["scrollbar_color"]
        for sf in self._scrollable_frames:
            try:
                if sf.winfo_exists() and hasattr(sf, "_scrollbar"):
                    cur = sf._scrollbar.cget("button_color")
                    if isinstance(cur, str) and cur.upper() == old_sb.upper():
                        sf._scrollbar.configure(
                            button_color=new_sb, button_hover_color=new_sb
                        )
                    else:
                        # always force to current setting
                        sf._scrollbar.configure(
                            button_color=new_sb, button_hover_color=new_sb
                        )
            except Exception:
                pass

        # ── Output preview font ───────────────────────────────────────────
        if hasattr(self, "output_text"):
            self.output_text.configure(font=("Consolas", self.settings["output_font_size"]))

        # ── Slot delete buttons (dynamically created) ─────────────────────
        for slot in getattr(self, "slots", []):
            try:
                slot.del_btn.configure(fg_color=danger)
                slot.del_dj_btn.configure(fg_color=danger)
            except Exception:
                pass

        # ── Snap applied state ────────────────────────────────────────────
        self._applied_settings = dict(self.settings)

    # ── Preset helpers ────────────────────────────────────────────────────

    def apply_preset(self, preset_settings: dict):
        """Load a preset's color/font values and rebuild the settings tab."""
        self._applied_settings = dict(self.settings)
        self.settings.update(
            {k: v for k, v in preset_settings.items() if k in DEFAULT_SETTINGS}
        )
        self.save_settings()
        self.apply_theme()
        tab = self.left_tabs.tab("Settings")
        for w in tab.winfo_children():
            w.destroy()
        self._build_settings_tab()

    def save_current_as_preset(self, name: str):
        name = name.strip()
        if not name:
            return
        # Overwrite if same name exists
        self.user_presets = [p for p in self.user_presets if p["name"] != name]
        self.user_presets.append({"name": name, "settings": dict(self.settings)})
        self.save_settings()

    def delete_preset(self, name: str):
        self.user_presets = [p for p in self.user_presets if p["name"] != name]
        self.save_settings()

    # ── Settings tab builder ──────────────────────────────────────────────

    def _build_settings_tab(self):
        tab = self.left_tabs.tab("Settings")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(0, weight=1)

        scroll = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        scroll.grid(row=0, column=0, sticky="nsew")
        scroll.grid_columnconfigure(0, weight=1)
        self._autohide_scrollbar(scroll)

        def _section(text):
            lbl = ctk.CTkLabel(
                scroll, text=text, font=("Arial", 11, "bold"),
                text_color=self.settings["accent_color"],
            )
            lbl.pack(anchor="w", padx=15, pady=(12, 4))
            self._accent_labels.append(lbl)

        # ── Output preview font size ──────────────────────────────────────
        _section("OUTPUT PREVIEW")

        font_card = ctk.CTkFrame(
            scroll, fg_color=self.settings["panel_bg"], corner_radius=8,
            border_width=1, border_color=self.settings["border_color"],
        )
        font_card.pack(fill="x", padx=15, pady=(0, 6))
        font_card.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            font_card, text="Font Size",
            font=("Arial", 11), text_color="#94A3B8",
        ).grid(row=0, column=0, padx=12, pady=12, sticky="w")

        font_size_lbl = ctk.CTkLabel(
            font_card, text=str(self.settings["output_font_size"]),
            font=("Arial", 12, "bold"), text_color="#CBD5E1", width=28,
        )
        font_size_lbl.grid(row=0, column=2, padx=(0, 12), pady=12)

        font_size_var = ctk.IntVar(value=self.settings["output_font_size"])

        def _on_font_size(val):
            size = int(val)
            self.settings["output_font_size"] = size
            font_size_lbl.configure(text=str(size))
            if hasattr(self, "output_text"):
                self.output_text.configure(font=("Consolas", size))
            self.save_settings()

        ctk.CTkSlider(
            font_card, from_=10, to=24, number_of_steps=14,
            variable=font_size_var, command=_on_font_size,
            fg_color=self.settings["border_color"],
            progress_color=self.settings["accent_color"],
            button_color=self.settings["primary_color"],
            button_hover_color="#4338CA",
        ).grid(row=0, column=1, padx=(0, 8), pady=12, sticky="ew")

        # ── Interactive colors ────────────────────────────────────────────
        _section("INTERACTIVE COLORS")

        interactive_defs = [
            ("Accent",   "accent_color",   "Section headers & highlights"),
            ("Primary",  "primary_color",  "Main action buttons"),
            ("Success",  "success_color",  "Save & confirm buttons"),
            ("Danger",   "danger_color",   "Delete & destructive buttons"),
        ]
        for name, key, desc in interactive_defs:
            self._make_color_row(scroll, name, key, desc)

        # ── Structural colors ─────────────────────────────────────────────
        _section("STRUCTURAL COLORS")

        structural_defs = [
            ("Panel BG",     "panel_bg",        "Panels, tabviews, foreground cards"),
            ("Card BG",      "card_bg",         "Input fields & deep card backgrounds"),
            ("Border",       "border_color",    "Borders, secondary button backgrounds"),
            ("Hover",        "hover_color",     "Hover state on buttons & controls"),
            ("Scrollbar",    "scrollbar_color", "Scrollbar thumb color"),
        ]
        for name, key, desc in structural_defs:
            self._make_color_row(scroll, name, key, desc)

        # ── Reset ─────────────────────────────────────────────────────────
        ctk.CTkButton(
            scroll, text="Reset to Defaults",
            fg_color=self.settings["border_color"],
            hover_color=self.settings["hover_color"],
            font=("Arial", 11), text_color="#94A3B8",
            command=self._reset_to_defaults,
        ).pack(fill="x", padx=15, pady=(12, 15))

    def _make_color_row(self, parent, label_text: str, key: str, description: str):
        row = ctk.CTkFrame(
            parent, fg_color=self.settings["panel_bg"], corner_radius=8,
            border_width=1, border_color=self.settings["border_color"],
        )
        row.pack(fill="x", padx=15, pady=(0, 5))
        row.grid_columnconfigure(1, weight=1)

        swatch = ctk.CTkButton(
            row, text="", width=32, height=32, corner_radius=6,
            fg_color=self.settings[key], hover_color=self.settings[key],
            border_width=1, border_color=self.settings["hover_color"],
        )
        swatch.grid(row=0, column=0, padx=(10, 8), pady=10)

        info_frame = ctk.CTkFrame(row, fg_color="transparent")
        info_frame.grid(row=0, column=1, sticky="ew")
        ctk.CTkLabel(
            info_frame, text=label_text,
            font=("Arial", 11, "bold"), text_color="#CBD5E1",
        ).pack(anchor="w")
        ctk.CTkLabel(
            info_frame, text=description,
            font=("Arial", 9), text_color="#475569",
        ).pack(anchor="w")

        hex_var = ctk.StringVar(value=self.settings[key])
        hex_entry = ctk.CTkEntry(
            row, textvariable=hex_var,
            width=90, height=32, fg_color=self.settings["card_bg"],
            border_color=self.settings["border_color"],
            font=("Consolas", 11), text_color="#CBD5E1",
        )
        hex_entry.grid(row=0, column=2, padx=(0, 10), pady=10)

        def _apply(val, k=key, sw=swatch, hvar=hex_var):
            val = val.strip()
            if not val.startswith("#"):
                val = "#" + val
            if len(val) == 7:
                try:
                    int(val[1:], 16)
                    val = val.upper()
                    self.settings[k] = val
                    sw.configure(fg_color=val, hover_color=val)
                    hvar.set(val)
                    self.apply_theme()
                    self.save_settings()
                except ValueError:
                    pass

        def _open_picker(k=key):
            result = colorchooser.askcolor(
                color=self.settings[k], title=f"Choose {label_text} Color"
            )
            if result and result[1]:
                _apply(result[1])

        swatch.configure(command=_open_picker)
        hex_entry.bind("<Return>",   lambda e: _apply(hex_var.get()))
        hex_entry.bind("<FocusOut>", lambda e: _apply(hex_var.get()))

    def _reset_to_defaults(self):
        # Keep applied_settings pointing at current so walker can find & replace
        self._applied_settings = dict(self.settings)
        self.settings = dict(DEFAULT_SETTINGS)
        self.save_settings()
        self.apply_theme()
        tab = self.left_tabs.tab("Settings")
        for w in tab.winfo_children():
            w.destroy()
        self._build_settings_tab()

