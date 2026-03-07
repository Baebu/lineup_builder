"""
Module: roster.py
Purpose: Manages the DJ Roster tab: display, edit, add, and delete DJ cards.
Dependencies: re, dearpygui, theme
Architecture: Mixin for App class. Uses DPG child_window "dj_roster_scroll".
"""

import re

import dearpygui.dearpygui as dpg

from .fonts import BODY, ERROR, HEADER, LABEL, MUTED, SUCCESS, Icon, bind_icon_font, styled_text
from .widgets import add_icon_button


class RosterMixin:

    def refresh_dj_roster_ui(self):
        if not dpg.does_item_exist("dj_roster_scroll"):
            return
        dpg.delete_item("dj_roster_scroll", children_only=True)
        self.saved_djs.sort(key=lambda d: re.sub(r'[^a-z]', '', (d.get("name") or "").lower()))
        query = self.dj_search_var.get().strip().lower()
        filtered = [(idx, dj) for idx, dj in enumerate(self.saved_djs)
                    if not query or query in dj.get("name", "").lower()]
        if not self.saved_djs:
            styled_text("No DJs saved yet.\nSave a DJ from a slot or press + NEW DJ.",
                         LABEL, parent="dj_roster_scroll")
            return
        if not filtered:
            styled_text("No DJs match your search.",
                         LABEL, parent="dj_roster_scroll")
            return
        for idx, dj in filtered:
            self._build_dj_card("dj_roster_scroll", dj, idx)

    def _build_dj_card(self, parent, dj, idx):
        card_tag = f"dj_card_{idx}"
        if dpg.does_item_exist(card_tag):
            dpg.delete_item(card_tag)
        dj_name = dj.get("name", "Unnamed")
        with dpg.group(tag=card_tag, parent=parent):
            with dpg.drag_payload(drag_data=dj_name, payload_type="DJ_CARD"):
                styled_text(f"+ {dj_name}", HEADER)
            with dpg.table(header_row=False, borders_innerH=False, borders_innerV=False, borders_outerH=False, borders_outerV=False, pad_outerX=False):
                dpg.add_table_column(width_stretch=True)
                dpg.add_table_column(width_fixed=True)
                with dpg.table_row():
                    with dpg.group(horizontal=True):
                        dpg.add_spacer(width=4)
                        _drag_txt = styled_text(Icon.DRAG, MUTED)
                        bind_icon_font(_drag_txt)
                        dpg.add_spacer(width=4)
                        styled_text(dj_name, BODY)
                    with dpg.group(horizontal=True):
                        if dj.get("stream", ""):
                            styled_text("LINK", SUCCESS)
                        else:
                            styled_text("LINK", ERROR)
                        add_icon_button(Icon.EDIT, width=28, height=20, user_data=(dj, idx), callback=lambda s, a, u: self._open_dj_edit_window(u[0], u[1]))
                        add_icon_button(Icon.DELETE, width=28, height=20, is_danger=True, user_data=idx, callback=lambda s, a, u: self._delete_dj_from_roster(u))
                        dpg.add_spacer(width=10)
            dpg.add_separator()

    def _open_dj_edit_window(self, dj, idx):
        win_tag = f"dj_edit_win_{idx}"
        if dpg.does_item_exist(win_tag):
            dpg.delete_item(win_tag)
        with dpg.window(tag=win_tag, label="Edit DJ", modal=True, width=320, no_resize=True,
                        autosize=True, no_scrollbar=True,
                        pos=dpg.get_mouse_pos(local=False)):
            dpg.add_text("NAME")
            name_input = dpg.add_input_text(tag=f"{win_tag}_name", default_value=dj.get("name", ""), width=290)
            dpg.add_text("STREAM LINK")
            stream_input = dpg.add_input_text(tag=f"{win_tag}_stream", default_value=dj.get("stream", ""), width=290,
                                               hint="https://stream.vrcdn.live/live/...")
            exact_check = dpg.add_checkbox(tag=f"{win_tag}_exact", label="Use exact link (skip Quest/PC conversion)",
                                            default_value=bool(dj.get("exact_link", False)))
            err_text = styled_text("", ERROR, show=False)
            with dpg.group(horizontal=True):
                save_data = {
                    "name_input": name_input,
                    "stream_input": stream_input,
                    "exact_check": exact_check,
                    "err_text": err_text,
                    "win_tag": win_tag,
                    "dj": dj,
                }
                def _save(sender, app_data, ud):
                    d = ud
                    name = (dpg.get_value(d["name_input"]) or "").strip()
                    if not name:
                        dpg.show_item(d["err_text"]); dpg.set_value(d["err_text"], "Name is required."); return
                    if name.lower() != d["dj"].get("name", "").lower() and name.lower() in [
                            x.get("name", "").lower() for x in self.saved_djs]:
                        dpg.show_item(d["err_text"]); dpg.set_value(d["err_text"], "Name already exists."); return
                    d["dj"]["name"] = name
                    d["dj"]["stream"] = (dpg.get_value(d["stream_input"]) or "").strip()
                    d["dj"]["exact_link"] = dpg.get_value(d["exact_check"])
                    self._save_library()
                    self.refresh_dj_roster_ui()
                    self._work_queue.put(self._refresh_slot_combos)
                    dpg.delete_item(d["win_tag"])
                save_btn = dpg.add_button(label="Save", width=140, user_data=save_data, callback=_save)
                dpg.bind_item_theme(save_btn, "primary_btn_theme")

    def open_dj_link_import(self):
        win_tag = "dj_link_import_win"
        if dpg.does_item_exist(win_tag):
            dpg.delete_item(win_tag)
        with dpg.window(tag=win_tag, label="Import DJ Links", modal=True,
                        width=480, no_resize=False, no_scrollbar=True,
                        pos=dpg.get_mouse_pos(local=False)):
            styled_text("IMPORT DJ LINKS", HEADER)
            styled_text("Paste one entry per line: raw URL, Name: URL, or **Name** URL",
                         MUTED, wrap=450)
            paste_input = dpg.add_input_text(tag=f"{win_tag}_paste", multiline=True, width=-11, height=120)
            status_text = styled_text("", LABEL, tag=f"{win_tag}_status")
            results_group = dpg.add_group(tag=f"{win_tag}_results")
            result_data = []

            def _parse(s, a, _pi=paste_input, _st=status_text, _rg=results_group,
                       _rd=result_data):
                dpg.delete_item(_rg, children_only=True)
                _rd.clear()
                raw = (dpg.get_value(_pi) or "").strip()
                if not raw:
                    dpg.set_value(_st, "Paste something first."); return
                entries = self._parse_dj_links(raw)
                if not entries:
                    dpg.set_value(_st, "No URLs detected."); return
                dpg.set_value(_st, f"{len(entries)} link(s) detected.")
                for det_name, url in entries:
                    short_url = url[:50] + "..." if len(url) > 50 else url
                    with dpg.group(parent=_rg, horizontal=True):
                        styled_text(short_url[:45], MUTED)
                        ni = dpg.add_input_text(default_value=det_name, width=120, hint="DJ name")
                        _rd.append({"url": url, "name_input": ni})

            def _import(s, a, _rd=result_data, _st=status_text, _wt=win_tag):
                if not _rd:
                    dpg.set_value(_st, "Parse first."); return
                for row in _rd:
                    name = dpg.get_value(row["name_input"]).strip()
                    url = row["url"]
                    if not name:
                        continue
                    existing = next((d for d in self.saved_djs
                                     if d.get("name", "").lower() == name.lower()), None)
                    if existing:
                        existing["stream"] = url
                    else:
                        self.saved_djs.append({"name": name, "stream": url, "exact_link": False})
                self._save_library()
                self.refresh_dj_roster_ui()
                self._work_queue.put(self._refresh_slot_combos)
                dpg.delete_item(_wt)

            with dpg.group(horizontal=True):
                dpg.add_button(label="Parse", width=140, callback=_parse)
                import_btn = dpg.add_button(label="Import", width=140, callback=_import)
                dpg.bind_item_theme(import_btn, "primary_btn_theme")

    @staticmethod
    def _parse_dj_links(text: str) -> list:
        import re as _re
        url_re = _re.compile(r'https?://[^\s<>"]+', _re.IGNORECASE)
        results = []
        for line in text.splitlines():
            s = line.strip()
            if not s:
                continue
            s_clean = _re.sub(r'<(https?://[^>]+)>', r'\1', s)
            urls_in_line = url_re.findall(s_clean)
            if not urls_in_line:
                continue
            url = urls_in_line[0]
            name_fragment = url_re.sub("", s_clean).strip().rstrip(":—-– ").strip()
            name_fragment = _re.sub(r'\*\*(.+?)\*\*', r'\1', name_fragment)
            name_fragment = _re.sub(r'\*([^*]+?)\*', r'\1', name_fragment)
            name_fragment = _re.sub(r'^[:\-–—]+\s*', '', name_fragment).strip()
            name_fragment = _re.sub(r'\s*[:\-–—]+$', '', name_fragment).strip()
            if name_fragment:
                det_name = name_fragment
            else:
                path_parts = [p for p in url.rstrip('/').split('/') if p]
                raw_slug = path_parts[-1] if path_parts else ""
                raw_slug = raw_slug.split('?')[0]
                det_name = raw_slug.replace('_', ' ').replace('-', ' ').title()
            results.append((det_name, url))
        return results

    def _delete_dj_from_roster(self, idx):
        if idx < len(self.saved_djs):
            win_tag = f"confirm_del_dj_{idx}"
            if dpg.does_item_exist(win_tag):
                dpg.delete_item(win_tag)
            name = self.saved_djs[idx].get("name", "this DJ")
            with dpg.window(tag=win_tag, label="Confirm Delete", modal=True,
                            autosize=True, no_resize=True, no_scrollbar=True,
                            pos=dpg.get_mouse_pos(local=False)):
                dpg.add_text(f"Remove '{name}' from the roster?")
                with dpg.group(horizontal=True):
                    def _confirm(s, a, u):
                        i, wt = u
                        self.saved_djs.pop(i)
                        self._save_library()
                        self.refresh_dj_roster_ui()
                        self._work_queue.put(self._refresh_slot_combos)
                        dpg.delete_item(wt)
                    dpg.add_button(label="Yes", width=140, user_data=(idx, win_tag), callback=_confirm)
                    dpg.bind_item_theme(dpg.last_item(), self._danger_btn_theme)
                    dpg.add_button(label="No", width=140, user_data=win_tag,
                                   callback=lambda s, a, u: dpg.delete_item(u))

    def add_new_dj_to_roster(self):
        win_tag = "new_dj_win"
        if dpg.does_item_exist(win_tag):
            dpg.delete_item(win_tag)
        with dpg.window(tag=win_tag, label="New DJ", modal=True,
                        width=320, no_resize=True, autosize=True, no_scrollbar=True,
                        pos=dpg.get_mouse_pos(local=False)):
            dpg.add_text("NAME")
            name_input = dpg.add_input_text(tag=f"{win_tag}_name", width=290)
            dpg.add_text("STREAM LINK")
            stream_input = dpg.add_input_text(
                tag=f"{win_tag}_stream", width=290, hint="https://stream.vrcdn.live/live/...")
            exact_check = dpg.add_checkbox(
                tag=f"{win_tag}_exact", label="Use exact link (skip Quest/PC conversion)")
            err_text = styled_text("", ERROR, show=False)
            with dpg.group(horizontal=True):
                def _save(s, a, _ni=name_input, _si=stream_input, _ec=exact_check,
                          _er=err_text, _wt=win_tag):
                    name = (dpg.get_value(_ni) or "").strip()
                    if not name:
                        dpg.show_item(_er); dpg.set_value(_er, "Name is required."); return
                    if name.lower() in [d.get("name", "").lower() for d in self.saved_djs]:
                        dpg.show_item(_er); dpg.set_value(_er, "Name already exists."); return
                    self.saved_djs.append({
                        "name": name,
                        "stream": (dpg.get_value(_si) or "").strip(),
                        "exact_link": dpg.get_value(_ec),
                    })
                    self._save_library()
                    self.refresh_dj_roster_ui()
                    self._work_queue.put(self._refresh_slot_combos)
                    dpg.delete_item(_wt)
                save_btn = dpg.add_button(label="Save", width=140, callback=_save)
                dpg.bind_item_theme(save_btn, "primary_btn_theme")

