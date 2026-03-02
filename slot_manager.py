from slot_ui import SlotUI


class SlotMixin:
    """Manages lineup slots: add, remove, reorder, open-decks toggle."""

    def add_initial_slots(self):
        self.add_slot("", "", int(self.master_duration.get()))

    def apply_master_duration(self):
        val = self.master_duration.get()
        for slot in self.slots:
            slot.duration_var.set(val)
        self.update_output()

    def add_slot(self, name="", genre="", duration=60):
        slot = SlotUI(self.slots_scroll, self, name, genre, duration)
        self.slots.append(slot)
        self.refresh_slots()
        self.update_output()

    def refresh_slots(self):
        for child in self.slots_scroll.winfo_children():
            child.pack_forget()
        for slot in self.slots:
            slot.pack(fill="x", pady=5)

    def move_slot(self, slot_ui, direction):
        idx = self.slots.index(slot_ui)
        new_idx = idx + direction
        if 0 <= new_idx < len(self.slots):
            self.slots[idx], self.slots[new_idx] = self.slots[new_idx], self.slots[idx]
            self.refresh_slots()
            self.update_output()

    def delete_slot(self, slot_ui):
        if slot_ui in self.slots:
            slot_ui.destroy()
            self.slots.remove(slot_ui)
            self.update_output()

    def toggle_od(self):
        if self.include_od.get():
            self.od_dur_label.configure(text_color="#94A3B8")
            self.od_count_label.configure(text_color="#94A3B8")
            self.od_dur_menu.configure(state="normal", text_color="#FFFFFF", button_color="#334155")
            self.od_count_menu.configure(state="normal", text_color="#FFFFFF", button_color="#334155")
        else:
            self.od_dur_label.configure(text_color="#475569")
            self.od_count_label.configure(text_color="#475569")
            self.od_dur_menu.configure(state="disabled", text_color="#475569", button_color="#1E293B")
            self.od_count_menu.configure(state="disabled", text_color="#475569", button_color="#1E293B")
        self.update_output()
