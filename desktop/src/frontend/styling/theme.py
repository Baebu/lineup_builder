"""
Module: theme.py
Purpose: Single source of truth for all visual constants.
Dependencies: None
Architecture: Provides default colors and styles. SettingsManager overrides colors at runtime.
"""

import dearpygui.dearpygui as dpg

# ─────────────────────────────────────────────────────────────────
# Colors
# ─────────────────────────────────────────────────────────────────

# Background layers
APP_BG          = "#000000"   # root window
PANEL_BG        = "#1E293B"   # panels, tabviews, cards in foreground
CARD_BG         = "#090E1A"   # input fields, deep cards

# Borders & hover
BORDER          = "#334155"   # all borders, secondary button backgrounds
HOVER           = "#475569"   # general hover state
SCROLLBAR       = "#475569"   # scrollbar thumb

# Text
TEXT_PRIMARY    = "#CBD5E1"   # main text / values
TEXT_SECONDARY  = "#94A3B8"   # labels / muted
TEXT_MUTED      = "#475569"   # disabled / very muted

# Interactive
ACCENT          = "#818CF8"   # section headers / highlights
PRIMARY         = "#4F46E5"   # main action buttons
PRIMARY_HOVER   = "#4338CA"
DANGER          = "#B91C1C"   # delete / destructive
DANGER_HOVER    = "#DC2626"
SUCCESS         = "#0B6E4F"   # save / confirm
SUCCESS_HOVER   = "#00533C"
ERROR           = "#EF4444"   # validation errors
WHITE           = "#FFFFFF"   # checkmarks, active text on filled buttons
DRAG_HINT       = "#B9B9B9"   # subtle secondary hint text ("drag to add →")
LOAD_BTN        = "#3730A3"   # indigo load-event button
IMPORT_SUCCESS  = "#34D399"   # green preview-success feedback text


# ─────────────────────────────────────────────────────────────────
# Dimensions
# ─────────────────────────────────────────────────────────────────

WIDGET_H        = 20    # standard input / button height
WIDGET_H_SM     = 20    # compact buttons
WIDGET_H_XS     = 20    # tiny buttons (edit popups, pill rows)
WIDGET_H_PILL   = 20    # header action pills

ICON_BTN_W      = 34    # width of square icon-only buttons

CARD_RADIUS     = 12    # rounded corners for cards / slots
PANEL_RADIUS    = 5     # rounded corners for panels, tabviews
BORDER_W        = 1     # standard border width

SCROLL_PAD_X    = 6     # horizontal padding: scroll container ↔ card edge
CARD_PAD_INNER  = 10    # internal card padding (content from card edge)

# ─────────────────────────────────────────────────────────────────
# Standardized UI Style — single source of truth for all DPG sizing
# ─────────────────────────────────────────────────────────────────

class Style:
    """Fixed style constants applied to the global DPG theme.

    All values are in pixels. Nothing here scales with ui_scale —
    font_scale handles perceived size; these stay crisp and tight.
    """

    # Padding inside frames (buttons, inputs, combos)
    FRAME_PAD_X     = 6
    FRAME_PAD_Y     = 2

    # Spacing between consecutive items
    ITEM_SPACING_X  = 6
    ITEM_SPACING_Y  = 4

    # Spacing inside compound widgets (label↔checkbox, etc.)
    INNER_SPACING_X = 4
    INNER_SPACING_Y = 4

    # Padding inside child_windows / popups / panels
    WINDOW_PAD_X    = 5
    WINDOW_PAD_Y    = 5

    # Rounding
    FRAME_ROUNDING    = CARD_RADIUS    # inputs, buttons, combos
    CHILD_ROUNDING    = PANEL_RADIUS   # child_window panels
    WINDOW_ROUNDING   = PANEL_RADIUS   # top-level / popup windows
    POPUP_ROUNDING    = CARD_RADIUS
    SCROLLBAR_ROUNDING = CARD_RADIUS
    GRAB_ROUNDING     = CARD_RADIUS
    TAB_ROUNDING      = PANEL_RADIUS

    # Scrollbar & grab
    SCROLLBAR_SIZE  = 12
    GRAB_MIN_SIZE   = 10

    # Borders
    WINDOW_BORDER   = 1
    FRAME_BORDER    = 1

    # Button text alignment (centered)
    BTN_ALIGN_X     = 0.5
    BTN_ALIGN_Y     = 0.5

# ─────────────────────────────────────────────────────────────────
# Dear PyGui helpers
# ─────────────────────────────────────────────────────────────────

def hex_to_dpg(hex_color: str, alpha: int = 255) -> tuple:
    """Convert a CSS hex color string to a DearPyGui (R, G, B, A) tuple."""
    h = hex_color.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), alpha)


# Pre-converted DPG color tuples (used by DPG theme and widget calls)
DPG_APP_BG         = hex_to_dpg(APP_BG)
DPG_PANEL_BG       = hex_to_dpg(PANEL_BG)
DPG_CARD_BG        = hex_to_dpg(CARD_BG)
DPG_BORDER         = hex_to_dpg(BORDER)
DPG_HOVER          = hex_to_dpg(HOVER)
DPG_SCROLLBAR      = hex_to_dpg(SCROLLBAR)
DPG_TEXT_PRIMARY   = hex_to_dpg(TEXT_PRIMARY)
DPG_TEXT_SECONDARY = hex_to_dpg(TEXT_SECONDARY)
DPG_TEXT_MUTED     = hex_to_dpg(TEXT_MUTED)
DPG_ACCENT         = hex_to_dpg(ACCENT)
DPG_PRIMARY        = hex_to_dpg(PRIMARY)
DPG_PRIMARY_HOVER  = hex_to_dpg(PRIMARY_HOVER)
DPG_DANGER         = hex_to_dpg(DANGER)
DPG_DANGER_HOVER   = hex_to_dpg(DANGER_HOVER)
DPG_SUCCESS        = hex_to_dpg(SUCCESS)
DPG_SUCCESS_HOVER  = hex_to_dpg(SUCCESS_HOVER)
DPG_ERROR          = hex_to_dpg(ERROR)
DPG_WHITE          = hex_to_dpg(WHITE)
DPG_DRAG_HINT      = hex_to_dpg(DRAG_HINT)
DPG_LOAD_BTN       = hex_to_dpg(LOAD_BTN)
DPG_IMPORT_SUCCESS = hex_to_dpg(IMPORT_SUCCESS)
