import json
import os

import customtkinter as ctk
from . import theme as T
from .utils import get_data_dir

SETTINGS_FILE = os.path.join(get_data_dir(), "settings.json")
DEFAULT_SETTINGS = {
    # Output preview
    "output_font_size": 14,
    # Interactive colors
    "accent_color":    T.ACCENT,          # section headers / highlights
    "primary_color":   T.PRIMARY,         # main action buttons
    "danger_color":    T.DANGER,          # delete / destructive buttons
    "success_color":   T.SUCCESS,         # save / confirm buttons
    # Text colors
    "text_primary":    T.TEXT_PRIMARY,    # main text / values
    "text_secondary":  T.TEXT_SECONDARY,  # labels / muted text
    # Interactive Hovers
    "primary_hover_color": T.PRIMARY_HOVER,
    "danger_hover_color":  T.DANGER_HOVER,
    "success_hover_color": T.SUCCESS_HOVER,
    # Structural colors
    "panel_bg":        T.PANEL_BG,        # panels, tabviews, cards in foreground
    "card_bg":         T.CARD_BG,         # deep cards, input field backgrounds
    "border_color":    T.BORDER,          # all borders, secondary button backgrounds
    "hover_color":     T.HOVER,           # general hover state
    "scrollbar_color": T.SCROLLBAR,       # scrollbar thumb
}

# All widget attributes that carry color values and should be walked
_COLOR_ATTRS = [
    "fg_color", "border_color", "hover_color",
    "button_color", "button_hover_color",
    "dropdown_fg_color", "dropdown_hover_color",
    "progress_color", "scrollbar_color",
    "text_color", "placeholder_text_color",
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
            # New Theme
            "text_primary":    "#D1FAE5", # Emerald-100
            "text_secondary":  "#6EE7B7", # Emerald-300
            "primary_hover_color": "#047857",
            "danger_hover_color":  "#991B1B",
            "success_hover_color": "#064E3B",
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
            # New Theme
            "text_primary":    "#FFE4E6",
            "text_secondary":  "#FDA4AF",
            "primary_hover_color": "#BE123C",
            "danger_hover_color":  "#991B1B",
            "success_hover_color": "#047857",
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
            # New Theme
            "text_primary":    "#CBD5E1",
            "text_secondary":  "#94A3B8",
            "primary_hover_color": "#334155",
            "danger_hover_color":  "#991B1B",
            "success_hover_color": "#475569",
        },
    },
    {
        "name": "Ocean (Blue)",
        "settings": {
            **DEFAULT_SETTINGS,
            "accent_color":  "#38BDF8",  # Sky 400
            "primary_color": "#0284C7",  # Sky 600
            "success_color": "#059669",
            "danger_color":  "#9F1239",  # Rose 800
            "panel_bg":      "#0C4A6E",  # Sky 900
            "card_bg":       "#082F49",  # Sky 950
            "border_color":  "#0369A1",  # Sky 700
            "hover_color":   "#075985",  # Sky 800
            "scrollbar_color": "#075985",
            "text_primary":    "#E0F2FE", # Sky 100
            "text_secondary":  "#7DD3FC", # Sky 300
            "primary_hover_color": "#0369A1",
            "danger_hover_color":  "#881337",
        },
    },
    {
        "name": "Amber (Orange)",
        "settings": {
            **DEFAULT_SETTINGS,
            "accent_color":  "#F59E0B",  # Amber 500
            "primary_color": "#D97706",  # Amber 600
            "success_color": "#059669",
            "danger_color":  "#7F1D1D",
            "panel_bg":      "#451A03",  # Amber 950 (shifted to brown)
            "card_bg":       "#270E01",  # Deep brown
            "border_color":  "#78350F",  # Amber 900
            "hover_color":   "#92400E",  # Amber 800
            "scrollbar_color": "#92400E",
            "text_primary":    "#FEF3C7", # Amber 100
            "text_secondary":  "#FCD34D", # Amber 300
            "primary_hover_color": "#B45309",
            "danger_hover_color":  "#991B1B",
        },
    },
    {
        "name": "Violet (Deep)",
        "settings": {
            **DEFAULT_SETTINGS,
            "accent_color":  "#A78BFA",  # Violet 400
            "primary_color": "#7C3AED",  # Violet 600
            "success_color": "#059669",
            "danger_color":  "#831843",  # Pink 900
            "panel_bg":      "#2E1065",  # Violet 950
            "card_bg":       "#170536",  # Deep violet
            "border_color":  "#5B21B6",  # Violet 800
            "hover_color":   "#6D28D9",  # Violet 700
            "scrollbar_color": "#6D28D9",
            "text_primary":    "#EDE9FE", # Violet 100
            "text_secondary":  "#C4B5FD", # Violet 300
            "primary_hover_color": "#6D28D9",
            "danger_hover_color":  "#831843",
        },
    },
    {
        "name": "Crimson (Red)",
        "settings": {
            **DEFAULT_SETTINGS,
            "accent_color":  "#F87171",  # Red 400
            "primary_color": "#DC2626",  # Red 600
            "success_color": "#059669",
            "danger_color":  "#450A0A",  # Red 950
            "panel_bg":      "#450A0A",  # Red 950
            "card_bg":       "#280505",  # Deep red
            "border_color":  "#7F1D1D",  # Red 900
            "hover_color":   "#991B1B",  # Red 800
            "scrollbar_color": "#991B1B",
            "text_primary":    "#FEE2E2", # Red 100
            "text_secondary":  "#FCA5A5", # Red 300
            "primary_hover_color": "#B91C1C",
            "danger_hover_color":  "#450A0A",
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
        full_keys = [
            "panel_bg", "card_bg", "border_color", "hover_color",
            "text_primary", "text_secondary"
        ]
        for key in full_keys:
            old = applied.get(key, DEFAULT_SETTINGS[key])
            new = self.settings[key]
            self._recolor_widgets(self, old, new)
            applied[key] = new  # Keep track for next update!

        # ── Explicit registered lists ─────────────────────────────────────
        self._accent_labels   = self._clean_list(self._accent_labels)
        self._primary_buttons = self._clean_list(self._primary_buttons)
        self._danger_buttons  = self._clean_list(self._danger_buttons)
        self._success_buttons = self._clean_list(self._success_buttons)
        self._scrollable_frames = self._clean_list(self._scrollable_frames)

        accent  = self.settings["accent_color"]
        primary = self.settings["primary_color"]
        p_hover = self.settings["primary_hover_color"]
        danger  = self.settings["danger_color"]
        d_hover = self.settings["danger_hover_color"]
        success = self.settings["success_color"]
        s_hover = self.settings["success_hover_color"]

        applied["accent_color"]  = accent
        applied["primary_color"] = primary
        applied["danger_color"]  = danger
        applied["success_color"] = success

        for lbl in self._accent_labels:
            try:
                lbl.configure(text_color=accent)
            except Exception:
                pass

        for btn in self._primary_buttons:
            try:
                btn.configure(fg_color=primary, hover_color=p_hover)
            except Exception:
                pass

        for btn in self._danger_buttons:
            try:
                btn.configure(fg_color=danger, hover_color=d_hover)
            except Exception:
                pass

        for btn in self._success_buttons:
            try:
                btn.configure(fg_color=success, hover_color=s_hover)
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

        # ── Output preview colors & font ──────────────────────────────────
        if hasattr(self, "output_text"):
            self.output_text.configure(
                font=("Consolas", self.settings["output_font_size"]),
                fg_color=self.settings.get("card_bg", "#0F172A"),
                text_color=self.settings.get("text_primary", "#CBD5E1"),
                border_color=self.settings.get("border_color", "#334155"),
            )
        if hasattr(self, "copy_icon_btn"):
            self.copy_icon_btn.configure(
                fg_color=self.settings.get("border_color", "#334155"),
                hover_color=self.settings.get("primary_color", "#4F46E5"),
                text_color=self.settings.get("text_secondary", "#94A3B8"),
            )

        # ── Structural panels ─────────────────────────────────────────────
        if hasattr(self, "_bot_right"):
            self._bot_right.configure(
                fg_color=self.settings.get("panel_bg", "#1E293B"),
                border_color=self.settings.get("border_color", "#334155"),
            )
        if hasattr(self, "_preview_header"):
            self._preview_header.configure(
                fg_color=self.settings.get("card_bg", "#0F172A"),
            )
        if hasattr(self, "_od_row"):
            self._od_row.configure(
                fg_color=self.settings.get("card_bg", "#0F172A"),
            )

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
        # ── Theme Selection ───────────────────────────────────────────────
        _section("THEME SELECTION")

        theme_card = ctk.CTkFrame(
            scroll, fg_color=self.settings["panel_bg"], corner_radius=12,
            border_width=1, border_color=self.settings["border_color"],
        )
        theme_card.pack(fill="x", padx=15, pady=(0, 6))
        theme_card.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            theme_card, text="Color Theme",
            font=("Arial", 11), text_color=self.settings.get("text_secondary", "#94A3B8"),
        ).grid(row=0, column=0, padx=12, pady=12, sticky="w")

        # 1. Get presets names
        preset_names = [p["name"] for p in BUILTIN_PRESETS]

        # 2. Determine current preset
        current_selection = preset_names[0]
        # Simple heuristic: check if primary_color matches a preset
        # (A full dict compare is better but this is likely sufficient for UI state)
        for p in BUILTIN_PRESETS:
            if p["settings"]["primary_color"] == self.settings["primary_color"]:
                current_selection = p["name"]
                break

        def _on_theme_change(choice):
            # Find the preset
            preset = next((p for p in BUILTIN_PRESETS if p["name"] == choice), None)
            if not preset:
                return
            
            # Update settings from preset (excluding font size to preserve it)
            old_font = self.settings.get("output_font_size", 14)
            self.settings.update(preset["settings"])
            self.settings["output_font_size"] = old_font
            
            # Save & Apply
            self.save_settings()
            self.apply_theme()
            
            # Rebuild this settings tab to reflect new colors immediately
            # (panel background, dropdown colors, etc)
            for widget in tab.winfo_children():
                widget.destroy()
            self._build_settings_tab()

        theme_menu = ctk.CTkOptionMenu(
            theme_card,
            values=preset_names,
            command=_on_theme_change,
            fg_color=self.settings.get("card_bg", "#0F172A"),
            button_color=self.settings["primary_color"],
            button_hover_color=self.settings.get("primary_hover_color", self.settings["primary_color"]),
            text_color=self.settings.get("text_primary", "#CBD5E1"),
            dropdown_fg_color=self.settings.get("card_bg", "#0F172A"),
            dropdown_hover_color=self.settings.get("hover_color", "#334155"),
            dropdown_text_color=self.settings.get("text_primary", "#CBD5E1"),
            width=140
        )
        theme_menu.grid(row=0, column=2, padx=(0, 12), pady=12, sticky="e")
        theme_menu.set(current_selection)

        # ── Output Preview ────────────────────────────────────────────────
        _section("OUTPUT PREVIEW")

        font_card = ctk.CTkFrame(
            scroll, fg_color=self.settings["panel_bg"], corner_radius=12,
            border_width=1, border_color=self.settings["border_color"],
        )
        font_card.pack(fill="x", padx=15, pady=(0, 6))
        font_card.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            font_card, text="Font Size",
            font=("Arial", 11), text_color=self.settings.get("text_secondary", "#94A3B8"),
        ).grid(row=0, column=0, padx=12, pady=12, sticky="w")

        font_size_lbl = ctk.CTkLabel(
            font_card, text=str(self.settings["output_font_size"]),
            font=("Arial", 12, "bold"), text_color=self.settings.get("text_primary", "#CBD5E1"), width=28,
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
            button_hover_color=self.settings.get("primary_hover_color", "#4338CA"),
        ).grid(row=0, column=1, padx=(0, 8), pady=12, sticky="ew")

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

