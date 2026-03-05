"""
Module: dj_roster.py
Purpose: Manages the DJ Roster tab: display, edit, add, and delete DJ cards.
Dependencies: re, dearpygui, theme
Architecture: Mixin for App class. Uses DPG child_window "dj_roster_scroll".
"""

import re
import dearpygui.dearpygui as dpg

from . import theme as T
from .fonts import Icon


class DJRosterMixin:

    def refresh_dj_roster_ui(self):
        if not dpg.does_item_exist("dj_roster_scroll"):
            return
        dpg.delete_item("dj_roster_scroll", children_only=True)
        self.saved_djs.sort(key=lambda d: re.sub(r'[^a-z]', '', (d.get("name") or "").lower()))
        query = self.dj_search_var.get().strip().lower()
        filtered = [(idx, dj) for idx, dj in enumerate(self.saved_djs)
                    if not query or query in dj.get("name", "").lower()]
        if not self.saved_djs:
            dpg.add_text("No DJs saved yet.\nSave a DJ from a slot or press + NEW DJ.",
                         parent="dj_roster_scroll", color=T.DPG_TEXT_SECONDARY)
            return
        if not filtered:
            dpg.add_text("No DJs match your search.",
                         parent="dj_roster_scroll", color=T.DPG_TEXT_SECONDARY)
            return
        for idx, dj in filtered:
            self._build_dj_card("dj_roster_scroll", dj, idx)

    def _build_dj_card(self, parent, dj, idx):
        card_tag = f"dj_card_{idx}"
        if dpg.does_item_exist(card_tag):
            dpg.delete_item(card_tag)
        with dpg.group(tag=card_tag, parent=parent):
            with dpg.group(horizontal=True):
                dpg.add_text(dj.get("name", "Unnamed"), color=T.DPG_TEXT_PRIMARY)
                dpg.add_button(label=Icon.ADD, small=True,
                               callback=lambda s, a, n=dj.get("name", ""): self._add_dj_to_lineup(n))
                dpg.add_button(label=Icon.EDIT, small=True,
                               callback=lambda s, a, d=dj, i=idx: self._open_dj_edit_window(d, i))
                dpg.add_button(label=Icon.DELETE, small=True,
                               callback=lambda s, a, i=idx: self._delete_dj_from_roster(i))
            stream = dj.get("stream", "")
            if stream:
                exact = dj.get("exact_link", False)
                prefix = "Exact: " if exact else "Stream: "
                short = stream[:40] + "..." if len(stream) > 40 else stream
                dpg.add_text(f"{prefix}{short}", color=T.DPG_TEXT_MUTED)
            else:
                dpg.add_text("No stream link set", color=T.DPG_TEXT_MUTED)
            dpg.add_separator()

    def _open_dj_edit_window(self, dj, idx):
        win_tag = f"dj_edit_win_{idx}"
        if dpg.does_item_exist(win_tag):
            dpg.delete_item(win_tag)
        with dpg.window(tag=win_tag, label="Edit DJ", modal=True, width=350, height=260, no_resize=True):
            dpg.add_text("NAME")
            name_input = dpg.add_input_text(default_value=dj.get("name", ""), width=-1)
            dpg.add_text("STREAM LINK")
            stream_input = dpg.add_input_text(default_value=dj.get("stream", ""), width=-1,
                                               hint="https://stream.vrcdn.live/live/...")
            exact_check = dpg.add_checkbox(label="Use exact link (skip Quest/PC conversion)",
                                            default_value=bool(dj.get("exact_link", False)))
            err_text = dpg.add_text("", color=T.DPG_ERROR, show=False)
            with dpg.group(horizontal=True):
                def _save(sender, app_data, ud, _n=name_input, _s=stream_input, _e=exact_check,
                          _er=err_text, _wt=win_tag, _dj=dj):
                    name = dpg.get_value(_n).strip()
                    if not name:
                        dpg.show_item(_er); dpg.set_value(_er, "Name is required."); return
                    if name.lower() != _dj.get("name", "").lower() and name.lower() in [
                            d.get("name", "").lower() for d in self.saved_djs]:
                        dpg.show_item(_er); dpg.set_value(_er, "Name already exists."); return
                    _dj["name"] = name
                    _dj["stream"] = dpg.get_value(_s).strip()
                    _dj["exact_link"] = dpg.get_value(_e)
                    self._save_library()
                    self.refresh_dj_roster_ui()
                    self._work_queue.put(self._refresh_slot_combos)
                    dpg.delete_item(_wt)
                dpg.add_button(label=Icon.SAVE + " Save", callback=_save)
                dpg.add_button(label=Icon.CLOSE + " Cancel",
                               callback=lambda s, a, wt=win_tag: dpg.delete_item(wt))

    def open_dj_link_import(self):
        win_tag = "dj_link_import_win"
        if dpg.does_item_exist(win_tag):
            dpg.delete_item(win_tag)
        with dpg.window(tag=win_tag, label="Import DJ Links", modal=True,
                        width=560, height=400, no_resize=False):
            dpg.add_text("IMPORT DJ LINKS", color=T.DPG_ACCENT)
            dpg.add_text("Paste one entry per line: raw URL, Name: URL, or **Name** URL",
                         color=T.DPG_TEXT_MUTED, wrap=540)
            paste_input = dpg.add_input_text(multiline=True, width=-1, height=120)
            status_text = dpg.add_text("", color=T.DPG_TEXT_SECONDARY)
            results_group = dpg.add_group()
            result_data = []

            def _parse(s, a, _pi=paste_input, _st=status_text, _rg=results_group,
                       _rd=result_data):
                dpg.delete_item(_rg, children_only=True)
                _rd.clear()
                raw = dpg.get_value(_pi).strip()
                if not raw:
                    dpg.set_value(_st, "Paste something first."); return
                entries = self._parse_dj_links(raw)
                if not entries:
                    dpg.set_value(_st, "No URLs detected."); return
                dpg.set_value(_st, f"{len(entries)} link(s) detected.")
                for det_name, url in entries:
                    short_url = url[:50] + "..." if len(url) > 50 else url
                    with dpg.group(parent=_rg, horizontal=True):
                        dpg.add_text(short_url[:45], color=T.DPG_TEXT_MUTED)
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
                dpg.add_button(label=Icon.SEARCH + " Parse", callback=_parse)
                dpg.add_button(label=Icon.DOWNLOAD + " Import", callback=_import)
                dpg.add_button(label=Icon.CLOSE + " Cancel",
                               callback=lambda s, a, wt=win_tag: dpg.delete_item(wt))

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
                            width=300, height=100, no_resize=True):
                dpg.add_text(f"Remove '{name}' from the roster?")
                with dpg.group(horizontal=True):
                    def _confirm(s, a, i=idx, wt=win_tag):
                        self.saved_djs.pop(i)
                        self._save_library()
                        self.refresh_dj_roster_ui()
                        self._work_queue.put(self._refresh_slot_combos)
                        dpg.delete_item(wt)
                    dpg.add_button(label=Icon.CHECK + " Yes", callback=_confirm)
                    dpg.add_button(label=Icon.CLOSE + " No",
                                   callback=lambda s, a, wt=win_tag: dpg.delete_item(wt))

    def add_new_dj_to_roster(self):
        win_tag = "new_dj_win"
        if dpg.does_item_exist(win_tag):
            dpg.delete_item(win_tag)
        with dpg.window(tag=win_tag, label="New DJ", modal=True,
                        width=380, height=220, no_resize=True):
            dpg.add_text("NAME")
            name_input = dpg.add_input_text(width=-1)
            dpg.add_text("STREAM LINK")
            stream_input = dpg.add_input_text(
                width=-1, hint="https://stream.vrcdn.live/live/...")
            exact_check = dpg.add_checkbox(
                label="Use exact link (skip Quest/PC conversion)")
            err_text = dpg.add_text("", color=T.DPG_ERROR, show=False)
            with dpg.group(horizontal=True):
                def _save(s, a, _ni=name_input, _si=stream_input, _ec=exact_check,
                          _er=err_text, _wt=win_tag):
                    name = dpg.get_value(_ni).strip()
                    if not name:
                        dpg.show_item(_er); dpg.set_value(_er, "Name is required."); return
                    if name.lower() in [d.get("name", "").lower() for d in self.saved_djs]:
                        dpg.show_item(_er); dpg.set_value(_er, "Name already exists."); return
                    self.saved_djs.append({
                        "name": name,
                        "stream": dpg.get_value(_si).strip(),
                        "exact_link": dpg.get_value(_ec),
                    })
                    self._save_library()
                    self.refresh_dj_roster_ui()
                    self._work_queue.put(self._refresh_slot_combos)
                    dpg.delete_item(_wt)
                dpg.add_button(label="💾 Save", callback=_save)
                dpg.add_button(label="✕ Cancel",
                               callback=lambda s, a, wt=win_tag: dpg.delete_item(wt))

