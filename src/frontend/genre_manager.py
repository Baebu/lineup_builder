import dearpygui.dearpygui as dpg

from .fonts import HEADER, MUTED, styled_text


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
                            autosize=True, no_resize=True, no_scrollbar=True,
                            pos=dpg.get_mouse_pos(local=False)):
                dpg.add_text(f"Remove '{val}' from saved genres?")
                with dpg.group(horizontal=True):
                    dpg.add_button(label="Yes", width=140, callback=lambda s, a, u=None: _do_del())
                    dpg.bind_item_theme(dpg.last_item(), self._danger_btn_theme)
                    dpg.add_button(label="No", width=140, user_data=win_tag,
                                   callback=lambda s, a, u: dpg.delete_item(u))

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
            styled_text("Type a genre above and press Enter to add it.",
                         MUTED, parent="genre_tags_frame")
            return
        query = self.genre_search_var.get().strip().lower() if hasattr(self, 'genre_search_var') else ""
        filtered = [g for g in self.saved_genres if not query or query in g.lower()]
        if not filtered and query:
            styled_text("No genres match your search.",
                         MUTED, parent="genre_tags_frame")
            return

        active_lower = {g.lower() for g in self.active_genres}
        # Intelligent greedy bin-packing: pack as many genre buttons per row to minimize empty space
        container_w = 0
        if dpg.does_item_exist("genre_tags_frame"):
            container_w = dpg.get_item_rect_size("genre_tags_frame")[0]
        if container_w <= 0:
            container_w = dpg.get_item_width("genre_tags_frame")
        if container_w is None or container_w <= 0:
            container_w = self._LEFT_DEFAULT if hasattr(self, '_LEFT_DEFAULT') else 300
        
        # Compensate for padding/scrollbars inside the child window
        usable_w = max(100, container_w - 20)

        frame_pad_x = 6   # mvStyleVar_FramePadding X (from theme)
        item_gap = 6       # mvStyleVar_ItemSpacing X (from theme)

        # Precompute widths for all buttons
        items = []
        for genre in filtered:
            text_size = dpg.get_text_size(genre)
            btn_w = (text_size[0] if text_size else len(genre) * 8) + 2 * frame_pad_x
            items.append((genre, btn_w))

        # Sort items descending by width for best-fit bin packing
        items.sort(key=lambda x: x[1], reverse=True)

        rows = []  # list of tuples: (used_width, [list of (genre, btn_w)])
        
        for item in items:
            genre, btn_w = item
            placed = False
            # Find the first row that can fit this item
            for i, row in enumerate(rows):
                used_w, items_in_row = row
                # The extra cost is the item width + an item gap
                cost = btn_w
                if len(items_in_row) > 0:
                    cost += item_gap
                
                if used_w + cost <= usable_w:
                    rows[i] = (used_w + cost, items_in_row + [item])
                    placed = True
                    break
            
            # If it doesn't fit in any existing row, create a new row
            if not placed:
                rows.append((btn_w, [item]))

        # Render the grouped rows
        for used_w, items_in_row in rows:
            row_group = dpg.add_group(horizontal=True, parent="genre_tags_frame")
            for genre, btn_w in items_in_row:
                is_active = genre.lower() in active_lower
                btn = dpg.add_button(
                    label=genre, parent=row_group, height=20,
                    user_data=(genre, is_active),
                    callback=lambda s, a, u: self._toggle_genre(u[0], u[1]),
                )
                if is_active:
                    dpg.bind_item_theme(btn, "success_btn_theme")

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
                styled_text("No genres saved yet.", MUTED, parent=_wg)
                return
            for i, genre in enumerate(self.saved_genres):
                with dpg.group(parent=_wg, horizontal=True):
                    dpg.add_text(genre)
                    dpg.add_button(label="^", small=True, user_data=i,
                                   callback=lambda s, a, u: _move(u, -1))
                    dpg.add_button(label="v", small=True, user_data=i,
                                   callback=lambda s, a, u: _move(u, 1))
                    dpg.add_button(label="Del", small=True, user_data=genre,
                                   callback=lambda s, a, u: _delete(u))

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
            styled_text("GENRE LIBRARY", HEADER)
            new_input = dpg.add_input_text(hint="New genre name...", width=-11)

            def _add_new(s, a, _ni=new_input):
                val = dpg.get_value(_ni).strip()
                if not val:
                    return
                dpg.set_value(_ni, "")
                self.add_genre(val)
                _rebuild()

            add_btn = dpg.add_button(label="+ Add", callback=_add_new, width=-1)
            dpg.bind_item_theme(add_btn, "primary_btn_theme")
            dpg.add_separator()
            dpg.add_group(tag="genre_editor_list")
            _rebuild()
