"""
Module: date_time_picker.py
Purpose: DPG date/time input helper with a custom Sun-Sat Calendar popout.
"""
import calendar
from datetime import datetime

import dearpygui.dearpygui as dpg

from .fonts import Icon, bind_icon_font


def add_datetime_row(tag: str, var, parent: str = "", callback=None):
    """Add a DPG input_text for date/time + a button to open the picker."""
    grp_kwargs = {"horizontal": True}
    if parent:
        grp_kwargs["parent"] = parent

    with dpg.group(**grp_kwargs):
        dpg.add_input_text(
            tag=tag,
            default_value=var.get() if var is not None else "",
            width=-50,
            hint="YYYY-MM-DD HH:MM",
            callback=callback
        )
        if var is not None:
            var._tag = tag

        btn = dpg.add_button(label=Icon.SCHEDULE, width=32, height=20,
                             callback=lambda: open_datetime_picker(var, callback))
        bind_icon_font(btn)
        dpg.add_spacer(width=10)


def open_datetime_picker(var, callback=None):
    """Open a modal DPG window with a Sun-Sat calendar and time picker."""
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

    state = {
        "view_year": current_dt.year,
        "view_month": current_dt.month,
        "sel_year": current_dt.year,
        "sel_month": current_dt.month,
        "sel_day": current_dt.day,
        "hour": current_dt.hour,
        "minute": current_dt.minute
    }

    months = ["January", "February", "March", "April", "May", "June",
              "July", "August", "September", "October", "November", "December"]

    def _rebuild_calendar():
        if not dpg.does_item_exist("cal_grid_group"):
            return
        dpg.delete_item("cal_grid_group", children_only=True)

        header_text = f"{months[state['view_month']-1]} {state['view_year']}"
        dpg.set_value("cal_month_year_text", header_text.center(22))

        cal = calendar.Calendar(firstweekday=calendar.SUNDAY)
        month_days = cal.monthdatescalendar(state["view_year"], state["view_month"])

        with dpg.table(header_row=True, parent="cal_grid_group",
                       borders_innerH=False, borders_innerV=False):
            for day_name in ["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"]:
                dpg.add_table_column(label=day_name, width_fixed=True,
                                     init_width_or_weight=32)

            for week in month_days:
                with dpg.table_row():
                    for dt in week:
                        is_current_month = (dt.month == state["view_month"])
                        is_selected = (
                            dt.year == state["sel_year"]
                            and dt.month == state["sel_month"]
                            and dt.day == state["sel_day"]
                        )

                        btn = dpg.add_button(label=str(dt.day), width=32, height=20)

                        def _select_date(s, a, u):
                            state["sel_year"] = u.year
                            state["sel_month"] = u.month
                            state["sel_day"] = u.day
                            state["view_year"] = u.year
                            state["view_month"] = u.month
                            _rebuild_calendar()

                        dpg.set_item_callback(btn, _select_date)
                        dpg.set_item_user_data(btn, dt)

                        if is_selected:
                            dpg.bind_item_theme(btn, "primary_btn_theme")
                        elif not is_current_month:
                            dpg.bind_item_theme(btn, "cal_muted_theme")

    if not dpg.does_item_exist("cal_muted_theme"):
        with dpg.theme(tag="cal_muted_theme"):
            with dpg.theme_component(dpg.mvButton):
                dpg.add_theme_color(dpg.mvThemeCol_Button, (0, 0, 0, 0))
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (255, 255, 255, 20))
                dpg.add_theme_color(dpg.mvThemeCol_Text, (100, 100, 100, 255))

    with dpg.window(tag=win_tag, label="Select Date & Time", modal=True,
                    no_resize=True, autosize=True, no_scrollbar=True,
                    pos=dpg.get_mouse_pos(local=False)):

        # ── Calendar Navigation ──
        with dpg.group(horizontal=True):
            def _prev():
                state["view_month"] -= 1
                if state["view_month"] < 1:
                    state["view_month"] = 12
                    state["view_year"] -= 1
                _rebuild_calendar()

            def _next():
                state["view_month"] += 1
                if state["view_month"] > 12:
                    state["view_month"] = 1
                    state["view_year"] += 1
                _rebuild_calendar()

            dpg.add_button(label="<", width=25, callback=_prev)
            dpg.add_text("", tag="cal_month_year_text")
            dpg.add_button(label=">", width=25, callback=_next)

        dpg.add_separator()
        dpg.add_group(tag="cal_grid_group")
        dpg.add_separator()

        # ── Time Picker ──
        dpg.add_text("Time (HH : MM)")
        with dpg.group(horizontal=True):
            hour_tag = dpg.add_input_int(
                default_value=state["hour"], min_value=0, max_value=23,
                step=1, width=70)
            dpg.add_text(":")
            minute_tag = dpg.add_input_int(
                default_value=state["minute"], min_value=0, max_value=59,
                step=15, width=70)

        dpg.add_separator()

        # ── Actions ──
        def _confirm():
            state["hour"] = dpg.get_value(hour_tag)
            state["minute"] = dpg.get_value(minute_tag)
            dt_str = (
                f"{state['sel_year']}-{state['sel_month']:02d}-"
                f"{state['sel_day']:02d} "
                f"{state['hour']:02d}:{state['minute']:02d}"
            )

            if var is not None:
                var.set(dt_str)
                if hasattr(var, "_tag") and dpg.does_item_exist(var._tag):
                    dpg.set_value(var._tag, dt_str)

            if callback:
                callback(None, None, None)

            dpg.delete_item(win_tag)

        with dpg.group(horizontal=True):
            ok_btn = dpg.add_button(label="OK", width=128, callback=_confirm)
            dpg.bind_item_theme(ok_btn, "primary_btn_theme")

    _rebuild_calendar()
