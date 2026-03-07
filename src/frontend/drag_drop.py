"""
Module: drag_drop.py
Purpose: Slot reordering and DJ-to-lineup interaction helpers.
Architecture: Mixin for App class. Drag-and-drop for slot reordering
              and DJ roster → lineup insertion.
"""
import dearpygui.dearpygui as dpg

from . import theme as T

# ── Highlight theme (created once, reused) ────────────────────────────────
_flash_theme_tag = "_dd_flash_theme"


def _ensure_flash_theme():
    """Create a DPG theme that tints a group with the accent color."""
    if dpg.does_item_exist(_flash_theme_tag):
        return
    with dpg.theme(tag=_flash_theme_tag):
        with dpg.theme_component(dpg.mvAll):
            dpg.add_theme_color(dpg.mvThemeCol_Text, T.DPG_ACCENT)


class DragDropMixin:
    """Helpers for roster-to-lineup drag/drop and slot reordering."""

    def _add_dj_to_lineup(self, dj_name: str):
        """Add a DJ from the roster directly into a new lineup slot."""
        self.add_slot(dj_name, "")

    def _drop_dj_on_lineup(self, sender, app_data):
        """Handle DJ card dropped onto the slots panel — creates a new slot."""
        if app_data:
            self._add_dj_to_lineup(str(app_data))

    def _drop_on_slot(self, sender, app_data):
        """Unified drop handler for slot rows.

        Accepts two payload shapes:
        - ("slot_reorder", slot_id)  — reorder slots
        - str (DJ name)              — assign DJ to slot
        """
        if not app_data:
            return
        # Slot reorder
        if isinstance(app_data, (tuple, list)) and len(app_data) == 2 and app_data[0] == "slot_reorder":
            dragged_id = app_data[1]
            self._reorder_slot_by_drop(sender, dragged_id)
            return
        # DJ card drop — assign name to existing slot
        dj_name = str(app_data)
        for slot in self.slots:
            if slot.row_tag == sender:
                slot.name_var.set(dj_name)
                self._schedule_update()
                from .slot_ui import _update_slot_info
                _update_slot_info(slot, self)
                self._flash_slot(slot)
                return

    def _reorder_slot_by_drop(self, target_row_tag: str, dragged_slot_id: int):
        """Move the dragged slot to the position of the target slot."""
        drag_idx = next((i for i, s in enumerate(self.slots) if s._id == dragged_slot_id), None)
        drop_idx = next((i for i, s in enumerate(self.slots) if s.row_tag == target_row_tag), None)
        if drag_idx is None or drop_idx is None or drag_idx == drop_idx:
            return
        slot = self.slots.pop(drag_idx)
        self.slots.insert(drop_idx, slot)
        self.refresh_slots()
        self.update_output()
        # Flash the moved slot briefly to confirm placement
        self._flash_slot(slot)

    def _flash_slot(self, slot):
        """Briefly highlight a slot row with the accent theme, then revert."""
        _ensure_flash_theme()
        tag = slot.row_tag
        if not tag or not dpg.does_item_exist(tag):
            return
        dpg.bind_item_theme(tag, _flash_theme_tag)
        # Remove the highlight after 400 ms
        self._timer("_flash_job", 0.4, lambda: self._clear_flash(tag))

    @staticmethod
    def _clear_flash(tag: str):
        if dpg.does_item_exist(tag):
            dpg.bind_item_theme(tag, 0)

    def _refresh_slot_combos(self):
        """Update suggestion list items on all existing slot rows after roster changes."""
        import dearpygui.dearpygui as dpg
        names = self.get_dj_names()
        for slot in self.slots:
            # The name field is now an input_text; just keep the current value as-is.
            # Suggestion list will always use fresh get_dj_names() when opened.
            tag = f"slot_name_{slot._id}"
            if dpg.does_item_exist(tag):
                current = dpg.get_value(tag)
                # Keep current value — nothing to reconfigure for input_text



