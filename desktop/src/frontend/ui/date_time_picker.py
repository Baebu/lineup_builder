"""
Module: date_time_picker.py
Purpose: DPG date/time input helper with a custom Sun-Sat Calendar popout.
         Supports full date+time, date-only, and time-only picker modes.
"""
import calendar
from datetime import datetime, timedelta

import dearpygui.dearpygui as dpg

from .widgets import popup_pos


# ── Full date+time picker (existing) ─────────────────────────────────────


def add_datetime_row(tag: str, var, parent: str = "", callback=None):
    """Add a DPG input_text for date/time that opens the picker on click."""
    grp_kwargs = {"horizontal": True}
    if parent:
        grp_kwargs["parent"] = parent

    with dpg.group(**grp_kwargs):
        dpg.add_input_text(
            tag=tag,
            default_value=var.get() if var is not None else "",
            width=-1,
            hint="YYYY-MM-DD HH:MM",
            callback=callback,
            readonly=True,
        )
        if var is not None:
            var._tag = tag

        # Click handler on the text box opens the picker
        _hr_tag = f"{tag}_click_hr"
        with dpg.item_handler_registry(tag=_hr_tag):
            dpg.add_item_clicked_handler(
                callback=lambda s, a, u=None: open_datetime_picker(var, callback)
            )
        dpg.bind_item_handler_registry(tag, _hr_tag)


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
    if dpg.does_item_exist("dt_picker_key_hr"):
        dpg.delete_item("dt_picker_key_hr")
    if dpg.does_item_exist("dt_picker_wheel_hr"):
        dpg.delete_item("dt_picker_wheel_hr")

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
                    pos=popup_pos(width=280, height=340)):

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

        # Scroll-wheel on hour/minute fields
        _hour_hovered = {"v": False}
        _min_hovered = {"v": False}

        def _hour_hover(sender, app_data):
            _hour_hovered["v"] = (app_data == 1)

        def _min_hover(sender, app_data):
            _min_hovered["v"] = (app_data == 1)

        _hh_hr = "dt_hour_hover_hr"
        _mm_hr = "dt_min_hover_hr"
        for t in (_hh_hr, _mm_hr):
            if dpg.does_item_exist(t):
                dpg.delete_item(t)

        with dpg.item_handler_registry(tag=_hh_hr):
            dpg.add_item_hover_handler(callback=_hour_hover)
        dpg.bind_item_handler_registry(hour_tag, _hh_hr)

        with dpg.item_handler_registry(tag=_mm_hr):
            dpg.add_item_hover_handler(callback=_min_hover)
        dpg.bind_item_handler_registry(minute_tag, _mm_hr)

        def _on_wheel(sender, app_data):
            delta = int(app_data)  # positive = scroll up, negative = scroll down
            if _hour_hovered["v"]:
                h = (dpg.get_value(hour_tag) + delta) % 24
                dpg.set_value(hour_tag, h)
                state["hour"] = h
            elif _min_hovered["v"]:
                m = dpg.get_value(minute_tag) + delta * 15
                h = dpg.get_value(hour_tag)
                if m > 59:
                    m = 0
                    h = (h + 1) % 24
                elif m < 0:
                    m = 45
                    h = (h - 1) % 24
                dpg.set_value(minute_tag, m)
                dpg.set_value(hour_tag, h)
                state["minute"] = m
                state["hour"] = h

        _wheel_hr = "dt_picker_wheel_hr"
        if dpg.does_item_exist(_wheel_hr):
            dpg.delete_item(_wheel_hr)
        with dpg.handler_registry(tag=_wheel_hr):
            dpg.add_mouse_wheel_handler(callback=_on_wheel)

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

            if dpg.does_item_exist("dt_picker_key_hr"):
                dpg.delete_item("dt_picker_key_hr")
            if dpg.does_item_exist("dt_picker_wheel_hr"):
                dpg.delete_item("dt_picker_wheel_hr")
            dpg.delete_item(win_tag)

        with dpg.group(horizontal=True):
            ok_btn = dpg.add_button(label="OK", width=128, callback=_confirm)
            dpg.bind_item_theme(ok_btn, "primary_btn_theme")

        # ── Arrow-key handlers ──
        def _on_key(sender, app_data):
            key = app_data
            if key == dpg.mvKey_Up:
                # Increment minute by 15
                m = dpg.get_value(minute_tag) + 15
                h = dpg.get_value(hour_tag)
                if m > 59:
                    m = 0
                    h = (h + 1) % 24
                dpg.set_value(minute_tag, m)
                dpg.set_value(hour_tag, h)
                state["minute"] = m
                state["hour"] = h
            elif key == dpg.mvKey_Down:
                # Decrement minute by 15
                m = dpg.get_value(minute_tag) - 15
                h = dpg.get_value(hour_tag)
                if m < 0:
                    m = 45
                    h = (h - 1) % 24
                dpg.set_value(minute_tag, m)
                dpg.set_value(hour_tag, h)
                state["minute"] = m
                state["hour"] = h
            elif key in (dpg.mvKey_Left, dpg.mvKey_Right):
                # Navigate date by +/- 1 day
                delta = 1 if key == dpg.mvKey_Right else -1
                cur = datetime(state["sel_year"], state["sel_month"], state["sel_day"])
                nxt = cur + timedelta(days=delta)
                state["sel_year"] = nxt.year
                state["sel_month"] = nxt.month
                state["sel_day"] = nxt.day
                state["view_year"] = nxt.year
                state["view_month"] = nxt.month
                _rebuild_calendar()

        _key_hr = "dt_picker_key_hr"
        if dpg.does_item_exist(_key_hr):
            dpg.delete_item(_key_hr)
        with dpg.handler_registry(tag=_key_hr):
            dpg.add_key_press_handler(callback=_on_key)

    _rebuild_calendar()


# ── Date-only picker ─────────────────────────────────────────────────────


def add_date_row(tag: str, default: str = "", parent: str = "", callback=None,
                 width: int = -1):
    """Add a readonly input_text that opens a date-only picker on click."""
    grp_kwargs = {"horizontal": True}
    if parent:
        grp_kwargs["parent"] = parent

    with dpg.group(**grp_kwargs):
        dpg.add_input_text(
            tag=tag,
            default_value=default,
            width=width,
            hint="YYYY-MM-DD",
            readonly=True,
        )
        _hr_tag = f"{tag}_click_hr"
        if dpg.does_item_exist(_hr_tag):
            dpg.delete_item(_hr_tag)
        with dpg.item_handler_registry(tag=_hr_tag):
            dpg.add_item_clicked_handler(
                callback=lambda s, a, u=None: open_date_picker(tag, callback)
            )
        dpg.bind_item_handler_registry(tag, _hr_tag)


def open_date_picker(input_tag: str, callback=None):
    """Open a modal date-only calendar picker. Writes YYYY-MM-DD to *input_tag*."""
    current_str = dpg.get_value(input_tag) if dpg.does_item_exist(input_tag) else ""
    try:
        current_dt = datetime.strptime(current_str, "%Y-%m-%d")
    except ValueError:
        current_dt = datetime.now()

    win_tag = "date_picker_modal"
    if dpg.does_item_exist(win_tag):
        dpg.delete_item(win_tag)

    state = {
        "view_year": current_dt.year,
        "view_month": current_dt.month,
        "sel_year": current_dt.year,
        "sel_month": current_dt.month,
        "sel_day": current_dt.day,
    }
    months = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December",
    ]

    def _rebuild():
        if not dpg.does_item_exist("dpk_cal_grid"):
            return
        dpg.delete_item("dpk_cal_grid", children_only=True)
        header = f"{months[state['view_month']-1]} {state['view_year']}"
        dpg.set_value("dpk_month_year", header.center(22))
        cal = calendar.Calendar(firstweekday=calendar.SUNDAY)
        weeks = cal.monthdatescalendar(state["view_year"], state["view_month"])
        with dpg.table(header_row=True, parent="dpk_cal_grid",
                       borders_innerH=False, borders_innerV=False):
            for d in ["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"]:
                dpg.add_table_column(label=d, width_fixed=True, init_width_or_weight=32)
            for week in weeks:
                with dpg.table_row():
                    for dt in week:
                        is_cur = dt.month == state["view_month"]
                        is_sel = (dt.year == state["sel_year"]
                                  and dt.month == state["sel_month"]
                                  and dt.day == state["sel_day"])
                        btn = dpg.add_button(label=str(dt.day), width=32, height=20)

                        def _sel(s, a, u):
                            state["sel_year"] = u.year
                            state["sel_month"] = u.month
                            state["sel_day"] = u.day
                            state["view_year"] = u.year
                            state["view_month"] = u.month
                            _rebuild()

                        dpg.set_item_callback(btn, _sel)
                        dpg.set_item_user_data(btn, dt)
                        if is_sel:
                            dpg.bind_item_theme(btn, "primary_btn_theme")
                        elif not is_cur:
                            if not dpg.does_item_exist("cal_muted_theme"):
                                with dpg.theme(tag="cal_muted_theme"):
                                    with dpg.theme_component(dpg.mvButton):
                                        dpg.add_theme_color(dpg.mvThemeCol_Button, (0, 0, 0, 0))
                                        dpg.add_theme_color(
                                            dpg.mvThemeCol_ButtonHovered, (255, 255, 255, 20))
                                        dpg.add_theme_color(
                                            dpg.mvThemeCol_Text, (100, 100, 100, 255))
                            dpg.bind_item_theme(btn, "cal_muted_theme")

    with dpg.window(tag=win_tag, label="Select Date", modal=True,
                    no_resize=True, autosize=True, no_scrollbar=True,
                    pos=popup_pos(width=280, height=280)):
        with dpg.group(horizontal=True):
            def _prev():
                state["view_month"] -= 1
                if state["view_month"] < 1:
                    state["view_month"] = 12
                    state["view_year"] -= 1
                _rebuild()

            def _next():
                state["view_month"] += 1
                if state["view_month"] > 12:
                    state["view_month"] = 1
                    state["view_year"] += 1
                _rebuild()

            dpg.add_button(label="<", width=25, callback=_prev)
            dpg.add_text("", tag="dpk_month_year")
            dpg.add_button(label=">", width=25, callback=_next)

        dpg.add_separator()
        dpg.add_group(tag="dpk_cal_grid")
        dpg.add_separator()

        def _confirm():
            dt_str = (f"{state['sel_year']}-{state['sel_month']:02d}-"
                      f"{state['sel_day']:02d}")
            if dpg.does_item_exist(input_tag):
                dpg.set_value(input_tag, dt_str)
            if callback:
                callback(dt_str)
            dpg.delete_item(win_tag)

        with dpg.group(horizontal=True):
            ok = dpg.add_button(label="OK", width=128, callback=_confirm)
            dpg.bind_item_theme(ok, "primary_btn_theme")

    _rebuild()


# ── Time-only picker ─────────────────────────────────────────────────────


def add_time_row(tag: str, default: str = "", parent: str = "", callback=None,
                 width: int = -1):
    """Add a readonly input_text that opens a time-only picker on click."""
    grp_kwargs = {"horizontal": True}
    if parent:
        grp_kwargs["parent"] = parent

    with dpg.group(**grp_kwargs):
        dpg.add_input_text(
            tag=tag,
            default_value=default,
            width=width,
            hint="H:MM AM/PM",
            readonly=True,
        )
        _hr_tag = f"{tag}_click_hr"
        if dpg.does_item_exist(_hr_tag):
            dpg.delete_item(_hr_tag)
        with dpg.item_handler_registry(tag=_hr_tag):
            dpg.add_item_clicked_handler(
                callback=lambda s, a, u=None: open_time_picker(tag, callback)
            )
        dpg.bind_item_handler_registry(tag, _hr_tag)


def _parse_12h(val: str) -> tuple[int, int]:
    """Parse '8:00 PM' or '12:30 AM' into (hour_24, minute)."""
    val = val.strip().upper()
    try:
        dt = datetime.strptime(val, "%I:%M %p")
        return dt.hour, dt.minute
    except ValueError:
        return 20, 0  # fallback 8 PM


def _format_12h(h: int, m: int) -> str:
    """Format 24h (hour, minute) as '8:00 PM'."""
    period = "AM" if h < 12 else "PM"
    display_h = h % 12 or 12
    return f"{display_h}:{m:02d} {period}"


def open_time_picker(input_tag: str, callback=None):
    """Open a modal time-only picker. Writes 'H:MM AM/PM' to *input_tag*."""
    current_str = dpg.get_value(input_tag) if dpg.does_item_exist(input_tag) else ""
    h, m = _parse_12h(current_str) if current_str else (20, 0)

    win_tag = "time_picker_modal"
    for old in (win_tag, "tp_wheel_hr"):
        if dpg.does_item_exist(old):
            dpg.delete_item(old)

    state = {"hour": h, "minute": m}

    with dpg.window(tag=win_tag, label="Select Time", modal=True,
                    no_resize=True, autosize=True, no_scrollbar=True,
                    pos=popup_pos(width=200, height=150)):

        dpg.add_text("Time")
        with dpg.group(horizontal=True):
            hour_tag = dpg.add_input_int(
                default_value=h, min_value=0, max_value=23,
                step=1, width=70)
            dpg.add_text(":")
            minute_tag = dpg.add_input_int(
                default_value=m, min_value=0, max_value=59,
                step=15, width=70)

        # Live preview label
        dpg.add_text(_format_12h(h, m), tag="tp_preview")

        def _update_preview():
            hv = dpg.get_value(hour_tag)
            mv = dpg.get_value(minute_tag)
            dpg.set_value("tp_preview", _format_12h(hv, mv))

        # Scroll-wheel support
        _hh = {"v": False}
        _mm = {"v": False}

        def _hh_hover(s, a):
            _hh["v"] = (a == 1)

        def _mm_hover(s, a):
            _mm["v"] = (a == 1)

        for t in ("tp_hh_hr", "tp_mm_hr"):
            if dpg.does_item_exist(t):
                dpg.delete_item(t)
        with dpg.item_handler_registry(tag="tp_hh_hr"):
            dpg.add_item_hover_handler(callback=_hh_hover)
        dpg.bind_item_handler_registry(hour_tag, "tp_hh_hr")
        with dpg.item_handler_registry(tag="tp_mm_hr"):
            dpg.add_item_hover_handler(callback=_mm_hover)
        dpg.bind_item_handler_registry(minute_tag, "tp_mm_hr")

        def _on_wheel(sender, app_data):
            delta = int(app_data)
            if _hh["v"]:
                hv = (dpg.get_value(hour_tag) + delta) % 24
                dpg.set_value(hour_tag, hv)
            elif _mm["v"]:
                mv = dpg.get_value(minute_tag) + delta * 15
                hv = dpg.get_value(hour_tag)
                if mv > 59:
                    mv = 0
                    hv = (hv + 1) % 24
                elif mv < 0:
                    mv = 45
                    hv = (hv - 1) % 24
                dpg.set_value(minute_tag, mv)
                dpg.set_value(hour_tag, hv)
            _update_preview()

        with dpg.handler_registry(tag="tp_wheel_hr"):
            dpg.add_mouse_wheel_handler(callback=_on_wheel)

        dpg.add_separator()

        def _confirm():
            hv = dpg.get_value(hour_tag)
            mv = dpg.get_value(minute_tag)
            result = _format_12h(hv, mv)
            if dpg.does_item_exist(input_tag):
                dpg.set_value(input_tag, result)
            if callback:
                callback(result)
            for old in ("tp_wheel_hr", "tp_hh_hr", "tp_mm_hr"):
                if dpg.does_item_exist(old):
                    dpg.delete_item(old)
            dpg.delete_item(win_tag)

        with dpg.group(horizontal=True):
            ok = dpg.add_button(label="OK", width=128, callback=_confirm)
            dpg.bind_item_theme(ok, "primary_btn_theme")
