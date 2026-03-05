"""
Module: fonts.py
Purpose: Load system font with extended Unicode ranges for icons.
         Provides Icon constants (standard Unicode symbols in Segoe UI / common system fonts).
"""
import os
import sys

import dearpygui.dearpygui as dpg


# ── Icon constants ─────────────────────────────────────────────────────────────
# All codepoints exist in Segoe UI (Windows), San Francisco (macOS),
# and DejaVu Sans (Linux) — no icon font needed.
class Icon:
    UP       = "\u2191"  # ↑
    DOWN     = "\u2193"  # ↓
    CLOSE    = "\u00D7"  # ×
    CHECK    = "\u2713"  # ✓
    ADD      = "+"
    EDIT     = "\u270E"  # ✎
    DELETE   = "\u2715"  # ✕
    SAVE     = "\u2714"  # ✔
    REFRESH  = "\u21BA"  # ↺
    RESTORE  = "\u21BB"  # ↻
    SEARCH   = "\u2315"  # ⌕
    DOWNLOAD = "\u2B07"  # ⬇
    UPLOAD   = "\u2B06"  # ⬆
    COPY     = "\u2398"  # ⎘
    FOLDER   = "\u2302"  # ⌂
    PREVIEW  = "\u25CE"  # ◎
    LINK     = "\u2197"  # ↗
    NOTES    = "\u2630"  # ☰
    COMPUTER = "\u2395"  # ⎕
    CHAT     = "\u2709"  # ✉
    CODE     = "\u2039"  # ‹ (used as </>)
    HEADSET  = "\u2641"  # ♁
    VR       = "\u29BE"  # ⦾
    SCHEDULE = "\u29D6"  # ⧖ hourglass
    TUNE     = "\u2261"  # ≡ (menu/tune)
    PASTE    = "\u2398"  # ⎘ clipboard


def setup_fonts(size: int = 14) -> int | None:
    """
    Load a system sans-serif font with extended Unicode symbol ranges.
    Call once after dpg.create_context() and before any widget creation.
    Returns the DPG font id (or None if no custom font was loaded).
    """
    sys_font = _find_system_font()
    if not sys_font:
        return None

    main_font = None
    with dpg.font_registry():
        with dpg.font(sys_font, size) as main_font:
            dpg.add_font_range_hint(dpg.mvFontRangeHint_Default)
            # Arrows & math operators (↑ ↓ ← → ↩ ↺ ↻ ⬆ ⬇ ✓ ✕ ✎ ⎘ ⌕ ☰ ≡ …)
            dpg.add_font_range(0x00A0, 0x02FF)  # Latin Extended + IPA
            dpg.add_font_range(0x2000, 0x27BF)  # General Punct → Dingbats
            dpg.add_font_range(0x2900, 0x2BFF)  # Supp Arrows B + Misc Symbols & Arrows

    if main_font is not None:
        dpg.bind_font(main_font)

    return main_font


def _find_system_font() -> str | None:
    """Return path to a suitable system sans-serif TTF, or None."""
    if sys.platform == "win32":
        for candidate in [
            "C:/Windows/Fonts/segoeui.ttf",
            "C:/Windows/Fonts/arial.ttf",
        ]:
            if os.path.exists(candidate):
                return candidate
    elif sys.platform == "darwin":
        for candidate in [
            "/System/Library/Fonts/SFNS.ttf",
            "/Library/Fonts/Arial.ttf",
        ]:
            if os.path.exists(candidate):
                return candidate
    else:
        for candidate in [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        ]:
            if os.path.exists(candidate):
                return candidate
    return None
