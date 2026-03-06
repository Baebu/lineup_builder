"""
Module: slot_ui.py
Purpose: DPG variable wrappers and slot row builder for the lineup editor.
Dependencies: dearpygui, theme
"""

import dearpygui.dearpygui as dpg

from . import theme as T
from .fonts import styled_text, bind_icon_font, Icon, HEADER, LABEL, MUTED, SUCCESS, ERROR
from .widgets import add_icon_button
from .types import DPGVar, DPGBoolVar, SlotState

# Re-export for backward compatibility
__all__ = ["DPGVar", "DPGBoolVar", "SlotState", "build_slot_row"]


def _toggle_slot_fold(slot: SlotState):
    """Toggle the detail section of a slot row."""
    sid = slot._id
    detail_tag = f"slot_detail_{sid}"
    btn_tag = f"slot_fold_btn_{sid}"
    if dpg.does_item_exist(detail_tag):
        visible = dpg.is_item_shown(detail_tag)
        if visible:
            dpg.hide_item(detail_tag)
            dpg.configure_item(btn_tag, label="v")
        else:
            dpg.show_item(detail_tag)
            dpg.configure_item(btn_tag, label="^")


def _edit_dj_from_slot(slot: SlotState, app):
    """Open the DJ edit window for the DJ currently in this slot."""
    import traceback
    try:
        name = slot.name_var.get().strip()
        if not name:
            print("[slot_ui] Edit DJ: no name entered, ignoring.")
            return
        for idx, dj in enumerate(app.saved_djs):
            if dj.get("name", "").lower() == name.lower():
                app._open_dj_edit_window(dj, idx)
                return
        # DJ not in roster â€” offer to create
        app.saved_djs.append({"name": name, "stream": "", "exact_link": False})
        app._save_library()
        app.refresh_dj_roster_ui()
        idx = len(app.saved_djs) - 1
        app._open_dj_edit_window(app.saved_djs[idx], idx)
    except Exception as e:
        print(f"[slot_ui] _edit_dj_from_slot ERROR: {e}")
        traceback.print_exc()


def _on_name_input(slot: SlotState, value: str, app):
    slot.name_var.set(value)
    app._schedule_update()
    _update_slot_info(slot, app)
    # Filter and show suggestions
    sid = slot._id
    suggest_tag = f"slot_suggest_{sid}"
    query = value.strip().lower()
    if query:
        matches = [n for n in app.get_dj_names() if query in n.lower()]
    else:
        matches = []
    if matches and dpg.does_item_exist(suggest_tag):
        _show_suggestions(slot, matches)
    elif dpg.does_item_exist(suggest_tag):
        dpg.hide_item(suggest_tag)


def _show_suggestions(slot: SlotState, items: list):
    sid = slot._id
    suggest_tag = f"slot_suggest_{sid}"
    list_tag = f"slot_suggest_list_{sid}"
    name_tag = f"slot_name_{sid}"
    num = min(5, len(items))
    # Align suggestion list with the name input
    if dpg.does_item_exist(name_tag) and dpg.does_item_exist(suggest_tag):
        name_pos = dpg.get_item_pos(name_tag)
        row_pos = dpg.get_item_pos(slot.row_tag) if slot.row_tag and dpg.does_item_exist(slot.row_tag) else [0, 0]
        indent = max(0, name_pos[0] - row_pos[0])
        dpg.configure_item(suggest_tag, indent=int(indent))
    if dpg.does_item_exist(list_tag):
        w = dpg.get_item_width(name_tag) if dpg.does_item_exist(name_tag) else 175
        dpg.configure_item(list_tag, items=items, num_items=num, width=w)
    if dpg.does_item_exist(suggest_tag):
        dpg.show_item(suggest_tag)


def _toggle_name_suggest(slot: SlotState, app):
    sid = slot._id
    suggest_tag = f"slot_suggest_{sid}"
    if dpg.does_item_exist(suggest_tag) and dpg.is_item_shown(suggest_tag):
        dpg.hide_item(suggest_tag)
    else:
        all_names = app.get_dj_names()
        if all_names:
            _show_suggestions(slot, all_names)


def _select_dj_suggestion(slot: SlotState, app):
    sid = slot._id
    selected = dpg.get_value(f"slot_suggest_list_{sid}")
    if not selected:
        return
    name_tag = f"slot_name_{sid}"
    dpg.set_value(name_tag, selected)
    slot.name_var.set(selected)
    dpg.hide_item(f"slot_suggest_{sid}")
    app._schedule_update()
    _update_slot_info(slot, app)


def build_slot_row(slot: SlotState, app, parent_tag: str):
    """Create DPG widgets for *slot* inside *parent_tag*."""
    sid = slot._id
    row_tag = f"slot_row_{sid}"
    slot.row_tag = row_tag

    dur_vals = [str(x) for x in range(15, 121, 15)]
    if slot.duration_var.get() not in dur_vals:
        dur_vals.append(slot.duration_var.get())
        dur_vals.sort(key=int)

    with dpg.group(tag=row_tag, parent=parent_tag,
                   payload_type="DJ_CARD",
                   drop_callback=lambda s, a, u=None: app._drop_on_slot(s, a)):
        # Drag source: lets this slot be dragged for reordering
        with dpg.drag_payload(drag_data=("slot_reorder", sid),
                              payload_type="DJ_CARD"):
            name_preview = slot.name_var.get() or "(empty)"
            dur_preview = slot.duration_var.get() + " min"
            styled_text(f"= {name_preview}  [{dur_preview}]", HEADER)
        with dpg.group(horizontal=True):
            dpg.add_spacer(width=4)
            _drag_txt = styled_text(
                Icon.DRAG,
                MUTED,
            )
            bind_icon_font(_drag_txt)
            dpg.add_spacer(width=4)
            styled_text(
                "--:--",
                HEADER,
                tag=f"slot_time_{sid}",
            )
            dpg.add_combo(
                items=dur_vals,
                default_value=slot.duration_var.get(),
                tag=f"slot_dur_{sid}",
                width=50,
                user_data=slot,
                callback=lambda s, a, u: (
                    u.duration_var.set(a),
                    app._schedule_update(),
                ),
            )
            slot.duration_var._tag = f"slot_dur_{sid}"
            app._register_scroll_combo(
                f"slot_dur_{sid}", dur_vals,
                on_change=lambda u=slot: (u.duration_var.set(
                    dpg.get_value(f"slot_dur_{u._id}")), app._schedule_update()),
            )
            dpg.add_input_text(
                default_value=slot.name_var.get(),
                tag=f"slot_name_{sid}",
                hint="DJ name...",
                width=90,
                user_data=slot,
                callback=lambda s, a, u: _on_name_input(u, a, app),
            )
            slot.name_var._tag = f"slot_name_{sid}"
            styled_text("LINK", ERROR, tag=f"slot_info_{sid}")
            _edit_btn = add_icon_button(
                Icon.EDIT,
                user_data=slot,
                callback=lambda s, a, u: _edit_dj_from_slot(u, app),
            )

            _del_btn = add_icon_button(
                Icon.CLOSE, is_danger=True,
                user_data=slot,
                callback=lambda s, a, u: app.delete_slot(u),
            )

        # â”€â”€ Autocomplete suggestions â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        with dpg.group(tag=f"slot_suggest_{sid}", show=False):
            dpg.add_listbox(
                tag=f"slot_suggest_list_{sid}",
                items=[],
                width=175,
                num_items=4,
                user_data=slot,
                callback=lambda s, a, u: _select_dj_suggestion(u, app),
            )

        dpg.add_separator()

    _update_slot_info(slot, app)


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
        dpg.configure_item(info_tag, color=T.DPG_IMPORT_SUCCESS if has_stream else T.DPG_ERROR)