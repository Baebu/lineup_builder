"""
Module: theme.py
Purpose: Single source of truth for all visual constants.
Dependencies: None
Architecture: Provides default styling dicts. SettingsManager overrides colors at runtime.
"""

# ─────────────────────────────────────────────────────────────────
# Colors
# ─────────────────────────────────────────────────────────────────

# Background layers
APP_BG          = "#000000"   # root window
PANEL_BG        = "#1E293B"   # panels, tabviews, cards in foreground
CARD_BG         = "#0F172A"   # input fields, deep cards

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
DANGER          = "#7F1D1D"   # delete / destructive
DANGER_HOVER    = "#991B1B"
SUCCESS         = "#059669"   # save / confirm
SUCCESS_HOVER   = "#047857"
ERROR           = "#EF4444"   # validation errors
WHITE           = "#FFFFFF"   # checkmarks, active text on filled buttons
DRAG_HINT       = "#B9B9B9"   # subtle secondary hint text ("drag to add →")
LOAD_BTN        = "#3730A3"   # indigo load-event button
IMPORT_SUCCESS  = "#34D399"   # green preview-success feedback text


# ─────────────────────────────────────────────────────────────────
# Dimensions
# ─────────────────────────────────────────────────────────────────

WIDGET_H        = 35    # standard input / button height
WIDGET_H_SM     = 32    # compact buttons
WIDGET_H_XS     = 28    # tiny buttons (edit popups, pill rows)
WIDGET_H_PILL   = 26    # header action pills

ICON_BTN_W      = 34    # width of square icon-only buttons

CARD_RADIUS     = 12    # rounded corners for cards / slots
PANEL_RADIUS    = 5     # rounded corners for panels, tabviews
BORDER_W        = 1     # standard border width

SCROLL_PAD_X    = 6     # horizontal padding: scroll container ↔ card edge
CARD_PAD_INNER  = 10    # internal card padding (content from card edge)


# ─────────────────────────────────────────────────────────────────
# Fonts
# ─────────────────────────────────────────────────────────────────

FONT_TINY       = ("Arial", 12)           # very small text (genre pills, timestamps)
FONT_LABEL      = ("Arial", 14, "bold")   # section field labels (all-caps)
FONT_SMALL      = ("Arial", 12)           # secondary text (field values, pill text)
FONT_SMALL_BOLD = ("Arial", 12, "bold")   # emphasized secondary text (pill text when active)
FONT_BODY       = ("Arial", 14)           # main text (DJ names, event titles, tab labels)
FONT_BODY_BOLD  = ("Arial", 14, "bold")   # emphasized main text (section headers, active tab labels)
FONT_VALUE      = ("Arial", 12, "bold")   # prominent values (DJ name, event title)
FONT_MONO       = ("Consolas", 14)        # output preview


# ─────────────────────────────────────────────────────────────────
# Reusable widget-style dicts
# ─────────────────────────────────────────────────────────────────

# Text inputs
ENTRY = dict(
    fg_color=CARD_BG,
    border_width=BORDER_W,
    border_color=BORDER,
    height=WIDGET_H,
    corner_radius=6,
)

# Drop-down combo boxes (name entry, title, etc.)
COMBO = dict(
    fg_color=CARD_BG,
    border_width=BORDER_W,
    border_color=BORDER,
    height=WIDGET_H,
    button_color=BORDER,
    button_hover_color=HOVER,
    dropdown_fg_color=PANEL_BG,
    dropdown_text_color=TEXT_PRIMARY,
    dropdown_hover_color=BORDER,
    corner_radius=6,
)

# OptionMenu (duration, OD count, etc.)
OPTION_MENU = dict(
    fg_color=CARD_BG,
    button_color=BORDER,
    button_hover_color=HOVER,
    text_color=TEXT_PRIMARY,
    dropdown_fg_color=PANEL_BG,
    dropdown_text_color=TEXT_PRIMARY,
    dropdown_hover_color=BORDER,
    corner_radius=6,
)

# OptionMenu when disabled (muted appearance)
OPTION_MENU_DISABLED = dict(
    fg_color=CARD_BG,
    button_color=PANEL_BG,
    button_hover_color=BORDER,
    text_color=TEXT_MUTED,
    dropdown_fg_color=PANEL_BG,
    dropdown_text_color=TEXT_PRIMARY,
    dropdown_hover_color=BORDER,
    corner_radius=6,
)

# Standard buttons
BTN_PRIMARY   = dict(fg_color=PRIMARY,   hover_color=PRIMARY_HOVER, corner_radius=6)
BTN_SECONDARY = dict(fg_color=BORDER,    hover_color=HOVER, corner_radius=6)
BTN_DANGER    = dict(fg_color=DANGER,    hover_color=DANGER_HOVER, corner_radius=6)
BTN_SUCCESS   = dict(fg_color=SUCCESS,   hover_color=SUCCESS_HOVER, corner_radius=6)

# Icon-only square button (secondary style)
BTN_ICON = dict(
    fg_color=BORDER,
    hover_color=HOVER,
    width=ICON_BTN_W,
    height=WIDGET_H_SM,
    corner_radius=6,
)

# Icon-only square button (danger style)
BTN_ICON_DANGER = dict(
    fg_color=DANGER,
    hover_color=DANGER_HOVER,
    width=ICON_BTN_W,
    height=WIDGET_H_SM,
    corner_radius=6,
)

# Card frame (slot cards, event cards, DJ cards)
CARD = dict(
    fg_color=CARD_BG,
    border_width=BORDER_W,
    border_color=BORDER,
    corner_radius=CARD_RADIUS,
)

# Panel / tabview frame
PANEL = dict(
    fg_color=PANEL_BG,
    border_width=BORDER_W,
    border_color=BORDER,
    corner_radius=PANEL_RADIUS,
)

# Scrollbar inside genre drawer
SCROLLBAR_STYLE = dict(
    orientation="vertical",
    button_color=BORDER,
    button_hover_color=HOVER,
    width=10,
)