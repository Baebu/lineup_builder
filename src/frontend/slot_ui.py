"""
Module: slot_ui.py
Purpose: DPG variable wrappers and slot row builder for the lineup editor.
Dependencies: dearpygui, theme
"""

import dearpygui.dearpygui as dpg

from . import theme as T
from .fonts import Icon


class DPGVar:
    """tkinter.StringVar replacement backed by a DPG input item."""

    def __init__(self, tag=None, default=""):
        self._tag = tag
        self._value = str(default)

    def get(self) -> str:
        if self._tag and dpg.does_item_exist(self._tag):
            return str(dpg.get_value(self._tag))
        return self._value

    def set(self, value):
        self._value = str(value)
        if self._tag and dpg.does_item_exist(self._tag):
            dpg.set_value(self._tag, self._value)

    # Compatibility stubs so code calling trace_add/trace_remove won't crash
    def trace_add(self, mode, callback):
        pass

    def trace_remove(self, mode, name):
        pass


class DPGBoolVar:
    """tkinter.BooleanVar replacement backed by a DPG checkbox item."""

    def __init__(self, tag=None, default=False):
        self._tag = tag
        self._value = bool(default)

    def get(self) -> bool:
        if self._tag and dpg.does_item_exist(self._tag):
            return bool(dpg.get_value(self._tag))
        return self._value

    def set(self, value):
        self._value = bool(value)
        if self._tag and dpg.does_item_exist(self._tag):
            dpg.set_value(self._tag, self._value)

    def trace_add(self, mode, callback):
        pass

    def trace_remove(self, mode, name):
        pass


class SlotState:
    """Pure-data holder for a single performer slot; UI built by build_slot_row()."""

    _counter = 0

    def __init__(self, name="", genre="", duration=60):
        SlotState._counter += 1
        self._id = SlotState._counter
        self.name_var     = DPGVar(default=name)
        self.genre_var    = DPGVar(default=genre)
        self.duration_var = DPGVar(default=str(duration))
        self.row_tag      = None  # set by build_slot_row

    def destroy(self):
        """Remove the DPG widgets for this slot."""
        if self.row_tag and dpg.does_item_exist(self.row_tag):
            dpg.delete_item(self.row_tag)
        self.row_tag = None


def build_slot_row(slot: SlotState, app, parent_tag: str):
    """Create DPG widgets for *slot* inside *parent_tag*."""
    sid = slot._id
    row_tag = f"slot_row_{sid}"
    slot.row_tag = row_tag

    dur_vals = [str(x) for x in range(15, 121, 15)]
    if slot.duration_var.get() not in dur_vals:
        dur_vals.append(slot.duration_var.get())
        dur_vals.sort(key=int)

    with dpg.group(tag=row_tag, parent=parent_tag):
        with dpg.group(horizontal=True):
            dpg.add_text(
                "--:--",
                tag=f"slot_time_{sid}",
                color=T.DPG_ACCENT,
            )
            dpg.add_combo(
                items=app.get_dj_names(),
                default_value=slot.name_var.get(),
                tag=f"slot_name_{sid}",
                width=200,
                callback=lambda s, a, u=slot: _on_name_change(u, a, app),
            )
            slot.name_var._tag = f"slot_name_{sid}"

            dpg.add_combo(
                items=dur_vals,
                default_value=slot.duration_var.get(),
                tag=f"slot_dur_{sid}",
                width=75,
                callback=lambda s, a, u=slot: (
                    slot.duration_var.set(a),
                    app._schedule_update(),
                ),
            )
            slot.duration_var._tag = f"slot_dur_{sid}"

            dpg.add_button(
                label=Icon.UP,
                callback=lambda s, a, u=slot: app.move_slot(u, -1),
            )
            dpg.add_button(
                label=Icon.DOWN,
                callback=lambda s, a, u=slot: app.move_slot(u, 1),
            )
            dpg.add_button(
                label=Icon.CLOSE,
                callback=lambda s, a, u=slot: app.delete_slot(u),
            )
        dpg.add_text("", tag=f"slot_info_{sid}", color=T.DPG_TEXT_MUTED, show=False)
        dpg.add_separator()


def _on_name_change(slot: SlotState, value: str, app):
    slot.name_var.set(value)
    app._schedule_update()
    _update_slot_info(slot, app)


def _update_slot_info(slot: SlotState, app):
    val = slot.name_var.get().strip()
    sid = slot._id
    dj = next((d for d in app.saved_djs if d.get("name") == val), None)
    has_stream = bool(dj and dj.get("stream"))
    info_tag = f"slot_info_{sid}"
    if dpg.does_item_exist(info_tag):
        dpg.set_value(info_tag, "\U0001f3d9 Stream linked" if has_stream else "")
        if has_stream:
            dpg.show_item(info_tag)
        else:
            dpg.hide_item(info_tag)