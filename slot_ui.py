import customtkinter as ctk
from tkinter import messagebox


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

        self.grid_columnconfigure(1, weight=3)
        self.grid_columnconfigure(2, weight=2)
        self.grid_columnconfigure(3, weight=1)

        # Drag handle
        self.grip = ctk.CTkButton(
            self, text="", image=self.app_ref.icon_grip,
            width=28, height=40, cursor="fleur",
            fg_color="transparent", hover_color="#334155"
        )
        self.grip.grid(row=0, column=0, padx=(8, 4), pady=10)
        self.grip.bind("<ButtonPress-1>",   lambda e: self.app_ref._slot_drag_start(e, self))
        self.grip.bind("<B1-Motion>",       lambda e: self.app_ref._slot_drag_motion(e, self))
        self.grip.bind("<ButtonRelease-1>", lambda e: self.app_ref._slot_drag_end(e, self))

        self.name_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.name_frame.grid(row=0, column=1, padx=5, pady=10, sticky="ew")
        self.name_frame.grid_columnconfigure(0, weight=1)

        self.name_entry = ctk.CTkComboBox(
            self.name_frame, variable=self.name_var, values=self.app_ref.get_dj_names(),
            fg_color="#0F172A", border_width=1, border_color="#334155",
            height=35, button_color="#334155", button_hover_color="#475569",
            dropdown_fg_color="#1E293B", dropdown_text_color="#CBD5E1",
            dropdown_hover_color="#334155",
            command=lambda v: (self.app_ref.update_output(), self.update_dj_info())
        )
        self.name_entry.grid(row=0, column=0, sticky="ew", padx=(0, 5))

        self.info_label = ctk.CTkLabel(
            self.name_frame, text="", font=("Arial", 10), text_color="#475569", anchor="w"
        )
        self.info_label.grid(row=1, column=0, columnspan=2, sticky="ew", padx=(2, 5), pady=(0, 3))
        self.info_label.grid_remove()  # hidden until there's content

        btn_frame = ctk.CTkFrame(self.name_frame, fg_color="transparent")
        btn_frame.grid(row=0, column=1)

        self.save_dj_btn = ctk.CTkButton(
            btn_frame, text="", image=self.app_ref.icon_save, width=34, height=34,
            fg_color="#334155", hover_color="#475569", command=self.save_dj
        )
        self.save_dj_btn.pack(side="left", padx=(0, 2))

        self.del_dj_btn = ctk.CTkButton(
            btn_frame, text="", image=self.app_ref.icon_trash, width=34, height=34,
            fg_color="#7F1D1D", hover_color="#991B1B", command=self.delete_saved_dj
        )
        self.del_dj_btn.pack(side="left")

        self.genre_entry = ctk.CTkEntry(
            self, textvariable=self.genre_var, placeholder_text="Genre",
            fg_color="#0F172A", border_width=1, border_color="#334155", height=35
        )
        self.genre_entry.grid(row=0, column=2, padx=5, pady=10, sticky="ew")

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
        self.dur_menu.grid(row=0, column=3, padx=5, pady=10, sticky="ew")

        self.del_btn = ctk.CTkButton(
            self, text="", image=self.app_ref.icon_trash, width=34, height=34,
            command=self.delete_slot, fg_color="#7F1D1D", hover_color="#991B1B"
        )
        self.del_btn.grid(row=0, column=4, padx=10, pady=10)

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

    # ── DJ persistence actions ────────────────────────────────────────────

    def save_dj(self):
        val = self.name_var.get().strip()
        if val and val.lower() not in [n.lower() for n in self.app_ref.get_dj_names()]:
            self.app_ref.saved_djs.append({"name": val, "stream": ""})
            self.app_ref._schedule_save_library()
            self.app_ref.refresh_dj_roster_ui()
            self.app_ref.after(0, self.app_ref._refresh_slot_combos)

    def delete_saved_dj(self):
        val = self.name_var.get().strip()
        names = self.app_ref.get_dj_names()
        if val and val in names:
            if messagebox.askyesno("Confirm Delete", f"Remove '{val}' from saved DJs?"):
                idx = names.index(val)
                self.app_ref.saved_djs.pop(idx)
                self.app_ref._save_library()
                self.name_var.set("")
                self.app_ref.refresh_dj_roster_ui()
                self.app_ref.after(0, self.app_ref._refresh_slot_combos)
                for slot in self.app_ref.slots:
                    if slot.name_var.get() == val:
                        slot.name_var.set("")

    # ── Slot actions ──────────────────────────────────────────────────────

    def on_duration_change(self, choice):
        self.app_ref.update_output()

    def move_up(self):
        self.app_ref.move_slot(self, -1)

    def move_down(self):
        self.app_ref.move_slot(self, 1)

    def delete_slot(self):
        self.app_ref.delete_slot(self)
