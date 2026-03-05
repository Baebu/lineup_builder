import dearpygui.dearpygui as dpg

from .slot_ui import SlotState, build_slot_row


class SlotMixin:
    """Manages lineup slots: add, remove, reorder."""

    def add_initial_slots(self):
        try:
            dur = int(self.master_duration.get())
        except (ValueError, AttributeError):
            dur = 60
        self.add_slot("", "", dur)

    def apply_master_duration(self):
        val = self.master_duration.get()
        for slot in self.slots:
            slot.duration_var.set(val)
        self.update_output()

    def add_slot(self, name: str = "", genre: str = "", duration: int = 60):
        slot = SlotState(name, genre, duration)
        self.slots.append(slot)
        build_slot_row(slot, self, "slots_scroll")
        self.update_output()

    def refresh_slots(self):
        """Delete and recreate all slot rows in the current order."""
        # Remove existing
        for slot in self.slots:
            if dpg.does_item_exist(slot.row_tag):
                dpg.delete_item(slot.row_tag)
        # Recreate in current order
        for slot in self.slots:
            build_slot_row(slot, self, "slots_scroll")

    def move_slot(self, slot_state: SlotState, direction: int):
        idx = self.slots.index(slot_state)
        new_idx = idx + direction
        if 0 <= new_idx < len(self.slots):
            self.slots[idx], self.slots[new_idx] = self.slots[new_idx], self.slots[idx]
            self.refresh_slots()
            self.update_output()

    def _duplicate_last_slot(self):
        if self.slots:
            s = self.slots[-1]
            try:
                dur = int(s.duration_var.get())
            except ValueError:
                dur = 60
            self.add_slot(s.name_var.get(), s.genre_var.get(), dur)

    def delete_slot(self, slot_state: SlotState):
        if slot_state in self.slots:
            slot_state.destroy()
            self.slots.remove(slot_state)
            self.update_output()

    def toggle_od(self):
        enabled = self.include_od.get()
        if dpg.does_item_exist("od_count_combo"):
            dpg.configure_item("od_count_combo", enabled=enabled)
        if dpg.does_item_exist("od_dur_combo"):
            dpg.configure_item("od_dur_combo", enabled=enabled)
        self.update_output()
