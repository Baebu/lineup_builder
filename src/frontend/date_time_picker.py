"""
Module: date_time_picker.py
Purpose: DPG date/time input helper (replaces CTkDateTimePicker).
"""
from datetime import datetime

import dearpygui.dearpygui as dpg

from .fonts import Icon


def add_datetime_row(tag: str, var, parent: str = "", callback=None):
    """Add a DPG input_text for date/time in YYYY-MM-DD HH:MM format."""
    kwargs: dict = {
        "tag": tag,
        "default_value": var.get() if var is not None else "",
        "width": -1,
        "hint": "YYYY-MM-DD HH:MM",
    }
    if parent:
        kwargs["parent"] = parent
    if callback:
        kwargs["callback"] = callback
    dpg.add_input_text(**kwargs)
    if var is not None:
        var._tag = tag


def open_datetime_picker(var, callback=None):
    """Open a modal DPG window for picking a date and time.

    *var*      – DPGVar whose value is a 'YYYY-MM-DD HH:MM' string.
    *callback* – optional callable(datetime_str) invoked on confirm.
    """
    current_str = var.get() if var is not None else ""
    try:
        current_dt = datetime.strptime(current_str, "%Y-%m-%d %H:%M")
    except ValueError:
        try:
            current_dt = datetime.strptime(current_str, "%Y-%m-%d")
        except ValueError:
            current_dt = datetime.now()

    win_tag = "dt_picker_modal"
    if dpg.does_item_exist(win_tag):
        dpg.delete_item(win_tag)

    year_tag   = f"{win_tag}_year"
    month_tag  = f"{win_tag}_month"
    day_tag    = f"{win_tag}_day"
    hour_tag   = f"{win_tag}_hour"
    minute_tag = f"{win_tag}_minute"

    months = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December",
    ]

    with dpg.window(tag=win_tag, label="Select Date & Time",
                    modal=True, no_resize=True, width=320, height=260,
                    pos=(200, 150)):

        with dpg.group(horizontal=True):
            dpg.add_combo(tag=year_tag,
                          items=[str(y) for y in range(2020, 2040)],
                          default_value=str(current_dt.year),
                          width=80)
            dpg.add_combo(tag=month_tag,
                          items=months,
                          default_value=months[current_dt.month - 1],
                          width=110)
            dpg.add_input_int(tag=day_tag,
                              default_value=current_dt.day,
                              min_value=1, max_value=31,
                              step=0, width=60)

        dpg.add_separator()
        dpg.add_text("Time (HH : MM)")
        with dpg.group(horizontal=True):
            dpg.add_input_int(tag=hour_tag,
                              default_value=current_dt.hour,
                              min_value=0, max_value=23,
                              step=0, width=70)
            dpg.add_text(":")
            dpg.add_input_int(tag=minute_tag,
                              default_value=current_dt.minute,
                              min_value=0, max_value=59,
                              step=0, width=70)

        dpg.add_separator()

        def _confirm(_s, _a, _u):
            m_str = dpg.get_value(month_tag)
            month_num = months.index(m_str) + 1
            dt_str = (
                f"{dpg.get_value(year_tag)}-{month_num:02d}-"
                f"{dpg.get_value(day_tag):02d} "
                f"{dpg.get_value(hour_tag):02d}:{dpg.get_value(minute_tag):02d}"
            )
            if var is not None:
                var.set(dt_str)
                if hasattr(var, "_tag") and dpg.does_item_exist(var._tag):
                    dpg.set_value(var._tag, dt_str)
            if callback:
                callback(dt_str)
            dpg.delete_item(win_tag)

        def _cancel(_s, _a, _u):
            dpg.delete_item(win_tag)

        with dpg.group(horizontal=True):
            dpg.add_button(label=Icon.CHECK + " OK", width=120, callback=_confirm)
            dpg.add_button(label=Icon.CLOSE + " Cancel", width=120, callback=_cancel)
