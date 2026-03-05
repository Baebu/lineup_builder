import dearpygui.dearpygui as dpg

from . import theme as T
from .fonts import Icon


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
            win_tag = "del_genre_confirm"
            if dpg.does_item_exist(win_tag):
                dpg.delete_item(win_tag)
            def _do_del(_g=val, _wt=win_tag):
                self.saved_genres.remove(_g)
                if _g in self.active_genres:
                    self.active_genres.remove(_g)
                self._save_library()
                self.genre_entry_var.set("")
                if dpg.does_item_exist("genre_entry"):
                    dpg.set_value("genre_entry", "")
                self.refresh_genre_tags()
                self.update_output()
                if dpg.does_item_exist(_wt):
                    dpg.delete_item(_wt)
            with dpg.window(tag=win_tag, label="Confirm Delete", modal=True,
                            width=280, height=80, no_resize=True):
                dpg.add_text(f"Remove '{val}' from saved genres?")
                with dpg.group(horizontal=True):
                    dpg.add_button(label=Icon.CHECK + " Yes", callback=lambda s, a: _do_del())
                    dpg.add_button(label=Icon.CLOSE + " No", callback=lambda s, a, wt=win_tag: dpg.delete_item(wt))

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
        if not dpg.does_item_exist("genre_tags_frame"):
            return
        dpg.delete_item("genre_tags_frame", children_only=True)
        if not self.saved_genres:
            dpg.add_text("Type a genre above and press Enter to add it.",
                         parent="genre_tags_frame", color=T.DPG_TEXT_MUTED)
            return
        active_lower = {g.lower() for g in self.active_genres}
        for genre in self.saved_genres:
            is_active = genre.lower() in active_lower
            dpg.add_button(
                label=genre, parent="genre_tags_frame", small=True,
                callback=lambda s, a, g=genre, ia=is_active: self._toggle_genre(g, ia),
            )

    # ── Genre editor popout ───────────────────────────────────────────────

    def open_genre_editor(self):
        """Open a floating window for managing the saved-genre library."""
        win_tag = "genre_editor_win"
        if dpg.does_item_exist(win_tag):
            dpg.focus_item(win_tag)
            return

        def _rebuild(_wg=None):
            if _wg is None:
                _wg = "genre_editor_list"
            if not dpg.does_item_exist(_wg):
                return
            dpg.delete_item(_wg, children_only=True)
            if not self.saved_genres:
                dpg.add_text("No genres saved yet.", parent=_wg, color=T.DPG_TEXT_MUTED)
                return
            for i, genre in enumerate(self.saved_genres):
                with dpg.group(parent=_wg, horizontal=True):
                    dpg.add_text(genre)
                    dpg.add_button(label=Icon.UP, small=True,
                                   callback=lambda s, a, idx=i: _move(idx, -1))
                    dpg.add_button(label=Icon.DOWN, small=True,
                                   callback=lambda s, a, idx=i: _move(idx, 1))
                    dpg.add_button(label=Icon.DELETE, small=True,
                                   callback=lambda s, a, g=genre: _delete(g))

        def _move(idx, delta):
            ni = idx + delta
            if 0 <= ni < len(self.saved_genres):
                self.saved_genres[idx], self.saved_genres[ni] = (
                    self.saved_genres[ni], self.saved_genres[idx])
                self._save_library()
                self.refresh_genre_tags()
                _rebuild()

        def _delete(genre):
            if genre in self.saved_genres:
                self.saved_genres.remove(genre)
            if genre in self.active_genres:
                self.active_genres.remove(genre)
            self._save_library()
            self.refresh_genre_tags()
            self.update_output()
            _rebuild()

        with dpg.window(tag=win_tag, label="Edit Genres", width=340, height=480):
            dpg.add_text("GENRE LIBRARY", color=T.DPG_ACCENT)
            new_input = dpg.add_input_text(hint="New genre name...", width=-1)

            def _add_new(s, a, _ni=new_input):
                val = dpg.get_value(_ni).strip()
                if not val:
                    return
                dpg.set_value(_ni, "")
                self.add_genre(val)
                _rebuild()

            dpg.add_button(label=Icon.ADD + " Add", callback=_add_new, width=-1)
            dpg.add_separator()
            dpg.add_group(tag="genre_editor_list")
            _rebuild()
