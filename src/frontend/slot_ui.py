"""
Module: slot_ui.py
Purpose: Represents a single performer slot row in the lineup editor.
Dependencies: customtkinter, theme
Architecture: Instantiated by SlotMixin, communicates with App via app_ref.
"""

import customtkinter as ctk
from . import theme as T


class SlotUI(ctk.CTkFrame):
    """Represents a single performer slot row in the lineup editor."""

    def __init__(self, master, app_ref, name="", genre="", duration=60):
        super().__init__(master, fg_color=T.PANEL_BG, corner_radius=T.CARD_RADIUS, border_width=T.BORDER_W, border_color=T.BORDER)
        self.app_ref = app_ref

        self.name_var = ctk.StringVar(value=name)
        self.genre_var = ctk.StringVar(value=genre)
        self.duration_var = ctk.StringVar(value=str(duration))

        self._name_cb_name = self.name_var.trace_add("write", self._on_name_change)
        self._genre_cb_name = self.genre_var.trace_add("write", lambda *args: self.app_ref._schedule_update())
        self._duration_cb_name = self.duration_var.trace_add("write", lambda *args: self.app_ref._schedule_update())

        self.grid_columnconfigure(2, weight=1)
        self.configure(cursor="fleur")

        # Bind drag to the card frame itself
        self.bind("<ButtonPress-1>",   lambda e: self.app_ref._slot_drag_start(e, self))
        self.bind("<B1-Motion>",       lambda e: self.app_ref._slot_drag_motion(e, self))
        self.bind("<ButtonRelease-1>", lambda e: self.app_ref._slot_drag_end(e, self))

        # Drag handle
        self.grip = ctk.CTkButton(
            self, text="", image=self.app_ref.icon_grip,
            width=28, height=40, cursor="fleur",
            fg_color="transparent", hover_color=T.BORDER,
            corner_radius=6
        )
        self.grip.grid(row=0, column=0, padx=(6, 0), pady=6)
        self.grip.bind("<ButtonPress-1>",   lambda e: self.app_ref._slot_drag_start(e, self))
        self.grip.bind("<B1-Motion>",       lambda e: self.app_ref._slot_drag_motion(e, self))
        self.grip.bind("<ButtonRelease-1>", lambda e: self.app_ref._slot_drag_end(e, self))

        # Slot start-time label
        self.time_lbl = ctk.CTkLabel(
            self, text="--:--", font=T.FONT_VALUE,
            text_color=T.ACCENT, width=55, anchor="center", cursor="fleur"
        )
        self.time_lbl.grid(row=0, column=1, padx=(2, 0), pady=6)
        self.time_lbl.bind("<ButtonPress-1>",   lambda e: self.app_ref._slot_drag_start(e, self))
        self.time_lbl.bind("<B1-Motion>",       lambda e: self.app_ref._slot_drag_motion(e, self))
        self.time_lbl.bind("<ButtonRelease-1>", lambda e: self.app_ref._slot_drag_end(e, self))

        self.name_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.name_frame.grid(row=0, column=2, padx=6, pady=6, sticky="ew")
        self.name_frame.grid_columnconfigure(0, weight=1)

        self.name_entry = ctk.CTkComboBox(
            self.name_frame, variable=self.name_var, values=self.app_ref.get_dj_names(),
            **T.COMBO,
            command=lambda v: (self.app_ref.update_output(), self.update_dj_info())
        )
        self.name_entry.grid(row=0, column=0, sticky="ew")

        self.info_label = ctk.CTkLabel(
            self.name_frame, text="", font=T.FONT_SMALL, text_color=T.TEXT_MUTED, anchor="w",
            cursor="fleur"
        )
        self.info_label.grid(row=1, column=0, sticky="ew", padx=(2, 0), pady=(0, 3))
        self.info_label.grid_remove()  # hidden until there's content
        self.info_label.bind("<ButtonPress-1>",   lambda e: self.app_ref._slot_drag_start(e, self))
        self.info_label.bind("<B1-Motion>",       lambda e: self.app_ref._slot_drag_motion(e, self))
        self.info_label.bind("<ButtonRelease-1>", lambda e: self.app_ref._slot_drag_end(e, self))

        # Duration dropdown (15–120 min in 15-min steps)
        dur_values =[str(x) for x in range(15, 121, 15)]
        if self.duration_var.get() not in dur_values:
            dur_values.append(self.duration_var.get())
            dur_values.sort(key=lambda x: int(x))

        self.dur_menu = ctk.CTkOptionMenu(
            self,
            values=dur_values,
            variable=self.duration_var,
            width=80, height=T.WIDGET_H,
            **T.OPTION_MENU,
            command=self.on_duration_change
        )
        self.dur_menu.grid(row=0, column=3, padx=6, pady=6, sticky="ew")

        # Refined Delete Button
        self.del_btn = ctk.CTkButton(
            self, text="", image=self.app_ref.icon_trash,
            command=self.delete_slot,
            **T.BTN_ICON_DANGER
        )
        self.del_btn.grid(row=0, column=4, padx=(2, 8), pady=6)

    # ── Internal callbacks ────────────────────────────────────────────────

    def _on_name_change(self, *args):
        self.app_ref._schedule_update()
        self.update_dj_info()

    def update_dj_info(self):
        val = self.name_var.get().strip()
        dj = next((d for d in self.app_ref.saved_djs if d.get("name") == val), None)
        has_stream = bool(dj and dj.get("stream"))
        self.info_label.configure(text="🎙 Stream linked" if has_stream else "")
        if has_stream:
            self.info_label.grid()
        else:
            self.info_label.grid_remove()

    # ── Slot actions ──────────────────────────────────────────────────────

    def on_duration_change(self, choice):
        self.app_ref.update_output()

    def move_up(self):
        self.app_ref.move_slot(self, -1)

    def move_down(self):
        self.app_ref.move_slot(self, 1)

    def delete_slot(self):
        self.app_ref.delete_slot(self)

    def destroy(self):
        """Clean up traces to prevent memory leaks."""
        try:
            self.name_var.trace_remove("write", self._name_cb_name)
        except Exception:
            pass
        try:
            self.genre_var.trace_remove("write", self._genre_cb_name)
        except Exception:
            pass
        try:
            self.duration_var.trace_remove("write", self._duration_cb_name)
        except Exception:
            pass
        super().destroy()