import customtkinter as ctk


class SlotUI(ctk.CTkFrame):
    """Represents a single performer slot row in the lineup editor."""

    def __init__(self, master, app_ref, name="", genre="", duration=60):
        super().__init__(master, fg_color="#1E293B", corner_radius=10, border_width=1, border_color="#334155")
        self.app_ref = app_ref

        self.name_var = ctk.StringVar(value=name)
        self.genre_var = ctk.StringVar(value=genre)
        self.duration_var = ctk.StringVar(value=str(duration))

        self.name_var.trace_add("write", self._on_name_change)
        self.genre_var.trace_add("write", lambda *args: self.app_ref._schedule_update())
        self.duration_var.trace_add("write", lambda *args: self.app_ref._schedule_update())

        self.grid_columnconfigure(2, weight=3)
        self.grid_columnconfigure(3, weight=2)
        self.grid_columnconfigure(4, weight=1)

        # Drag handle
        self.grip = ctk.CTkButton(
            self, text="", image=self.app_ref.icon_grip,
            width=28, height=40, cursor="fleur",
            fg_color="transparent", hover_color="#334155"
        )
        self.grip.grid(row=0, column=0, padx=(6, 0), pady=10)
        self.grip.bind("<ButtonPress-1>",   lambda e: self.app_ref._slot_drag_start(e, self))
        self.grip.bind("<B1-Motion>",       lambda e: self.app_ref._slot_drag_motion(e, self))
        self.grip.bind("<ButtonRelease-1>", lambda e: self.app_ref._slot_drag_end(e, self))

        # Slot start-time label
        self.time_lbl = ctk.CTkLabel(
            self, text="--:--", font=("Arial", 13, "bold"),
            text_color="#818CF8", width=55, anchor="center"
        )
        self.time_lbl.grid(row=0, column=1, padx=(2, 0), pady=10)

        self.name_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.name_frame.grid(row=0, column=2, padx=5, pady=10, sticky="ew")
        self.name_frame.grid_columnconfigure(0, weight=1)

        self.name_entry = ctk.CTkComboBox(
            self.name_frame, variable=self.name_var, values=self.app_ref.get_dj_names(),
            fg_color="#0F172A", border_width=1, border_color="#334155",
            height=35, button_color="#334155", button_hover_color="#475569",
            dropdown_fg_color="#1E293B", dropdown_text_color="#CBD5E1",
            dropdown_hover_color="#334155",
            command=lambda v: (self.app_ref.update_output(), self.update_dj_info())
        )
        self.name_entry.grid(row=0, column=0, sticky="ew")

        self.info_label = ctk.CTkLabel(
            self.name_frame, text="", font=("Arial", 10), text_color="#475569", anchor="w"
        )
        self.info_label.grid(row=1, column=0, sticky="ew", padx=(2, 0), pady=(0, 3))
        self.info_label.grid_remove()  # hidden until there's content

        self.genre_entry = ctk.CTkEntry(
            self, textvariable=self.genre_var, placeholder_text="Genre",
            fg_color="#0F172A", border_width=1, border_color="#334155", height=35
        )
        self.genre_entry.grid(row=0, column=3, padx=5, pady=10, sticky="ew")

        # Duration dropdown (15–120 min in 15-min steps)
        dur_values = [str(x) for x in range(15, 121, 15)]
        if self.duration_var.get() not in dur_values:
            dur_values.append(self.duration_var.get())
            dur_values.sort(key=lambda x: int(x))

        self.dur_menu = ctk.CTkOptionMenu(
            self,
            values=dur_values,
            variable=self.duration_var,
            width=90, height=35,
            fg_color="#0F172A",
            button_color="#334155", button_hover_color="#475569",
            text_color="#CBD5E1",
            dropdown_fg_color="#1E293B", dropdown_text_color="#CBD5E1",
            dropdown_hover_color="#334155",
            command=self.on_duration_change
        )
        self.dur_menu.grid(row=0, column=4, padx=5, pady=10, sticky="ew")

        self.del_btn = ctk.CTkButton(
            self, text="", image=self.app_ref.icon_trash, width=34, height=34,
            command=self.delete_slot,
            fg_color=self.app_ref.settings.get("danger_color", "#7F1D1D"), hover_color="#991B1B"
        )
        self.del_btn.grid(row=0, column=5, padx=10, pady=10)

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
