"""
Module: toast.py
Purpose: Non-blocking toast notification overlay for DearPyGui.

Creates a small floating window at the bottom-right of the viewport that
auto-dismisses after a configurable duration.  Supports success, error,
info, and warning severity levels with distinct styling.
"""

import time
import dearpygui.dearpygui as dpg

from ..styling import theme as T

# ── Severity presets ──────────────────────────────────────────────────────────
_SEVERITY = {
    "success": {"bg": (11, 110, 79, 230), "border": (52, 211, 153, 255), "icon": "\u2713"},
    "error":   {"bg": (127, 29, 29, 230),  "border": (239, 68, 68, 255),  "icon": "\u2717"},
    "info":    {"bg": (30, 41, 59, 230),   "border": (129, 140, 248, 255),"icon": "\u25cf"},
    "warning": {"bg": (120, 83, 9, 230),   "border": (251, 191, 36, 255), "icon": "\u26a0"},
}

# Track active toasts for stacking
_active_toasts: list[dict] = []
_toast_counter = 0

_TOAST_WIDTH = 300
_TOAST_HEIGHT = 50
_TOAST_MARGIN = 12
_TOAST_GAP = 6


def _build_toast_theme(severity: str):
    """Create or return a cached DPG theme for the given severity."""
    tag = f"_toast_theme_{severity}"
    if dpg.does_item_exist(tag):
        return tag
    preset = _SEVERITY.get(severity, _SEVERITY["info"])
    with dpg.theme(tag=tag):
        with dpg.theme_component(dpg.mvAll):
            dpg.add_theme_color(dpg.mvThemeCol_WindowBg, preset["bg"])
            dpg.add_theme_color(dpg.mvThemeCol_Border, preset["border"])
            dpg.add_theme_style(dpg.mvStyleVar_WindowBorderSize, 1)
            dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 8)
            dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, 10, 8)
    return tag


def _reposition_toasts():
    """Stack active toasts from bottom-right of viewport."""
    vp_w = dpg.get_viewport_width()
    vp_h = dpg.get_viewport_height()
    y_offset = _TOAST_MARGIN
    for toast in reversed(_active_toasts):
        tag = toast["tag"]
        if dpg.does_item_exist(tag):
            x = vp_w - _TOAST_WIDTH - _TOAST_MARGIN - 16
            y = vp_h - _TOAST_HEIGHT - y_offset - 40
            dpg.configure_item(tag, pos=[x, y])
            y_offset += _TOAST_HEIGHT + _TOAST_GAP


def _dismiss_toast(tag: str):
    """Remove a toast by tag."""
    global _active_toasts
    _active_toasts = [t for t in _active_toasts if t["tag"] != tag]
    if dpg.does_item_exist(tag):
        dpg.delete_item(tag)
    _reposition_toasts()


def tick_toasts():
    """Call once per frame (from App.process_queue / render loop) to auto-dismiss expired toasts."""
    now = time.time()
    expired = [t for t in _active_toasts if t["duration"] > 0 and now - t["time"] >= t["duration"]]
    for t in expired:
        _dismiss_toast(t["tag"])


def show_toast(message: str, severity: str = "info", duration: float = 3.0):
    """Show a toast notification.

    Args:
        message:  Text to display.
        severity: One of 'success', 'error', 'info', 'warning'.
        duration: Seconds before auto-dismiss (0 = sticky).
    """
    global _toast_counter
    _toast_counter += 1
    tag = f"_toast_win_{_toast_counter}"
    theme_tag = _build_toast_theme(severity)
    preset = _SEVERITY.get(severity, _SEVERITY["info"])

    # Cap active toasts at 5
    while len(_active_toasts) >= 5:
        oldest = _active_toasts.pop(0)
        if dpg.does_item_exist(oldest["tag"]):
            dpg.delete_item(oldest["tag"])

    vp_w = dpg.get_viewport_width()
    vp_h = dpg.get_viewport_height()

    with dpg.window(
        tag=tag,
        label="",
        no_title_bar=True,
        no_resize=True,
        no_move=True,
        no_collapse=True,
        no_scrollbar=True,
        no_focus_on_appearing=True,
        width=_TOAST_WIDTH,
        height=_TOAST_HEIGHT,
        pos=[vp_w - _TOAST_WIDTH - _TOAST_MARGIN - 16,
             vp_h - _TOAST_HEIGHT - _TOAST_MARGIN - 40],
    ):
        with dpg.group(horizontal=True):
            dpg.add_text(preset["icon"])
            dpg.add_spacer(width=4)
            # Truncate long messages
            display = message if len(message) <= 40 else message[:37] + "..."
            dpg.add_text(display, wrap=_TOAST_WIDTH - 60)

    dpg.bind_item_theme(tag, theme_tag)

    toast_entry = {"tag": tag, "time": time.time(), "duration": duration}
    _active_toasts.append(toast_entry)
    _reposition_toasts()
