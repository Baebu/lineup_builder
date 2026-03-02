import re
import customtkinter as ctk
from tkinter import messagebox


class DJRosterMixin:
    """Manages the DJ Roster tab: display, edit, add, and delete DJ cards."""

    def refresh_dj_roster_ui(self):
        # Keep roster sorted alphabetically
        self.saved_djs.sort(key=lambda d: re.sub(r'[^a-z]', '', (d.get("name") or "").lower()))
        query = self.dj_search_var.get().strip().lower()
        filtered = [
            (idx, dj) for idx, dj in enumerate(self.saved_djs)
            if not query or query in dj.get("name", "").lower()
        ]
        for widget in self.dj_roster_scroll.winfo_children():
            widget.destroy()
        if not self.saved_djs:
            ctk.CTkLabel(
                self.dj_roster_scroll,
                text="No DJs saved yet.\nSave a DJ from a slot or press + NEW DJ.",
                text_color="#94A3B8", justify="center"
            ).pack(pady=20)
            return
        if not filtered:
            ctk.CTkLabel(
                self.dj_roster_scroll,
                text="No DJs match your search.",
                text_color="#94A3B8", justify="center"
            ).pack(pady=20)
            return
        for idx, dj in filtered:
            self._build_dj_card(self.dj_roster_scroll, dj, idx)

    def _build_dj_card(self, parent, dj, idx):
        card = ctk.CTkFrame(parent, fg_color="#0F172A", border_width=1, border_color="#334155", corner_radius=8)
        card.pack(fill="x", pady=(0, 6))

        expanded = ctk.BooleanVar(value=False)

        # ── Header row ──
        header = ctk.CTkFrame(card, fg_color="transparent", cursor="hand2")
        header.pack(fill="x", padx=10, pady=8)

        grip_btn = ctk.CTkButton(
            header, text="", image=self.icon_grip,
            width=24, height=32, cursor="fleur",
            fg_color="transparent", hover_color="#334155"
        )
        grip_btn.pack(side="left", padx=(0, 6))

        name_lbl = ctk.CTkLabel(
            header, text=dj.get("name", "Unnamed DJ"),
            font=("Arial", 13, "bold"), text_color="#CBD5E1", cursor="hand2"
        )
        name_lbl.pack(side="left")

        arrow_btn = ctk.CTkButton(
            header, text="", image=self.icon_chevron_up,
            width=32, height=32, fg_color="#334155", hover_color="#475569",
            command=lambda: toggle()
        )
        arrow_btn.pack(side="right")

        # ── Body (collapsed by default) ──
        body = ctk.CTkFrame(card, fg_color="#1E293B", corner_radius=6)

        ctk.CTkLabel(body, text="NAME", font=("Arial", 10, "bold"), text_color="#94A3B8").pack(anchor="w", padx=10, pady=(10, 2))
        name_var = ctk.StringVar(value=dj.get("name", ""))
        ctk.CTkEntry(body, textvariable=name_var, fg_color="#0F172A", border_color="#334155", height=32).pack(fill="x", padx=10, pady=(0, 8))

        ctk.CTkLabel(body, text="🎙  STREAM LINK", font=("Arial", 10, "bold"), text_color="#94A3B8").pack(anchor="w", padx=10, pady=(0, 2))
        stream_var = ctk.StringVar(value=dj.get("stream", ""))
        ctk.CTkEntry(
            body, textvariable=stream_var,
            placeholder_text="https://stream.vrcdn.live/live/...",
            fg_color="#0F172A", border_color="#334155", height=32
        ).pack(fill="x", padx=10, pady=(0, 8))

        btn_row = ctk.CTkFrame(body, fg_color="transparent")
        btn_row.pack(fill="x", padx=10, pady=(0, 10))
        ctk.CTkButton(
            btn_row, text="", image=self.icon_save, width=34, height=34,
            fg_color="#059669", hover_color="#047857",
            command=lambda: self._save_dj_card(idx, name_var, stream_var, name_lbl)
        ).pack(side="left", padx=(0, 6))
        ctk.CTkButton(
            btn_row, text="", image=self.icon_trash, width=34, height=34,
            fg_color="#7F1D1D", hover_color="#991B1B",
            command=lambda i=idx: self._delete_dj_from_roster(i)
        ).pack(side="left")

        def toggle(event=None):
            if expanded.get():
                body.pack_forget()
                arrow_btn.configure(image=self.icon_chevron_up)
                expanded.set(False)
            else:
                body.pack(fill="x", padx=6, pady=(0, 8))
                arrow_btn.configure(image=self.icon_chevron_down)
                expanded.set(True)

        header.bind("<Button-1>", toggle)
        name_lbl.bind("<Button-1>", toggle)

        # Drag-and-drop: grip → add to lineup
        for w in (grip_btn,):
            w.bind("<B1-Motion>",       lambda e: self._on_dj_drag(e, name_lbl.cget("text")))
            w.bind("<ButtonRelease-1>", lambda e: self._end_dj_drag(e, name_lbl.cget("text")))

    def _save_dj_card(self, idx, name_var, stream_var, name_lbl):
        new_name = name_var.get().strip()
        if not new_name:
            return
        old_name = self.saved_djs[idx].get("name", "")
        self.saved_djs[idx] = {
            "name": new_name,
            "stream": stream_var.get().strip()
        }
        self._save_library()
        name_lbl.configure(text=new_name)
        self.after(0, self._refresh_slot_combos)
        for slot in self.slots:
            if slot.name_var.get().strip() in (old_name, new_name):
                slot.update_dj_info()

    def _delete_dj_from_roster(self, idx):
        if idx < len(self.saved_djs):
            name = self.saved_djs[idx].get("name", "this DJ")
            if messagebox.askyesno("Confirm Delete", f"Remove '{name}' from the roster?"):
                self.saved_djs.pop(idx)
                self._save_library()
                self.refresh_dj_roster_ui()
                self.after(0, self._refresh_slot_combos)

    def add_new_dj_to_roster(self):
        """Open a modal popup to collect DJ details before adding to the roster."""
        popup = ctk.CTkToplevel(self)
        popup.title("New DJ")
        popup.geometry("380x240")
        popup.resizable(False, False)
        popup.configure(fg_color="#0F172A")
        popup.grab_set()
        popup.focus_force()

        self.update_idletasks()
        x = self.winfo_x() + (self.winfo_width()  - 380) // 2
        y = self.winfo_y() + (self.winfo_height() - 240) // 2
        popup.geometry(f"380x240+{x}+{y}")

        content = ctk.CTkFrame(popup, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=20, pady=16)
        content.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(content, text="NAME", font=("Arial", 10, "bold"), text_color="#94A3B8").grid(row=0, column=0, sticky="w", pady=(0, 2))
        name_var = ctk.StringVar()
        name_entry = ctk.CTkEntry(content, textvariable=name_var, height=34,
                                   fg_color="#1E293B", border_color="#334155")
        name_entry.grid(row=1, column=0, sticky="ew", pady=(0, 10))

        ctk.CTkLabel(content, text="🎙  STREAM LINK", font=("Arial", 10, "bold"), text_color="#94A3B8").grid(row=2, column=0, sticky="w", pady=(0, 2))
        stream_var = ctk.StringVar()
        ctk.CTkEntry(
            content, textvariable=stream_var,
            placeholder_text="https://stream.vrcdn.live/live/...",
            height=34, fg_color="#1E293B", border_color="#334155"
        ).grid(row=3, column=0, sticky="ew", pady=(0, 14))

        btn_row = ctk.CTkFrame(content, fg_color="transparent")
        btn_row.grid(row=4, column=0, sticky="e")

        def _save():
            name = name_var.get().strip()
            if not name:
                name_entry.configure(border_color="#EF4444")
                return
            if name.lower() in [d.get("name", "").lower() for d in self.saved_djs]:
                name_entry.configure(border_color="#EF4444")
                ctk.CTkLabel(content, text="Name already exists.",
                             font=("Arial", 10), text_color="#EF4444").grid(row=5, column=0, sticky="w")
                return
            self.saved_djs.append({"name": name, "stream": stream_var.get().strip()})
            self._save_library()
            self.refresh_dj_roster_ui()
            self.after(0, self._refresh_slot_combos)
            popup.destroy()

        ctk.CTkButton(
            btn_row, text="Cancel", width=80, height=32,
            fg_color="#334155", hover_color="#475569", font=("Arial", 11, "bold"),
            command=popup.destroy
        ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            btn_row, text="", image=self.icon_save, width=34, height=32,
            fg_color="#059669", hover_color="#047857",
            command=_save
        ).pack(side="left")

        popup.bind("<Return>", lambda e: _save())
        popup.bind("<Escape>", lambda e: popup.destroy())
        name_entry.focus_set()
