import json
import os

import dearpygui.dearpygui as dpg

from . import theme as T
from .fonts import HEADER, LABEL, styled_text
from .utils import get_data_dir

SETTINGS_FILE = os.path.join(get_data_dir(), "settings.json")
DEFAULT_SETTINGS = {
    # Layout
    "left_panel_width": 325,
    "ui_scale": 1.0,

    # Fixed Button Colors (Theme independent)
    "primary_color":   "#4F46E5",
    "primary_hover":   "#4338CA",
    "secondary_color": "#334155",
    "secondary_hover": "#475569",
    "success_color":   "#059669",
    "success_hover":   "#047857",
    "danger_color":    "#DC2626",
    "danger_hover":    "#B91C1C",
    "accent_color":    "#818CF8",

    # Structural Colors (Vary by theme)
    "panel_bg":        "#1E293B",
    "card_bg":         "#0F172A",
    "border_color":    "#334155",
    "hover_color":     "#475569",
    "scrollbar_color": "#475569",
    "text_primary":    "#CBD5E1",
    "text_secondary":  "#94A3B8",
}

BUILTIN_PRESETS = [
    {
        "name": "Slate (Default)",
        "settings": dict(DEFAULT_SETTINGS),
    },
    {
        "name": "Midnight",
        "settings": {
            **DEFAULT_SETTINGS,
            "panel_bg":      "#0A1128",
            "card_bg":       "#040814",
            "border_color":  "#1C2A4A",
            "hover_color":   "#2A3B61",
            "scrollbar_color": "#1C2A4A",
            "text_primary":  "#E2E8F0",
            "text_secondary": "#94A3B8",
        },
    },
    {
        "name": "OLED Black",
        "settings": {
            **DEFAULT_SETTINGS,
            "panel_bg":      "#121212",
            "card_bg":       "#000000",
            "border_color":  "#27272A",
            "hover_color":   "#3F3F46",
            "scrollbar_color": "#27272A",
            "text_primary":  "#F4F4F5",
            "text_secondary": "#A1A1AA",
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
        self._danger_btn_theme = None

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
                dpg.add_theme_color(dpg.mvThemeCol_WindowBg,           _c(s.get("panel_bg",             "#1E293B")))
                dpg.add_theme_color(dpg.mvThemeCol_ChildBg,             _c(s.get("panel_bg",            "#1E293B")))
                dpg.add_theme_color(dpg.mvThemeCol_FrameBg,             _c(s.get("card_bg",             "#0F172A")))
                dpg.add_theme_color(dpg.mvThemeCol_FrameBgHovered,      _c(s.get("hover_color",         "#334155")))
                dpg.add_theme_color(dpg.mvThemeCol_FrameBgActive,       _c(s.get("primary_color",       "#4F46E5")))
                dpg.add_theme_color(dpg.mvThemeCol_Button,              _c(s.get("secondary_color",     "#334155")))
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered,       _c(s.get("secondary_hover",     "#475569")))
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive,        _c(s.get("secondary_color",     "#334155")))
                dpg.add_theme_color(dpg.mvThemeCol_Text,                _c(s.get("text_primary",        "#CBD5E1")))
                dpg.add_theme_color(dpg.mvThemeCol_TextDisabled,        _c(s.get("text_secondary",      "#94A3B8")))
                dpg.add_theme_color(dpg.mvThemeCol_Border,              _c(s.get("border_color",        "#334155")))
                dpg.add_theme_color(dpg.mvThemeCol_ScrollbarBg,         (0, 0, 0, 0))
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
                dpg.add_theme_color(dpg.mvThemeCol_PopupBg,             _c(s.get("panel_bg",            "#1E293B")))
                dpg.add_theme_color(dpg.mvThemeCol_Separator,           _c(s.get("border_color",        "#334155")))
                dpg.add_theme_color(dpg.mvThemeCol_CheckMark,           _c(s.get("accent_color",        "#818CF8")))
                dpg.add_theme_color(dpg.mvThemeCol_SliderGrab,          _c(s.get("primary_color",       "#4F46E5")))
                dpg.add_theme_color(dpg.mvThemeCol_SliderGrabActive,    _c(s.get("primary_hover_color", "#4338CA")))
                # Rounding  (from Style)
                S = T.Style
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding,    S.FRAME_ROUNDING)
                dpg.add_theme_style(dpg.mvStyleVar_ChildRounding,     S.CHILD_ROUNDING)
                dpg.add_theme_style(dpg.mvStyleVar_WindowRounding,    S.WINDOW_ROUNDING)
                dpg.add_theme_style(dpg.mvStyleVar_PopupRounding,     S.POPUP_ROUNDING)
                dpg.add_theme_style(dpg.mvStyleVar_ScrollbarRounding, S.SCROLLBAR_ROUNDING)
                dpg.add_theme_style(dpg.mvStyleVar_GrabRounding,      S.GRAB_ROUNDING)
                dpg.add_theme_style(dpg.mvStyleVar_TabRounding,       S.TAB_ROUNDING)
                dpg.add_theme_style(dpg.mvStyleVar_ButtonTextAlign,   S.BTN_ALIGN_X, S.BTN_ALIGN_Y)
                # Sizing  (fixed — font_scale handles perceived size)
                dpg.add_theme_style(dpg.mvStyleVar_FramePadding,     S.FRAME_PAD_X, S.FRAME_PAD_Y)
                dpg.add_theme_style(dpg.mvStyleVar_ItemSpacing,      S.ITEM_SPACING_X, S.ITEM_SPACING_Y)
                dpg.add_theme_style(dpg.mvStyleVar_ItemInnerSpacing, S.INNER_SPACING_X, S.INNER_SPACING_Y)
                dpg.add_theme_style(dpg.mvStyleVar_ScrollbarSize,    S.SCROLLBAR_SIZE)
                dpg.add_theme_style(dpg.mvStyleVar_GrabMinSize,      S.GRAB_MIN_SIZE)
                dpg.add_theme_style(dpg.mvStyleVar_WindowPadding,    S.WINDOW_PAD_X, S.WINDOW_PAD_Y)
                dpg.add_theme_style(dpg.mvStyleVar_WindowBorderSize, S.WINDOW_BORDER)
                dpg.add_theme_style(dpg.mvStyleVar_FrameBorderSize,  S.FRAME_BORDER)
        # ── Explicit Button Themes ──────────────────────────────────────
        _btn_tags = ["primary_btn_theme", "secondary_btn_theme",
                     "success_btn_theme", "danger_btn_theme"]
        for t in _btn_tags:
            try:
                if dpg.does_item_exist(t):
                    dpg.delete_item(t)
                if dpg.does_alias_exist(t):
                    dpg.remove_alias(t)
            except Exception:
                pass

        with dpg.theme(tag="primary_btn_theme"):
            with dpg.theme_component(dpg.mvButton):
                dpg.add_theme_color(dpg.mvThemeCol_Button,        _c(s.get("primary_color", "#4F46E5")))
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, _c(s.get("primary_hover", "#4338CA")))
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive,  _c(s.get("primary_color", "#4F46E5")))

        with dpg.theme(tag="secondary_btn_theme"):
            with dpg.theme_component(dpg.mvButton):
                dpg.add_theme_color(dpg.mvThemeCol_Button,        _c(s.get("secondary_color", "#334155")))
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, _c(s.get("secondary_hover", "#475569")))
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive,  _c(s.get("secondary_color", "#334155")))

        with dpg.theme(tag="success_btn_theme"):
            with dpg.theme_component(dpg.mvButton):
                dpg.add_theme_color(dpg.mvThemeCol_Button,        _c(s.get("success_color", "#059669")))
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, _c(s.get("success_hover", "#047857")))
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive,  _c(s.get("success_color", "#059669")))
                dpg.add_theme_color(dpg.mvThemeCol_Text,          (10, 10, 10, 255))

        with dpg.theme(tag="danger_btn_theme"):
            with dpg.theme_component(dpg.mvButton):
                dpg.add_theme_color(dpg.mvThemeCol_Button,        _c(s.get("danger_color", "#DC2626")))
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, _c(s.get("danger_hover", "#B91C1C")))
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive,  _c(s.get("danger_color", "#DC2626")))

        if self._global_theme is not None:
            try:
                dpg.delete_item(self._global_theme)
            except Exception:
                pass

        self._global_theme = global_theme
        self._danger_btn_theme = "danger_btn_theme"
        dpg.bind_theme(global_theme)

        self._applied_settings = dict(self.settings)
        dpg.set_global_font_scale(float(s.get("ui_scale", 0.75)))
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
        styled_text("   THEME SELECTION", HEADER, parent=container)
        preset_names = [p["name"] for p in BUILTIN_PRESETS]
        current_selection = preset_names[0]
        for p in BUILTIN_PRESETS:
            if p["settings"].get("panel_bg") == self.settings.get("panel_bg"):
                current_selection = p["name"]
                break

        def _on_theme_change(s, a):
            choice = dpg.get_value(s)
            preset = next((p for p in BUILTIN_PRESETS if p["name"] == choice), None)
            if not preset:
                return
            self.settings.update(preset["settings"])
            self.save_settings()
            self.apply_theme()
            self._build_settings_tab()

        _theme_combo = dpg.add_combo(items=preset_names, default_value=current_selection,
                      parent=container, width=-1, callback=_on_theme_change)
        with dpg.theme() as _center_theme:
            with dpg.theme_component(dpg.mvCombo):
                dpg.add_theme_style(dpg.mvStyleVar_ButtonTextAlign, 0.5, 0.5)
        dpg.bind_item_theme(_theme_combo, _center_theme)
        dpg.add_separator(parent=container)

        # ── UI Scale ──────────────────────────────────────────────────────
        styled_text("   UI SCALE", HEADER, parent=container)
        current_scale = float(self.settings.get("ui_scale", 1.0))
        styled_text(f"{current_scale:.2f}\u00d7", LABEL, parent=container,
                     tag="ui_scale_label")

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
            min_value=75, max_value=125,
            default_value=int(current_scale * 100),
            parent=container, width=-1, callback=_on_scale,
            format="",
        )
        dpg.add_button(
            label="Reset to Defaults", parent=container, width=-1,
            callback=lambda: self._reset_to_defaults(),
        )

    def _reset_to_defaults(self):
        self._applied_settings = dict(self.settings)
        self.settings = dict(DEFAULT_SETTINGS)
        self.save_settings()
        self.apply_theme()
        self._build_settings_tab()

