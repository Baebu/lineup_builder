"""
Module: ui_builder.py
Purpose: Builds the entire application UI layout (Dear PyGui).
Architecture: Mixin for App class.
"""
from datetime import datetime, timedelta

import dearpygui.dearpygui as dpg

from . import theme as T
from .date_time_picker import add_datetime_row
from .fonts import styled_text, bind_icon_font, Icon, HEADER, LABEL, BODY, MUTED, HINT
from .widgets import add_icon_button, add_primary_button



class UISetupMixin:
    """Builds the entire application UI and provides helpers."""

    _LEFT_MIN = 300
    _LEFT_MAX = 350
    _LEFT_DEFAULT = 325

    def setup_ui(self):
        with dpg.window(tag="primary_window", no_title_bar=True, no_resize=True,
                        no_move=True, no_scrollbar=True,
                        no_scroll_with_mouse=True):
            with dpg.table(header_row=False, resizable=False,
                           scrollX=False, scrollY=False,
                           policy=dpg.mvTable_SizingFixedFit):
                dpg.add_table_column(init_width_or_weight=self._LEFT_DEFAULT,
                                     width_fixed=True)
                dpg.add_table_column(init_width_or_weight=1, width_fixed=True)
                dpg.add_table_column(width_stretch=True)
                with dpg.table_row():
                    with dpg.child_window(tag="left_panel", border=False,
                                          no_scrollbar=True):
                        self._build_left_panel()
                    with dpg.child_window(tag="panel_divider", border=False,
                                          no_scrollbar=True, width=1):
                        with dpg.theme() as _div_theme:
                            with dpg.theme_component(dpg.mvChildWindow):
                                dpg.add_theme_color(dpg.mvThemeCol_ChildBg, T.DPG_BORDER)
                        dpg.bind_item_theme("panel_divider", _div_theme)
                    with dpg.child_window(tag="right_panel", border=False,
                                          no_scrollbar=True):
                        self._build_right_panel()

        dpg.set_primary_window("primary_window", True)
        self._build_settings_tab()
        self.apply_theme()
        self._setup_wheel_handler()

    # ── Left panel ────────────────────────────────────────────────────────

    def _build_left_panel(self):
        with dpg.tab_bar(tag="left_tabs"):
            with dpg.tab(label="Event", tag="Event"):
                self._build_event_tab()
            with dpg.tab(label="Roster", tag="Roster"):
                self._build_dj_roster_tab()
            with dpg.tab(label="Settings", tag="Settings"):
                with dpg.child_window(tag="settings_scroll", height=-1,
                                      border=False, autosize_x=True):
                    pass  # populated by _build_settings_tab()

    def _build_event_tab(self):
        with dpg.child_window(tag="event_tab_inner", border=False,
                              autosize_x=True, height=-1):
            # ── Header row ────────────────────────────────────────────────────
            styled_text("   EVENT CONFIGURATION", HEADER)
            with dpg.table(header_row=False, borders_innerH=False, borders_innerV=True,
                           borders_outerH=False, borders_outerV=False, pad_outerX=False):
                dpg.add_table_column()
                dpg.add_table_column()
                with dpg.table_row():
                    dpg.add_button(label="+ New", width=-1,
                                   callback=lambda: self.new_event())
                    add_primary_button("Save", width=-1, callback=lambda: self.save_event_lineup())
            dpg.add_separator()

            # ── Social links shortcut ────────────────────────────────────
            dpg.add_button(
                label="Social Links",
                tag="social_links_btn",
                width=-1,
                callback=lambda: self._open_social_links_popup(),
            )
            dpg.add_separator()

            # ── Event title + vol ─────────────────────────────────────────────
            styled_text("   EVENT TITLE", LABEL)
            with dpg.group(horizontal=True):
                dpg.add_input_text(
                    tag="event_title_input",
                    default_value=self.event_title_var.get(),
                    hint="Event title...", width=-50,
                    callback=lambda s, a, u=None: self._schedule_update(),
                )
                dpg.add_input_text(
                    tag="event_vol_input",
                    default_value=self.event_vol_var.get(),
                    hint="Vol",
                    width=38,
                    callback=lambda s, a, u=None: self._schedule_update(),
                )
                with dpg.theme() as _pill_theme:
                    with dpg.theme_component(dpg.mvInputText):
                        dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 999)
                dpg.bind_item_theme("event_vol_input", _pill_theme)
            self.event_title_var._tag = "event_title_input"
            self.event_vol_var._tag   = "event_vol_input"
            self._register_scroll_int("event_vol_input", min_val=1,
                                      on_change=lambda: self._schedule_update())

            # ── Timestamp ─────────────────────────────────────────────────────
            styled_text("   START", LABEL)
            add_datetime_row(
                "event_timestamp_input", self.event_timestamp,
                callback=lambda s, a, u=None: self._schedule_update(),
            )

            # ── Genres ────────────────────────────────────────────────────────
            styled_text("   GENRES", LABEL)
            with dpg.group(horizontal=True):
                dpg.add_input_text(
                    tag="genre_entry",
                    default_value=self.genre_entry_var.get(),
                    hint="Search or press Enter to add...", width=-50,
                    on_enter=True,
                    callback=lambda s, a, u=None: self.add_genre_from_entry(),
                    user_data=None,
                )
                add_icon_button(Icon.EDIT, callback=lambda: self.open_genre_editor())
                dpg.add_spacer(width=10)
            self.genre_entry_var._tag = "genre_entry"
            self.genre_search_var._tag = "genre_entry"
            with dpg.item_handler_registry(tag="genre_entry_hr"):
                dpg.add_item_edited_handler(
                    callback=lambda s, a, u=None: self._schedule_genre_refresh()
                )
            dpg.add_separator()
            dpg.bind_item_handler_registry("genre_entry", "genre_entry_hr")
            with dpg.child_window(tag="genre_tags_frame", height=90,
                                  border=False, autosize_x=True):
                pass  # populated by refresh_genre_tags()
            dpg.add_separator()

            # ── Saved Events ──────────────────────────────────────────────────
            styled_text("   SAVED EVENTS", HEADER)
            with dpg.child_window(tag="saved_events_scroll", height=-1,
                                  border=False, autosize_x=True):
                pass  # populated by refresh_saved_events_ui()

        self.refresh_genre_tags()
        self.refresh_saved_events_ui()

    def _build_dj_roster_tab(self):
        with dpg.group(horizontal=True):
            styled_text("   DJS", HEADER)
        add_primary_button("+ New DJ", width=-1, callback=lambda: self.add_new_dj_to_roster())
        dpg.add_input_text(
            tag="dj_search_input",
            default_value=self.dj_search_var.get(),
            hint="Search...", width=-11,
            callback=lambda s, a, u=None: self._schedule_roster_refresh(),
        )
        self.dj_search_var._tag = "dj_search_input"
        with dpg.child_window(tag="dj_roster_scroll", height=-1,
                              border=False, autosize_x=True):
            pass  # populated by refresh_dj_roster_ui()
        self.refresh_dj_roster_ui()

    # ── Social links popup ──────────────────────────────────────────

    _SOCIAL_FIELDS = [
        ("TIMELINE",   "https://vrc.tl/event/"),
        ("VRCPOP",     "https://vrcpop.com/event/"),
        ("X",          "https://x.com/"),
        ("IG",         "https://www.instagram.com/p/"),
        ("DISCORD",    "https://discord.gg/"),
        ("VRC GROUP",  "https://vrc.group/"),
    ]

    def _open_social_links_popup(self):
        win_tag = "social_links_win"
        if dpg.does_item_exist(win_tag):
            dpg.focus_item(win_tag)
            return

        links = getattr(self, "social_links", {})
        persistent = getattr(self, "persistent_links", {})
        _PERSISTENT_KEYS = {"DISCORD", "VRC GROUP"}

        with dpg.window(
            tag=win_tag, label="Social Links", modal=True,
            no_resize=True, no_scrollbar=True, autosize=True,
        ):
            styled_text("  Links included in the Discord output below the genres.",
                        MUTED, wrap=340)
            dpg.add_spacer(height=4)

            input_tags = {}
            checkbox_tags = {}
            for label, hint in self._SOCIAL_FIELDS:
                styled_text(f"  {label}", LABEL)
                tag = f"social_input_{label.replace(' ', '_')}"
                # Pre-fill: use persistent link when enabled, otherwise event-specific
                p = persistent.get(label, {})
                default_val = (p.get("link", "") if p.get("enabled") else "") or links.get(label, "")
                dpg.add_input_text(
                    tag=tag,
                    default_value=default_val,
                    hint=hint,
                    width=340,
                )
                input_tags[label] = tag
                if label in _PERSISTENT_KEYS:
                    cb_tag = f"social_persist_{label.replace(' ', '_')}"
                    dpg.add_checkbox(
                        tag=cb_tag,
                        label="Use for all events",
                        default_value=bool(p.get("enabled", False)),
                    )
                    checkbox_tags[label] = cb_tag

            dpg.add_spacer(height=6)

            def _save_and_close():
                self.social_links = {
                    label: dpg.get_value(input_tags[label]).strip()
                    for label in input_tags
                }
                for key, cb_tag in checkbox_tags.items():
                    self.persistent_links[key] = {
                        "link": dpg.get_value(input_tags[key]).strip(),
                        "enabled": dpg.get_value(cb_tag),
                    }
                self.save_settings()
                self._schedule_update()
                if dpg.does_item_exist(win_tag):
                    dpg.delete_item(win_tag)

            def _clear_all():
                for t in input_tags.values():
                    dpg.set_value(t, "")

            with dpg.group(horizontal=True):
                _apply_btn = dpg.add_button(
                    label="Apply", width=160, callback=lambda: _save_and_close()
                )
                dpg.bind_item_theme(_apply_btn, "primary_btn_theme")
                dpg.add_button(
                    label="Clear All", width=80,
                    callback=lambda: _clear_all(),
                )
                dpg.add_button(
                    label="Cancel", width=80,
                    callback=lambda: dpg.delete_item(win_tag),
                )

    # ── Right panel ───────────────────────────────────────────────────────

    def _build_right_panel(self):
        # ── Lineup header ─────────────────────────────────────────────────
        with dpg.tab_bar():
            with dpg.tab(label="Lineup"):
                # ── Row 1: default length + add DJ ────────────────────
                with dpg.group(horizontal=True):
                    dur_values = [str(x) for x in range(15, 121, 15)]
                    styled_text("   CONTROLS  ", HEADER)
                    dpg.add_combo(
                        tag="master_dur_combo",
                        items=dur_values,
                        default_value=self.master_duration.get(),
                        width=50,
                        callback=lambda s, a, u=None: self.apply_master_duration(),
                    )
                    self.master_duration._tag = "master_dur_combo"
                    self._register_scroll_combo("master_dur_combo", dur_values,
                                                on_change=lambda: self.apply_master_duration())
                    add_primary_button("+ Add DJ", width=90, callback=lambda: self.add_slot())
                    dpg.add_spacer(width=10)

                # ── Slots scroll area ─────────────────────────────────────
                with dpg.child_window(tag="slots_scroll", height=320,
                                      border=True, autosize_x=True,
                                      payload_type="DJ_CARD",
                                      drop_callback=lambda s, a, u=None: self._drop_dj_on_lineup(s, a)):
                    pass  # populated by slot_manager

                # ── Draggable resize handle ───────────────────────────────
                dpg.add_button(tag="resize_handle", label="", width=-1, height=4)
                with dpg.theme() as _rh_theme:
                    with dpg.theme_component(dpg.mvButton):
                        dpg.add_theme_color(dpg.mvThemeCol_Button,       T.DPG_BORDER)
                        dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, T.DPG_ACCENT)
                        dpg.add_theme_color(dpg.mvThemeCol_ButtonActive,  T.DPG_ACCENT)
                        dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 0)
                        dpg.add_theme_style(dpg.mvStyleVar_FramePadding,  0, 0)
                dpg.bind_item_theme("resize_handle", _rh_theme)
                with dpg.item_handler_registry(tag="resize_handle_hr"):
                    dpg.add_item_clicked_handler(button=dpg.mvMouseButton_Left,
                                                 callback=self._resize_handle_click)
                dpg.bind_item_handler_registry("resize_handle", "resize_handle_hr")
                with dpg.handler_registry(tag="resize_global_hr"):
                    dpg.add_mouse_drag_handler(button=dpg.mvMouseButton_Left,
                                               callback=self._resize_handle_drag)
                    dpg.add_mouse_release_handler(button=dpg.mvMouseButton_Left,
                                                  callback=self._resize_handle_release)

                # ── Output preview ────────────────────────────────────────
                styled_text("   OUTPUT", HEADER)
                with dpg.table(header_row=False, borders_innerH=False, borders_innerV=True,
                               borders_outerH=False, borders_outerV=False, pad_outerX=False):
                    for _ in range(6):
                        dpg.add_table_column()
                    with dpg.table_row():
                        dpg.add_button(tag="fmt_discord", label="Discord", width=-1,
                                       callback=lambda: self.toggle_format())
                        dpg.add_button(tag="fmt_plain",   label="Plain",   width=-1,
                                       callback=lambda: self.set_plain_text())
                        dpg.add_button(tag="fmt_quest",   label="Quest",   width=-1,
                                       callback=lambda: self.set_quest_view())
                        dpg.add_button(tag="fmt_pc",      label="PC",      width=-1,
                                       callback=lambda: self.set_pc_view())
                        dpg.add_button(tag="fmt_times",   label="Times on", width=-1,
                                       callback=lambda: self._toggle_times())
                        add_icon_button(Icon.COPY, width=-1, height=20, is_primary=True, callback=lambda: self._copy_output())

                dpg.add_input_text(
                    tag="output_text",
                    multiline=True, readonly=True,
                    width=-11, height=-1,
                )

    # ── Helpers ───────────────────────────────────────────────────────────

    def _toggle_times(self):
        self.names_only.set(not self.names_only.get())
        self.update_output()

    def _copy_output(self):
        """Copy the output text to the system clipboard."""
        if dpg.does_item_exist("output_text"):
            text = dpg.get_value("output_text")
            if text:
                dpg.set_clipboard_text(text)

    # ── Scroll-wheel helpers ─────────────────────────────────────────
    # One global handler checks is_item_hovered for every registered item.

    def _shift_timestamp(self, delta_mins: int):
        """Shift the event timestamp by *delta_mins* minutes."""
        raw = self.event_timestamp.get()
        try:
            dt = datetime.strptime(raw, "%Y-%m-%d %H:%M")
        except ValueError:
            return
        dt += timedelta(minutes=delta_mins)
        new_str = dt.strftime("%Y-%m-%d %H:%M")
        self.event_timestamp.set(new_str)
        if dpg.does_item_exist("event_timestamp_input"):
            dpg.set_value("event_timestamp_input", new_str)
        self._schedule_update()

    def _setup_wheel_handler(self):
        if not hasattr(self, '_scroll_combos'):
            self._scroll_combos = {}
        if not hasattr(self, '_scroll_ints'):
            self._scroll_ints = {}
        if not dpg.does_item_exist("global_wheel_hr"):
            with dpg.handler_registry(tag="global_wheel_hr"):
                dpg.add_mouse_wheel_handler(callback=self._on_mouse_wheel)
                dpg.add_key_press_handler(dpg.mvKey_Up, callback=self._on_arrow_key)
                dpg.add_key_press_handler(dpg.mvKey_Down, callback=self._on_arrow_key)

    def _register_scroll_combo(self, tag: str, items: list, on_change):
        if not hasattr(self, '_scroll_combos'):
            self._scroll_combos = {}
        self._scroll_combos[tag] = (list(items), on_change)

    def _register_scroll_int(self, tag: str, min_val: int = 0,
                             max_val: int = 9999, on_change=None):
        if not hasattr(self, '_scroll_ints'):
            self._scroll_ints = {}
        self._scroll_ints[tag] = (min_val, max_val, on_change)

    def _on_arrow_key(self, sender, app_data):
        """Arrow Up/Down on the timestamp input shifts time."""
        if not (dpg.does_item_exist("event_timestamp_input")
                and dpg.is_item_hovered("event_timestamp_input")):
            return
        shift = dpg.is_key_down(dpg.mvKey_LShift) or dpg.is_key_down(dpg.mvKey_RShift)
        step = 1440 if shift else 15
        if app_data == dpg.mvKey_Up:
            self._shift_timestamp(step)
        else:
            self._shift_timestamp(-step)

    def _on_mouse_wheel(self, sender, app_data):
        # app_data is positive when scrolling up, negative when down.
        # We invert so scroll-up = higher value.
        delta = 1 if app_data > 0 else -1

        # ── Timestamp scroll ──────────────────────────────────────────
        if (dpg.does_item_exist("event_timestamp_input")
                and dpg.is_item_hovered("event_timestamp_input")):
            shift = dpg.is_key_down(dpg.mvKey_LShift) or dpg.is_key_down(dpg.mvKey_RShift)
            step = 1440 if shift else 15
            self._shift_timestamp(delta * step)
            return

        for tag, (items, cb) in list(getattr(self, '_scroll_combos', {}).items()):
            if dpg.does_item_exist(tag) and dpg.is_item_hovered(tag):
                itype = dpg.get_item_info(tag).get("type", "")
                if "Button" in itype:
                    cur = dpg.get_item_configuration(tag).get("label")
                else:
                    cur = str(dpg.get_value(tag))
                try:
                    idx = items.index(str(cur))
                except ValueError:
                    idx = 0
                new_idx = max(0, min(len(items) - 1, idx - delta))
                if "Button" in itype:
                    dpg.configure_item(tag, label=items[new_idx])
                else:
                    dpg.set_value(tag, items[new_idx])
                cb()
                return
        for tag, (mn, mx, cb) in list(getattr(self, '_scroll_ints', {}).items()):
            if dpg.does_item_exist(tag) and dpg.is_item_hovered(tag):
                try:
                    cur = int(dpg.get_value(tag))
                except (ValueError, TypeError):
                    cur = mn
                new_val = max(mn, min(mx, cur + delta))
                dpg.set_value(tag, str(new_val))
                if cb:
                    cb()
                return

    def _is_over_slots_panel(self, x_root: int, y_root: int) -> bool:
        try:
            mn = dpg.get_item_rect_min("slots_scroll")
            mx = dpg.get_item_rect_max("slots_scroll")
        except Exception:
            return False
        return mn[0] <= x_root <= mx[0] and mn[1] <= y_root <= mx[1]

    # ── Resize handle logic ───────────────────────────────────────────

    _resize_dragging = False
    _resize_start_y = 0
    _resize_start_h = 320

    def _resize_handle_click(self, sender, app_data):
        self._resize_dragging = True
        self._resize_start_y = dpg.get_mouse_pos(local=False)[1]
        try:
            self._resize_start_h = dpg.get_item_height("slots_scroll")
        except Exception:
            self._resize_start_h = 320

    def _resize_handle_drag(self, sender, app_data):
        if not self._resize_dragging:
            return
        current_y = dpg.get_mouse_pos(local=False)[1]
        delta = current_y - self._resize_start_y
        new_h = max(80, self._resize_start_h + int(delta))
        max_h = dpg.get_viewport_height() - 200
        new_h = min(new_h, max_h)
        dpg.configure_item("slots_scroll", height=new_h)

    def _resize_handle_release(self, sender, app_data):
        self._resize_dragging = False
