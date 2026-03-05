import json
import os

import dearpygui.dearpygui as dpg

from . import theme as T
from .fonts import Icon
from .utils import get_data_dir

SETTINGS_FILE = os.path.join(get_data_dir(), "settings.json")
DEFAULT_SETTINGS = {
    # Layout
    "left_panel_width": 380,
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
    # Scaling
    "ui_scale":        1.0,               # global font/UI scale multiplier
}

# (unused in DPG version)
_COLOR_ATTRS: list = []

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

        # Tracks the last-applied color for each key
        self._applied_settings: dict = dict(self.settings)
        self._global_theme = None

    def save_settings(self):
        try:
            with open(SETTINGS_FILE, "w") as f:
                json.dump({**self.settings, "user_presets": self.user_presets}, f, indent=2)
        except Exception as e:
            print(f"Error saving settings: {e}")

    # ── Theme application ─────────────────────────────────────────────────

    def apply_theme(self):
        """Build and bind a global DPG theme from current settings."""
        def _c(hex_val, alpha=255):
            h = hex_val.lstrip("#")
            r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
            return (r, g, b, alpha)

        s = self.settings
        with dpg.theme() as global_theme:
            with dpg.theme_component(dpg.mvAll):
                dpg.add_theme_color(dpg.mvThemeCol_WindowBg,           _c(s.get("card_bg",             "#0F172A")))
                dpg.add_theme_color(dpg.mvThemeCol_ChildBg,             _c(s.get("panel_bg",            "#1E293B")))
                dpg.add_theme_color(dpg.mvThemeCol_FrameBg,             _c(s.get("card_bg",             "#0F172A")))
                dpg.add_theme_color(dpg.mvThemeCol_FrameBgHovered,      _c(s.get("hover_color",         "#334155")))
                dpg.add_theme_color(dpg.mvThemeCol_FrameBgActive,       _c(s.get("primary_color",       "#4F46E5")))
                dpg.add_theme_color(dpg.mvThemeCol_Button,              _c(s.get("primary_color",       "#4F46E5")))
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered,       _c(s.get("primary_hover_color", "#4338CA")))
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive,        _c(s.get("primary_color",       "#4F46E5")))
                dpg.add_theme_color(dpg.mvThemeCol_Text,                _c(s.get("text_primary",        "#CBD5E1")))
                dpg.add_theme_color(dpg.mvThemeCol_TextDisabled,        _c(s.get("text_secondary",      "#94A3B8")))
                dpg.add_theme_color(dpg.mvThemeCol_Border,              _c(s.get("border_color",        "#334155")))
                dpg.add_theme_color(dpg.mvThemeCol_ScrollbarBg,         _c(s.get("card_bg",             "#0F172A")))
                dpg.add_theme_color(dpg.mvThemeCol_ScrollbarGrab,       _c(s.get("scrollbar_color",     "#334155")))
                dpg.add_theme_color(dpg.mvThemeCol_ScrollbarGrabHovered,_c(s.get("hover_color",         "#475569")))
                dpg.add_theme_color(dpg.mvThemeCol_ScrollbarGrabActive, _c(s.get("primary_color",       "#4F46E5")))
                dpg.add_theme_color(dpg.mvThemeCol_Header,              _c(s.get("primary_color",       "#4F46E5")))
                dpg.add_theme_color(dpg.mvThemeCol_HeaderHovered,       _c(s.get("primary_hover_color", "#4338CA")))
                dpg.add_theme_color(dpg.mvThemeCol_Tab,                 _c(s.get("panel_bg",            "#1E293B")))
                dpg.add_theme_color(dpg.mvThemeCol_TabHovered,          _c(s.get("primary_hover_color", "#4338CA")))
                dpg.add_theme_color(dpg.mvThemeCol_TabActive,           _c(s.get("primary_color",       "#4F46E5")))
                dpg.add_theme_color(dpg.mvThemeCol_TitleBg,             _c(s.get("panel_bg",            "#1E293B")))
                dpg.add_theme_color(dpg.mvThemeCol_TitleBgActive,       _c(s.get("primary_color",       "#4F46E5")))
                dpg.add_theme_color(dpg.mvThemeCol_PopupBg,             _c(s.get("card_bg",             "#0F172A")))
                dpg.add_theme_color(dpg.mvThemeCol_Separator,           _c(s.get("border_color",        "#334155")))
                dpg.add_theme_color(dpg.mvThemeCol_CheckMark,           _c(s.get("accent_color",        "#818CF8")))
                dpg.add_theme_color(dpg.mvThemeCol_SliderGrab,          _c(s.get("primary_color",       "#4F46E5")))
                dpg.add_theme_color(dpg.mvThemeCol_SliderGrabActive,    _c(s.get("primary_hover_color", "#4338CA")))
                # Rounding
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding,    T.CARD_RADIUS)
                dpg.add_theme_style(dpg.mvStyleVar_ChildRounding,     T.PANEL_RADIUS)
                dpg.add_theme_style(dpg.mvStyleVar_WindowRounding,    T.PANEL_RADIUS)
                dpg.add_theme_style(dpg.mvStyleVar_PopupRounding,     T.CARD_RADIUS)
                dpg.add_theme_style(dpg.mvStyleVar_ScrollbarRounding, T.CARD_RADIUS)
                dpg.add_theme_style(dpg.mvStyleVar_GrabRounding,      T.CARD_RADIUS)
                dpg.add_theme_style(dpg.mvStyleVar_TabRounding,       T.PANEL_RADIUS)
                dpg.add_theme_style(dpg.mvStyleVar_ButtonTextAlign,   0.5, 0.5)
                # Sizing (scales with ui_scale)
                sc = float(s.get("ui_scale", 1.0))
                dpg.add_theme_style(dpg.mvStyleVar_FramePadding,     int(8 * sc), int(6 * sc))
                dpg.add_theme_style(dpg.mvStyleVar_ItemSpacing,      int(8 * sc), int(6 * sc))
                dpg.add_theme_style(dpg.mvStyleVar_ItemInnerSpacing, int(4 * sc), int(4 * sc))
                dpg.add_theme_style(dpg.mvStyleVar_ScrollbarSize,    int(14 * sc))
                dpg.add_theme_style(dpg.mvStyleVar_GrabMinSize,      int(12 * sc))
        if self._global_theme is not None:
            try:
                dpg.delete_item(self._global_theme)
            except Exception:
                pass
        self._global_theme = global_theme
        dpg.bind_theme(global_theme)
        self._applied_settings = dict(self.settings)
        dpg.set_global_font_scale(float(s.get("ui_scale", 1.0)))
        self._set_titlebar_color(
            bg=s.get("panel_bg",      "#1E293B"),
            text=s.get("text_primary",  "#CBD5E1"),
            border=s.get("accent_color", "#818CF8"),
        )

    def _set_titlebar_color(self, bg: str, text: str, border: str):
        """Set the Windows title bar background, text, and border color via DWM API (Windows 11+)."""
        import sys
        if sys.platform != "win32":
            return
        import ctypes

        def _colorref(hex_val):
            h = hex_val.lstrip("#")
            r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
            return ctypes.c_ulong(b | (g << 8) | (r << 16))  # DWM expects BGR

        DWMWA_BORDER_COLOR  = 34
        DWMWA_CAPTION_COLOR = 35
        DWMWA_TEXT_COLOR    = 36
        try:
            hwnd = ctypes.windll.user32.FindWindowW(None, "Lineup Builder")
            if hwnd:
                for attr, val in [
                    (DWMWA_BORDER_COLOR,  _colorref(border)),
                    (DWMWA_CAPTION_COLOR, _colorref(bg)),
                    (DWMWA_TEXT_COLOR,    _colorref(text)),
                ]:
                    ctypes.windll.dwmapi.DwmSetWindowAttribute(
                        hwnd, attr, ctypes.byref(val), ctypes.sizeof(val)
                    )
        except Exception:
            pass

    # ── Preset helpers ────────────────────────────────────────────────────

    def apply_preset(self, preset_settings: dict):
        """Load a preset's color/font values and rebuild the settings tab."""
        self._applied_settings = dict(self.settings)
        self.settings.update(
            {k: v for k, v in preset_settings.items() if k in DEFAULT_SETTINGS}
        )
        self.save_settings()
        self.apply_theme()
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
        container = "settings_scroll"
        if not dpg.does_item_exist(container):
            return
        dpg.delete_item(container, children_only=True)

        # ── Theme Selection ───────────────────────────────────────────────
        dpg.add_text("THEME SELECTION", parent=container,
                     color=T.DPG_ACCENT)
        preset_names = [p["name"] for p in BUILTIN_PRESETS]
        current_selection = preset_names[0]
        for p in BUILTIN_PRESETS:
            if p["settings"]["primary_color"] == self.settings["primary_color"]:
                current_selection = p["name"]
                break
        dpg.add_text("Color Theme:", parent=container,
                     color=T.DPG_TEXT_SECONDARY)

        def _on_theme_change(s, a):
            choice = dpg.get_value(s)
            preset = next((p for p in BUILTIN_PRESETS if p["name"] == choice), None)
            if not preset:
                return
            old_font = self.settings.get("output_font_size", 14)
            self.settings.update(preset["settings"])
            self.settings["output_font_size"] = old_font
            self.save_settings()
            self.apply_theme()
            self._build_settings_tab()

        dpg.add_combo(items=preset_names, default_value=current_selection,
                      parent=container, width=-1, callback=_on_theme_change)
        dpg.add_separator(parent=container)

        # ── Output Preview ────────────────────────────────────────────────
        dpg.add_text("OUTPUT PREVIEW", parent=container,
                     color=T.DPG_ACCENT)
        dpg.add_text("Output Font Size:", parent=container,
                     color=T.DPG_TEXT_SECONDARY)

        def _on_font_size(s, a):
            size = int(dpg.get_value(s))
            self.settings["output_font_size"] = size
            self.save_settings()

        dpg.add_slider_int(
            min_value=10, max_value=24,
            default_value=self.settings.get("output_font_size", 14),
            parent=container, width=-1, callback=_on_font_size,
        )
        dpg.add_separator(parent=container)

        # ── UI Scale ──────────────────────────────────────────────────────
        dpg.add_text("UI SCALE", parent=container, color=T.DPG_ACCENT)
        current_scale = float(self.settings.get("ui_scale", 1.0))
        dpg.add_text(f"Scale: {current_scale:.2f}×", parent=container,
                     tag="ui_scale_label", color=T.DPG_TEXT_SECONDARY)

        def _on_scale(s, a):
            # slider gives int steps 75..200 representing 0.75..2.00
            raw = dpg.get_value(s)
            scale = round(raw / 100, 2)
            self.settings["ui_scale"] = scale
            self.save_settings()
            self.apply_theme()
            if dpg.does_item_exist("ui_scale_label"):
                dpg.set_value("ui_scale_label", f"Scale: {scale:.2f}×")

        dpg.add_slider_int(
            min_value=75, max_value=200,
            default_value=int(current_scale * 100),
            parent=container, width=-1, callback=_on_scale,
            format="",
        )
        dpg.add_separator(parent=container)
        dpg.add_button(
            label=Icon.REFRESH + " Reset to Defaults", parent=container, width=-1,
            callback=lambda: self._reset_to_defaults(),
        )

    def _reset_to_defaults(self):
        self._applied_settings = dict(self.settings)
        self.settings = dict(DEFAULT_SETTINGS)
        self.save_settings()
        self.apply_theme()
        self._build_settings_tab()

