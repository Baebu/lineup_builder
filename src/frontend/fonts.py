"""
Module: fonts.py
Purpose: Central text style configuration and font management.
         Single source of truth for all text styling (colors, fonts).
         Provides Icon constants, text style presets, and a styled_text() helper.
"""
import os
import sys

import dearpygui.dearpygui as dpg

from . import theme as T


# ── Icon constants (plain text labels) ────────────────────────────────────────
class Icon:
    DRAG     = "\ue945"   # drag_indicator
    UP       = "\ue5ce"   # expand_less
    DOWN     = "\ue5cf"   # expand_more
    DROPDOWN = "\ue5c5"   # arrow_drop_down
    CLOSE    = "\ue5cd"   # close
    CHECK    = "\ue5ca"   # check
    ADD      = "\ue145"   # add
    EDIT     = "\ue3c9"   # edit
    DELETE   = "\ue872"   # delete
    SAVE     = "\ue161"   # save
    REFRESH  = "\ue5d5"   # refresh
    RESTORE  = "\ue8ba"   # restore
    SEARCH   = "\ue8b6"   # search
    DOWNLOAD = "\uf090"   # download
    UPLOAD   = "\ue2c6"   # upload
    COPY     = "\ue14d"   # content_copy
    FOLDER   = "\ue2c7"   # folder
    PREVIEW  = "\ue8f4"   # visibility
    LINK     = "\ue157"   # link
    NOTES    = "\ue873"   # description
    COMPUTER = "\ue30a"   # computer
    CHAT     = "\ue0b7"   # chat
    CODE     = "\ue86f"   # code
    HEADSET  = "\ue310"   # headset
    VR       = "\ue3c7"   # vrpano
    SCHEDULE = "\ue8b5"   # schedule
    TUNE     = "\ue429"   # tune
    PASTE    = "\ue14f"   # content_paste


# ── Font configuration ───────────────────────────────────────────────────────
FONT_SIZE_DEFAULT = 16    # base UI font size


# ── Text styles ──────────────────────────────────────────────────────────────
# Each style is a dict of kwargs forwarded to dpg.add_text().
# To change how any text category looks app-wide, edit its dict here.

HEADER  = {"color": T.DPG_ACCENT}           # section headers: "EVENT CONFIGURATION", "DJ ROSTER", etc.
LABEL   = {"color": T.DPG_TEXT_SECONDARY}    # field labels: "EVENT TITLE", "GENRES", etc.
BODY    = {"color": T.DPG_TEXT_PRIMARY}      # primary body text: event titles, DJ names
MUTED   = {"color": T.DPG_TEXT_MUTED}        # hints, disabled text, secondary info
ERROR   = {"color": T.DPG_ERROR}             # validation / error messages
HINT    = {"color": T.DPG_DRAG_HINT}         # subtle drag-hint text
SUCCESS = {"color": T.DPG_IMPORT_SUCCESS}    # success feedback messages


def styled_text(label: str, style: dict = None, **kwargs) -> int:
    """Create a dpg.add_text() with centralized styling.

    Usage::

        styled_text("EVENT CONFIG", HEADER)
        styled_text("field label", LABEL, tag="my_tag")
        styled_text("plain text")  # no style — uses DPG theme default
    """
    if style:
        merged = {**style, **kwargs}
    else:
        merged = kwargs
    return dpg.add_text(label, **merged)


# ── Font loading ─────────────────────────────────────────────────────────────

def _find_system_font() -> str | None:
    """Return path to a suitable system sans-serif TTF."""
    if sys.platform == "win32":
        candidates = ["C:/Windows/Fonts/segoeui.ttf", "C:/Windows/Fonts/arial.ttf"]
    elif sys.platform == "darwin":
        candidates = ["/System/Library/Fonts/SFNS.ttf", "/Library/Fonts/Arial.ttf"]
    else:
        candidates = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return None


def _find_icon_font() -> str | None:
    """Return path to the Material Symbols Rounded TTF bundled in assets/."""
    if getattr(sys, "frozen", False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    path = os.path.join(base, "assets", "Material_Symbols_Rounded", "static",
                        "MaterialSymbolsRounded-Regular.ttf")
    return path if os.path.exists(path) else None


# Module-level reference to the icon font (set by setup_fonts)
icon_font = None


def setup_fonts(size: int = FONT_SIZE_DEFAULT) -> int | None:
    """Load a system sans-serif font and a Material Symbols icon font.

    Call once after dpg.create_context() and before any widget creation.
    """
    global icon_font
    font_path = _find_system_font()
    if not font_path:
        return None

    icon_path = _find_icon_font()

    main_font = None
    with dpg.font_registry():
        with dpg.font(font_path, size) as main_font:
            dpg.add_font_range_hint(dpg.mvFontRangeHint_Default)
            dpg.add_font_range(0x00A0, 0x02FF)   # Latin Extended
        if icon_path:
            with dpg.font(icon_path, size) as icon_font:
                dpg.add_font_range(0xE000, 0xF8FF)  # PUA icon range

    if main_font is not None:
        dpg.bind_font(main_font)

    return main_font


def bind_icon_font(item_id: int):
    """Bind the icon font to a specific widget. No-op if icon font not loaded."""
    if icon_font is not None:
        dpg.bind_item_font(item_id, icon_font)
