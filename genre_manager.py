import customtkinter as ctk
from tkinter import messagebox


class GenreMixin:
    """Manages active-genre tags and the saved-genres panel."""

    def add_genre_from_entry(self, event=None):
        val = self.genre_entry_var.get().strip()
        if val:
            self.add_genre(val)
            self.genre_entry_var.set("")

    def _toggle_genre_panel(self):
        if self._genre_panel_expanded:
            self._genre_saved_panel.pack_forget()
            self.genre_arrow_btn.configure(image=self.icon_chevron_down)
            self._genre_panel_expanded = False
        else:
            self._genre_saved_panel.pack(fill="x", pady=(4, 0), before=self.genre_tags_frame)
            self.genre_arrow_btn.configure(image=self.icon_chevron_up)
            self._genre_panel_expanded = True

    def refresh_genre_saved_panel(self):
        for w in self._genre_saved_panel.winfo_children():
            w.destroy()
        if not self.saved_genres:
            ctk.CTkLabel(
                self._genre_saved_panel, text="No saved genres yet.",
                text_color="#94A3B8", font=("Arial", 11)
            ).pack(padx=10, pady=8)
            return
        for genre in self.saved_genres:
            row = ctk.CTkFrame(self._genre_saved_panel, fg_color="transparent")
            row.pack(fill="x", padx=8, pady=3)
            ctk.CTkLabel(row, text=genre, font=("Arial", 12), text_color="#CBD5E1").pack(side="left")
            ctk.CTkButton(
                row, text="Add", width=54, height=28,
                fg_color="#3730A3", hover_color="#4338CA", font=("Arial", 10, "bold"),
                command=lambda g=genre: self.add_genre(g)
            ).pack(side="right")

    def add_genre(self, genre):
        genre = genre.strip()
        if genre.lower() not in [g.lower() for g in self.active_genres]:
            self.active_genres.append(genre)

        if genre.lower() not in [g.lower() for g in self.saved_genres]:
            self.saved_genres.append(genre)
            self._save_library()
            self.refresh_genre_saved_panel()

        self.refresh_genre_tags()
        self.update_output()

    def delete_saved_genre(self):
        val = self.genre_entry_var.get().strip()
        if val and val in self.saved_genres:
            if messagebox.askyesno("Confirm Delete", f"Remove '{val}' from saved genres?"):
                self.saved_genres.remove(val)
                self._save_library()
                self.genre_entry_var.set("")
                self.refresh_genre_saved_panel()

    def remove_genre(self, genre):
        if genre in self.active_genres:
            self.active_genres.remove(genre)
        self.refresh_genre_tags()
        self.update_output()

    def refresh_genre_tags(self):
        for widget in self.genre_tags_frame.winfo_children():
            widget.destroy()

        current_row = 0
        current_col = 0
        for genre in self.active_genres:
            btn = ctk.CTkButton(
                self.genre_tags_frame, text=f"{genre} ✕",
                command=lambda g=genre: self.remove_genre(g),
                fg_color="#3730A3", hover_color="#DC2626",
                height=28, font=("Arial", 11, "bold"), width=50
            )
            btn.grid(row=current_row, column=current_col, padx=2, pady=2)
            current_col += 1
            if current_col > 3:  # max 4 per row
                current_col = 0
                current_row += 1
