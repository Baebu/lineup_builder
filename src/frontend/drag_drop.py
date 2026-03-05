"""
Module: drag_drop.py
Purpose: Handles slot reordering and dragging DJs from the roster into the lineup.
Dependencies: tkinter, customtkinter, theme
Architecture: Mixin for App class. Hooks into mouse events to render visual indicators.
"""

import tkinter as tk
import customtkinter as ctk
from . import theme as T


class DragDropMixin:
    """Slot reorder drag-and-drop + DJ roster → lineup drop."""

    # ── Slot reorder ──────────────────────────────────────────────────────

    def _slot_drag_start(self, event, slot_ui):
        self._slot_ghost = None  # created on first motion
        # Cache vertical bounding boxes so we don't call winfo_rooty() every frame
        self._cached_slot_bounds: list[tuple] =[]
        for s in self.slots:
            try:
                y = s.winfo_rooty()
                h = s.winfo_height()
                self._cached_slot_bounds.append((s, y, h))
            except Exception:
                pass

    def _slot_drag_motion(self, event, slot_ui):
        name = slot_ui.name_var.get().strip() or "(empty)"
        if self._slot_ghost is None:
            primary = getattr(self, "settings", {}).get("primary_color", T.PRIMARY)
            self._slot_ghost = ctk.CTkFrame(
                self, fg_color=primary, corner_radius=6,
                border_width=1, border_color=T.BORDER
            )
            ctk.CTkLabel(
                self._slot_ghost, text=f" ↕  {name} ",
                font=T.FONT_BODY_BOLD, text_color=T.WHITE
            ).pack(padx=14, pady=8)
            self._slot_ghost.lift()
            
        rx = event.x_root - self.winfo_rootx() + 12
        ry = event.y_root - self.winfo_rooty() + 8
        self._slot_ghost.place(x=rx, y=ry)
        self._update_drop_indicator(event.y_root)

    def _slot_drag_end(self, event, slot_ui):
        if self._slot_ghost:
            self._slot_ghost.place_forget()
            self._slot_ghost.destroy()
            self._slot_ghost = None
        if self._drop_indicator:
            self._drop_indicator.place_forget()
            
        if slot_ui not in self.slots:
            return
        if not getattr(self, "_cached_slot_bounds", None):
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
        """Return the insertion index closest to y_root using cached bounds."""
        for i, (slot, sy, sh) in enumerate(self._cached_slot_bounds):
            if y_root < sy + sh // 2:
                return i
        return len(self.slots)

    def _update_drop_indicator(self, y_root):
        """Draw a thin colored line between slots at the drop position."""
        if self._drop_indicator is None:
            accent = getattr(self, "settings", {}).get("accent_color", T.ACCENT)
            # Using tk.Frame for the indicator line as it renders sharper at 2px than CTkFrame
            self._drop_indicator = tk.Frame(
                self.slots_scroll, bg=accent, height=3, bd=0
            )
            
        idx = self._get_drop_index(y_root)
        try:
            scroll_root_y = self.slots_scroll.winfo_rooty()
            if idx < len(self._cached_slot_bounds):
                _, sy, _ = self._cached_slot_bounds[idx]
                ry = sy - scroll_root_y
                self._drop_indicator.place(x=0, y=max(0, ry - 2), relwidth=1.0)
            elif self._cached_slot_bounds:
                _, sy, sh = self._cached_slot_bounds[-1]
                ry = sy + sh - scroll_root_y
                self._drop_indicator.place(x=0, y=ry, relwidth=1.0)
            self._drop_indicator.lift()
        except Exception:
            pass

    # ── DJ roster → lineup drop ───────────────────────────────────────────

    def _on_dj_drag(self, event, dj_name):
        """Create or move the drag ghost on B1-Motion."""
        if self._drag_ghost is None:
            primary = getattr(self, "settings", {}).get("primary_color", T.PRIMARY)
            self._drag_ghost = ctk.CTkFrame(
                self, fg_color=primary, corner_radius=6,
                border_width=1, border_color=T.BORDER
            )
            ctk.CTkLabel(
                self._drag_ghost, text=f" ➕  {dj_name} ",
                font=T.FONT_BODY_BOLD, text_color=T.WHITE
            ).pack(padx=14, pady=8)
            self._drag_ghost.lift()
            
        rx = event.x_root - self.winfo_rootx() + 14
        ry = event.y_root - self.winfo_rooty() + 10
        self._drag_ghost.place(x=rx, y=ry)
        
        # Highlight the slots panel if hovering over it
        if self._is_over_slots_panel(event.x_root, event.y_root):
            hover_bg = getattr(self, "settings", {}).get("hover_color", T.HOVER)
            self.slots_scroll.configure(fg_color=hover_bg)
        else:
            self.slots_scroll.configure(fg_color="transparent")

    def _end_dj_drag(self, event, dj_name):
        """Drop DJ into lineup if released over the slots panel."""
        was_dragging = self._drag_ghost is not None
        if self._drag_ghost is not None:
            self._drag_ghost.place_forget()
            self._drag_ghost.destroy()
            self._drag_ghost = None
            
        self.slots_scroll.configure(fg_color="transparent")
        
        if was_dragging and self._is_over_slots_panel(event.x_root, event.y_root):
            try:
                dur = int(self.master_duration.get())
            except ValueError:
                dur = 60
            self.add_slot(dj_name, "", dur)

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