"""
Module: drag_drop.py
Purpose: Slot reordering and DJ-to-lineup interaction helpers.
Architecture: Mixin for App class. Slot order uses ↑/↓ buttons (slot_ui).
              DJ-to-lineup done via "Add" button in dj_roster.
"""


class DragDropMixin:
    """Helpers for roster-to-lineup and slot reordering via buttons."""

    def _add_dj_to_lineup(self, dj_name: str):
        """Add a DJ from the roster directly into a new lineup slot."""
        try:
            dur = int(self.master_duration.get())
        except (ValueError, AttributeError):
            dur = 60
        self.add_slot(dj_name, "", dur)

    def _refresh_slot_combos(self):
        """Update name combo items on all existing slot rows after roster changes."""
        import dearpygui.dearpygui as dpg
        names = self.get_dj_names()
        for slot in self.slots:
            tag = f"slot_name_{slot._id}"
            if dpg.does_item_exist(tag):
                current = dpg.get_value(tag)
                dpg.configure_item(tag, items=names)
                if current not in names:
                    dpg.set_value(tag, current)



