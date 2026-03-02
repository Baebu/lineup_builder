import tkinter as tk


class DragDropMixin:
    """Slot reorder drag-and-drop + DJ roster → lineup drop."""

    # ── Slot reorder ──────────────────────────────────────────────────────

    def _slot_drag_start(self, event, slot_ui):
        self._slot_ghost = None  # created on first motion

    def _slot_drag_motion(self, event, slot_ui):
        name = slot_ui.name_var.get().strip() or "(empty)"
        if self._slot_ghost is None:
            self._slot_ghost = tk.Toplevel(self)
            self._slot_ghost.overrideredirect(True)
            self._slot_ghost.attributes("-alpha", 0.80)
            self._slot_ghost.configure(bg="#4F46E5")
            tk.Label(
                self._slot_ghost, text=f"  {name}  ",
                font=("Arial", 12, "bold"), fg="white", bg="#4F46E5",
                padx=10, pady=5
            ).pack()
        self._slot_ghost.geometry(f"+{event.x_root + 12}+{event.y_root + 8}")
        self._update_drop_indicator(event.y_root)

    def _slot_drag_end(self, event, slot_ui):
        if self._slot_ghost:
            self._slot_ghost.destroy()
            self._slot_ghost = None
        if self._drop_indicator:
            self._drop_indicator.place_forget()
        if slot_ui not in self.slots:
            return
        target_idx = self._get_drop_index(event.y_root)
        src_idx = self.slots.index(slot_ui)
        if target_idx is not None and target_idx != src_idx:
            self.slots.pop(src_idx)
            if target_idx > src_idx:
                target_idx -= 1
            self.slots.insert(target_idx, slot_ui)
            self.refresh_slots()
            self.update_output()

    def _get_drop_index(self, y_root):
        """Return the insertion index closest to y_root."""
        for i, slot in enumerate(self.slots):
            try:
                sy = slot.winfo_rooty()
                sh = slot.winfo_height()
                if y_root < sy + sh // 2:
                    return i
            except Exception:
                pass
        return len(self.slots)

    def _update_drop_indicator(self, y_root):
        """Draw a thin colored line between slots at the drop position."""
        if self._drop_indicator is None:
            self._drop_indicator = tk.Frame(
                self.slots_scroll, bg="#818CF8", height=3, bd=0
            )
        idx = self._get_drop_index(y_root)
        try:
            if idx < len(self.slots):
                ref = self.slots[idx]
                ry = ref.winfo_rooty() - self.slots_scroll.winfo_rooty()
                self._drop_indicator.place(x=0, y=max(0, ry - 2), relwidth=1.0)
            else:
                ref = self.slots[-1]
                ry = ref.winfo_rooty() + ref.winfo_height() - self.slots_scroll.winfo_rooty()
                self._drop_indicator.place(x=0, y=ry, relwidth=1.0)
            self._drop_indicator.lift()
        except Exception:
            pass

    # ── DJ roster → lineup drop ───────────────────────────────────────────

    def _on_dj_drag(self, event, dj_name):
        """Create or move the drag ghost on B1-Motion."""
        if self._drag_ghost is None:
            self._drag_ghost = tk.Toplevel(self)
            self._drag_ghost.overrideredirect(True)
            self._drag_ghost.attributes("-alpha", 0.88)
            self._drag_ghost.configure(bg="#4F46E5")
            tk.Label(
                self._drag_ghost, text=f"  {dj_name}  ",
                font=("Arial", 12, "bold"), fg="white", bg="#4F46E5",
                padx=12, pady=6
            ).pack()
            self._drag_ghost.lift()
        self._drag_ghost.geometry(f"+{event.x_root + 14}+{event.y_root + 10}")
        if self._is_over_slots_panel(event.x_root, event.y_root):
            self.slots_scroll.configure(fg_color="#1E3A5F")
        else:
            self.slots_scroll.configure(fg_color="transparent")

    def _end_dj_drag(self, event, dj_name):
        """Drop DJ into lineup if released over the slots panel."""
        was_dragging = self._drag_ghost is not None
        if self._drag_ghost is not None:
            self._drag_ghost.destroy()
            self._drag_ghost = None
        self.slots_scroll.configure(fg_color="transparent")
        if was_dragging and self._is_over_slots_panel(event.x_root, event.y_root):
            try:
                dur = int(self.master_duration.get())
            except ValueError:
                dur = 60
            self.add_slot(dj_name, "", dur)
            try:
                self.right_tabs.set("Lineup")
            except Exception:
                pass

    def _is_over_slots_panel(self, x_root, y_root):
        """Return True if screen coordinates are within self.slots_scroll."""
        try:
            sx = self.slots_scroll.winfo_rootx()
            sy = self.slots_scroll.winfo_rooty()
            sw = self.slots_scroll.winfo_width()
            sh = self.slots_scroll.winfo_height()
            return sx <= x_root <= sx + sw and sy <= y_root <= sy + sh
        except Exception:
            return False
