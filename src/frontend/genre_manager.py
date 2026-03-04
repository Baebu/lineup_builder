import customtkinter as ctk
from tkinter import messagebox, simpledialog


class GenreMixin:
    """Manages active-genre tags and the saved-genres panel."""

    def add_genre_from_entry(self, event=None):
        val = self.genre_entry_var.get().strip()
        if val:
            self.add_genre(val)
            self.genre_entry_var.set("")

    def add_genre(self, genre):
        genre = genre.strip()
        if genre.lower() not in [g.lower() for g in self.active_genres]:
            self.active_genres.append(genre)

        if genre.lower() not in [g.lower() for g in self.saved_genres]:
            self.saved_genres.append(genre)
            self._save_library()

        self.refresh_genre_tags()
        self.update_output()

    def delete_saved_genre(self):
        val = self.genre_entry_var.get().strip()
        if val and val in self.saved_genres:
            if messagebox.askyesno("Confirm Delete", f"Remove '{val}' from saved genres?"):
                self.saved_genres.remove(val)
                if val in self.active_genres:
                    self.active_genres.remove(val)
                self._save_library()
                self.genre_entry_var.set("")
                self.refresh_genre_tags()
                self.update_output()

    def remove_genre(self, genre):
        if genre in self.active_genres:
            self.active_genres.remove(genre)
        self.refresh_genre_tags()
        self.update_output()

    def _toggle_genre(self, genre: str, is_active: bool):
        if is_active:
            self.remove_genre(genre)
        else:
            if genre.lower() not in [g.lower() for g in self.active_genres]:
                self.active_genres.append(genre)
            self.refresh_genre_tags()
            self.update_output()

    def refresh_genre_tags(self):
        for widget in self.genre_tags_frame.winfo_children():
            widget.destroy()

        if not self.saved_genres:
            ctk.CTkLabel(
                self.genre_tags_frame,
                text="Type a genre above and press Enter to add it.",
                text_color="#475569", font=("Arial", 10),
            ).grid(row=0, column=0, padx=2, pady=2)
            return

        active_lower = {g.lower() for g in self.active_genres}
        primary = getattr(self, "settings", {}).get("primary_color", "#4F46E5")
        buttons = []
        for genre in self.saved_genres:
            is_active = genre.lower() in active_lower
            btn = ctk.CTkButton(
                self.genre_tags_frame,
                text=genre,
                command=lambda g=genre, a=is_active: self._toggle_genre(g, a),
                fg_color=primary if is_active else "#1E293B",
                hover_color="#4338CA" if is_active else "#334155",
                text_color="#FFFFFF" if is_active else "#94A3B8",
                border_width=1,
                border_color=primary if is_active else "#334155",
                height=26, font=("Arial", 11), corner_radius=6,
            )
            buttons.append(btn)

        # Update drawer header with active count
        active_count = len(self.active_genres)
        total_count = len(self.saved_genres)
        chevron = "▾" if getattr(self, "_genre_drawer_open", True) else "▸"
        lbl = f"{chevron}  SAVED GENRES"
        if active_count:
            lbl += f"  ({active_count}/{total_count} active)"
        if hasattr(self, "_genre_drawer_chevron"):
            self._genre_drawer_chevron.configure(text=lbl)

        self._genre_buttons = buttons

        def _reflow(event=None):
            canvas = getattr(self, "_genre_canvas", None)
            frame_w = canvas.winfo_width() if canvas else self.genre_tags_frame.winfo_width()
            if frame_w <= 1:
                frame_w = 400
            cols = max(1, frame_w // 120)
            for c in range(max(cols + 1, 10)):
                self.genre_tags_frame.grid_columnconfigure(c, weight=0, minsize=0)
            for c in range(cols):
                self.genre_tags_frame.grid_columnconfigure(c, weight=1)
            for i, btn in enumerate(self._genre_buttons):
                r, c = divmod(i, cols)
                btn.grid(row=r, column=c, padx=1, pady=1, sticky="ew")
            # Update canvas scroll region after reflow
            if canvas:
                canvas.configure(scrollregion=canvas.bbox("all"))

        self._genre_reflow = _reflow
        _reflow()
        # Single replacing bind — always calls current self._genre_reflow
        self.genre_tags_frame.bind("<Configure>", lambda e: self._genre_reflow(e))

    # ── Drawer toggle ─────────────────────────────────────────────────────

    def _toggle_genre_drawer(self):
        self._genre_drawer_open = not getattr(self, "_genre_drawer_open", True)
        if self._genre_drawer_open:
            self._genre_drawer_body.pack(fill="x", pady=(2, 0))
        else:
            self._genre_drawer_body.pack_forget()
        # Refresh header chevron + count
        self.refresh_genre_tags()

    # ── Genre editor popout ───────────────────────────────────────────────

    def open_genre_editor(self):
        """Open a floating window for managing the saved-genre library."""
        # Prevent opening multiple copies
        if hasattr(self, "_genre_editor_win") and self._genre_editor_win.winfo_exists():
            self._genre_editor_win.focus()
            return

        win = ctk.CTkToplevel(self)
        self._genre_editor_win = win
        win.title("Edit Genres")
        win.geometry("340x480")
        win.resizable(True, True)
        win.configure(fg_color="#0F172A")
        win.grab_set()
        win.focus()

        # ── Header ────────────────────────────────────────────────────────
        header = ctk.CTkFrame(win, fg_color="#1E293B", corner_radius=0)
        header.pack(fill="x")
        ctk.CTkLabel(
            header, text="Genre Library",
            font=("Arial", 14, "bold"), text_color="#818CF8",
        ).pack(side="left", padx=14, pady=10)
        ctk.CTkLabel(
            header, text="Changes apply immediately",
            font=("Arial", 10), text_color="#475569",
        ).pack(side="left")

        # ── Add-new row ───────────────────────────────────────────────────
        add_frame = ctk.CTkFrame(win, fg_color="transparent")
        add_frame.pack(fill="x", padx=12, pady=(10, 4))
        add_frame.grid_columnconfigure(0, weight=1)

        new_var = ctk.StringVar()
        add_entry = ctk.CTkEntry(
            add_frame, textvariable=new_var,
            placeholder_text="New genre name…",
            fg_color="#0F172A", border_color="#334155", height=34,
        )
        add_entry.grid(row=0, column=0, sticky="ew", padx=(0, 6))

        def _add_new(event=None):
            val = new_var.get().strip()
            if not val:
                return
            new_var.set("")
            self.add_genre(val)
            _rebuild()

        add_entry.bind("<Return>", _add_new)
        ctk.CTkButton(
            add_frame, text="Add", width=56, height=34,
            fg_color="#4F46E5", hover_color="#4338CA",
            font=("Arial", 11, "bold"),
            command=_add_new,
        ).grid(row=0, column=1)

        # ── Scrollable genre list ─────────────────────────────────────────
        scroll = ctk.CTkScrollableFrame(win, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=12, pady=(4, 12))
        scroll.grid_columnconfigure(0, weight=1)

        def _rebuild():
            for w in scroll.winfo_children():
                w.destroy()
            if not self.saved_genres:
                ctk.CTkLabel(
                    scroll, text="No genres saved yet.",
                    text_color="#475569", font=("Arial", 11),
                ).pack(pady=20)
                return

            for i, genre in enumerate(self.saved_genres):
                row = ctk.CTkFrame(
                    scroll, fg_color="#1E293B",
                    corner_radius=8, border_width=1, border_color="#334155",
                )
                row.pack(fill="x", pady=(0, 5))
                row.grid_columnconfigure(1, weight=1)

                # ── Reorder buttons ────────────────────────────────────
                btn_col = ctk.CTkFrame(row, fg_color="transparent")
                btn_col.grid(row=0, column=0, padx=(8, 4), pady=8)
                ctk.CTkButton(
                    btn_col, text="", image=self.icon_arrow_up,
                    width=26, height=24, fg_color="#334155", hover_color="#475569",
                    command=lambda idx=i: _move(idx, -1),
                ).pack(pady=(0, 2))
                ctk.CTkButton(
                    btn_col, text="", image=self.icon_arrow_down,
                    width=26, height=24, fg_color="#334155", hover_color="#475569",
                    command=lambda idx=i: _move(idx, 1),
                ).pack()

                # ── Inline rename entry ────────────────────────────────
                name_var = ctk.StringVar(value=genre)
                entry = ctk.CTkEntry(
                    row, textvariable=name_var,
                    fg_color="#0F172A", border_color="#334155", height=34,
                )
                entry.grid(row=0, column=1, sticky="ew", padx=(0, 6), pady=8)

                def _rename(event=None, old=genre, var=name_var, idx=i):
                    new = var.get().strip()
                    if not new or new == old:
                        return
                    if new.lower() in [g.lower() for g in self.saved_genres if g != old]:
                        messagebox.showwarning("Duplicate", f"'{new}' already exists.", parent=win)
                        var.set(old)
                        return
                    self.saved_genres[idx] = new
                    if old in self.active_genres:
                        pos = self.active_genres.index(old)
                        self.active_genres[pos] = new
                    self._save_library()
                    self.refresh_genre_tags()
                    self.update_output()
                    _rebuild()

                entry.bind("<Return>",   _rename)
                entry.bind("<FocusOut>", _rename)

                # ── Delete button ──────────────────────────────────────
                danger = getattr(self, "settings", {}).get("danger_color", "#7F1D1D")
                ctk.CTkButton(
                    row, text="", image=self.icon_trash,
                    width=30, height=30,
                    fg_color=danger, hover_color="#991B1B",
                    command=lambda g=genre: _delete(g),
                ).grid(row=0, column=2, padx=(0, 8), pady=8)

        def _move(idx: int, direction: int):
            other = idx + direction
            if other < 0 or other >= len(self.saved_genres):
                return
            self.saved_genres[idx], self.saved_genres[other] = (
                self.saved_genres[other], self.saved_genres[idx],
            )
            self._save_library()
            self.refresh_genre_tags()
            _rebuild()

        def _delete(genre: str):
            if not messagebox.askyesno(
                "Confirm Delete", f"Remove '{genre}' from your genre library?", parent=win
            ):
                return
            if genre in self.saved_genres:
                self.saved_genres.remove(genre)
            if genre in self.active_genres:
                self.active_genres.remove(genre)
            self._save_library()
            self.refresh_genre_tags()
            self.update_output()
            _rebuild()

        _rebuild()
        add_entry.focus()
