"""
Module: dj_roster.py
Purpose: Manages the DJ Roster tab: display, edit, add, and delete DJ cards.
Dependencies: re, customtkinter, tkinter.messagebox, theme
Architecture: Mixin for App class. Emits events/updates model via DataMixin.
"""

import re
import customtkinter as ctk
from tkinter import messagebox
from . import theme as T


class DJRosterMixin:
    """Manages the DJ Roster tab: display, edit, add, and delete DJ cards."""

    def refresh_dj_roster_ui(self):
        # Keep roster sorted alphabetically
        self.saved_djs.sort(key=lambda d: re.sub(r'[^a-z]', '', (d.get("name") or "").lower()))
        query = self.dj_search_var.get().strip().lower()
        filtered =[
            (idx, dj) for idx, dj in enumerate(self.saved_djs)
            if not query or query in dj.get("name", "").lower()
        ]
        
        for widget in self.dj_roster_scroll.winfo_children():
            widget.destroy()
            
        if not self.saved_djs:
            ctk.CTkLabel(
                self.dj_roster_scroll,
                text="No DJs saved yet.\nSave a DJ from a slot or press + NEW DJ.",
                text_color=T.TEXT_SECONDARY, justify="center"
            ).pack(pady=20)
            return
            
        if not filtered:
            ctk.CTkLabel(
                self.dj_roster_scroll,
                text="No DJs match your search.",
                text_color=T.TEXT_SECONDARY, justify="center"
            ).pack(pady=20)
            return
            
        for idx, dj in filtered:
            self._build_dj_card(self.dj_roster_scroll, dj, idx)

    def _build_dj_card(self, parent, dj, idx):
        card = ctk.CTkFrame(parent, **T.CARD)
        card.pack(fill="x", padx=T.SCROLL_PAD_X, pady=(0, 6))

        # ── Header row ──
        header = ctk.CTkFrame(card, fg_color="transparent", cursor="hand2")
        header.pack(fill="x", padx=T.CARD_PAD_INNER, pady=8)

        grip_btn = ctk.CTkButton(
            header, text="", image=self.icon_grip,
            width=24, height=T.WIDGET_H_SM, cursor="fleur",
            fg_color="transparent", hover_color=T.BORDER
        )
        grip_btn.pack(side="left", padx=(0, 6))

        # ── Info Column (Name + Stream Link) ──
        info_col = ctk.CTkFrame(header, fg_color="transparent", cursor="hand2")
        info_col.pack(side="left", fill="x", expand=True, padx=(4, 10))

        name_lbl = ctk.CTkLabel(
            info_col, text=dj.get("name", "Unnamed DJ"),
            font=T.FONT_VALUE, text_color=T.TEXT_PRIMARY, cursor="hand2"
        )
        name_lbl.pack(anchor="w")

        stream = dj.get("stream", "")
        if stream:
            exact = dj.get("exact_link", False)
            prefix = "🔗 Exact: " if exact else "🎙 "
            short_stream = stream if len(stream) <= 38 else stream[:35] + "..."
            stream_lbl = ctk.CTkLabel(
                info_col, text=f"{prefix}{short_stream}",
                font=T.FONT_TINY, text_color=T.TEXT_MUTED, cursor="hand2"
            )
            stream_lbl.pack(anchor="w", pady=(0, 2))
        else:
            stream_lbl = ctk.CTkLabel(
                info_col, text="No stream link set",
                font=T.FONT_TINY, text_color=T.TEXT_MUTED, cursor="hand2"
            )
            stream_lbl.pack(anchor="w", pady=(0, 2))

        # ── Action Buttons ──
        edit_btn = ctk.CTkButton(
            header, text="", image=self.icon_edit,
            width=T.WIDGET_H_SM, height=T.WIDGET_H_SM, **T.BTN_SECONDARY,
            command=lambda: self._open_dj_edit_window(dj, idx, name_lbl, edit_btn)
        )
        edit_btn.pack(side="right", padx=(0, 4))

        del_btn = ctk.CTkButton(
            header, text="", image=self.icon_trash, width=T.WIDGET_H_SM, height=T.WIDGET_H_SM,
            **T.BTN_DANGER,
            command=lambda i=idx: self._delete_dj_from_roster(i)
        )
        del_btn.pack(side="right", padx=(0, 4))

        # Drag-and-drop: Bind to grip AND the entire info column for easier grabbing
        for w in (grip_btn, info_col, name_lbl, stream_lbl):
            w.bind("<B1-Motion>",       lambda e, n=dj.get("name", ""): self._on_dj_drag(e, n))
            w.bind("<ButtonRelease-1>", lambda e, n=dj.get("name", ""): self._end_dj_drag(e, n))

    def _open_dj_edit_window(self, dj, idx, name_label, button):
        """Open a pop-out window positioned near the edit button."""
        window_key = f"dj_edit_{idx}"
        cur_win = getattr(self, window_key, None)
        if cur_win and cur_win.winfo_exists():
            cur_win.destroy()
            return

        popup = ctk.CTkToplevel(self)
        setattr(self, window_key, popup)
        popup.title("")
        popup.geometry("320x240")
        popup.resizable(False, False)
        popup.configure(fg_color=T.CARD_BG, border_color=T.BORDER, border_width=T.BORDER_W)
        popup.overrideredirect(True)
        popup.attributes("-topmost", True)

        def _on_focus_out(event):
            new_focus = self.focus_get()
            if new_focus != popup and (new_focus is None or not str(new_focus).startswith(str(popup))):
                if new_focus == button:
                    return
                popup.destroy()

        popup.bind("<FocusOut>", _on_focus_out)

        self.update_idletasks()
        button_x = button.winfo_rootx()
        button_y = button.winfo_rooty()
        button_width = button.winfo_width()
        button_height = button.winfo_height()

        popup_x = button_x + button_width + 5
        popup_y = button_y

        screen_width = self.winfo_screenwidth()
        if popup_x + 320 > screen_width:
            popup_x = button_x - 320 - 5

        screen_height = self.winfo_screenheight()
        if popup_y + 240 > screen_height:
            popup_y = button_y + button_height - 240

        popup.geometry(f"320x240+{popup_x}+{popup_y}")

        border_frame = ctk.CTkFrame(popup, fg_color=T.CARD_BG, border_width=2, border_color=T.BORDER)
        border_frame.pack(fill="both", expand=True)

        content = ctk.CTkFrame(border_frame, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=15, pady=12)
        content.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(content, text="NAME", font=T.FONT_SMALL_BOLD, text_color=T.TEXT_SECONDARY).grid(row=0, column=0, sticky="w", pady=(0, 2))
        name_var = ctk.StringVar(value=dj.get("name", ""))
        name_entry = ctk.CTkEntry(content, textvariable=name_var, height=T.WIDGET_H_XS,
                                   fg_color=T.PANEL_BG, border_color=T.BORDER)
        name_entry.grid(row=1, column=0, sticky="ew", pady=(0, 8))

        ctk.CTkLabel(content, text="🎙  STREAM LINK", font=T.FONT_SMALL_BOLD, text_color=T.TEXT_SECONDARY).grid(row=2, column=0, sticky="w", pady=(0, 2))
        stream_var = ctk.StringVar(value=dj.get("stream", ""))
        ctk.CTkEntry(
            content, textvariable=stream_var,
            placeholder_text="https://stream.vrcdn.live/live/...",
            height=T.WIDGET_H_XS, fg_color=T.PANEL_BG, border_color=T.BORDER
        ).grid(row=3, column=0, sticky="ew", pady=(0, 6))

        exact_var = ctk.BooleanVar(value=bool(dj.get("exact_link", False)))
        ctk.CTkCheckBox(
            content, text="Use exact link (skip Quest/PC conversion)",
            variable=exact_var,
            font=T.FONT_SMALL, text_color=T.TEXT_SECONDARY,
            fg_color=T.ACCENT, hover_color=T.PRIMARY,
            border_color=T.BORDER, checkmark_color=T.WHITE
        ).grid(row=4, column=0, sticky="w", pady=(0, 8))

        btn_row = ctk.CTkFrame(content, fg_color="transparent")
        btn_row.grid(row=5, column=0, sticky="e")

        def _save():
            name = name_var.get().strip()
            if not name:
                name_entry.configure(border_color=T.ERROR)
                return
            if name.lower() != dj.get("name", "").lower() and name.lower() in[d.get("name", "").lower() for d in self.saved_djs]:
                name_entry.configure(border_color=T.ERROR)
                ctk.CTkLabel(content, text="Name already exists.",
                             font=T.FONT_SMALL, text_color=T.ERROR).grid(row=6, column=0, sticky="w")
                return

            old_name = dj.get("name", "")
            dj["name"] = name
            dj["stream"] = stream_var.get().strip()
            dj["exact_link"] = exact_var.get()

            self._save_library()
            self.refresh_dj_roster_ui()
            self.after(0, self._refresh_slot_combos)
            
            for slot in self.slots:
                if slot.name_var.get().strip() in (old_name, name):
                    slot.update_dj_info()
            popup.destroy()

        def _cancel():
            popup.destroy()

        ctk.CTkButton(
            btn_row, text="Cancel", width=70, height=T.WIDGET_H_XS,
            **T.BTN_SECONDARY, font=T.FONT_SMALL_BOLD,
            command=_cancel
        ).pack(side="left", padx=(0, 6))
        ctk.CTkButton(
            btn_row, text="Save", width=60, height=T.WIDGET_H_XS,
            **T.BTN_SUCCESS, font=T.FONT_SMALL_BOLD,
            command=_save
        ).pack(side="left")

        popup.bind("<Return>", lambda e: _save())
        popup.bind("<Escape>", lambda e: _cancel())
        name_entry.focus_set()
        popup.lift()

    def open_dj_link_import(self):
        """Popup: paste links → auto-detect name → create or assign to DJ."""
        popup = ctk.CTkToplevel(self)
        popup.title("Import DJ Links")
        popup.geometry("540x580")
        popup.resizable(True, True)
        popup.configure(fg_color=T.CARD_BG)
        popup.grab_set()
        popup.focus_force()

        self.update_idletasks()
        x = self.winfo_x() + (self.winfo_width()  - 540) // 2
        y = self.winfo_y() + (self.winfo_height() - 580) // 2
        popup.geometry(f"540x580+{x}+{y}")

        outer = ctk.CTkFrame(popup, fg_color="transparent")
        outer.pack(fill="both", expand=True, padx=20, pady=16)
        outer.grid_columnconfigure(0, weight=1)
        outer.grid_rowconfigure(2, weight=1)

        ctk.CTkLabel(
            outer, text="IMPORT DJ LINKS",
            font=T.FONT_BODY_BOLD, text_color=T.ACCENT,
        ).grid(row=0, column=0, sticky="w", pady=(0, 2))
        ctk.CTkLabel(
            outer,
            text="Paste one entry per line. Supported:\n"
                 "  • Raw URL        https://stream.vrcdn.live/live/djname\n"
                 "  • Name + URL     DJ Name: https://...  or  DJ Name — https://...\n"
                 "  • Bold + URL     **DJ Name** https://...",
            font=T.FONT_SMALL, text_color=T.TEXT_MUTED, justify="left",
        ).grid(row=1, column=0, sticky="w", pady=(0, 6))

        paste_box = ctk.CTkTextbox(
            outer, fg_color=T.PANEL_BG, text_color=T.TEXT_PRIMARY,
            font=("Consolas", 12), border_width=T.BORDER_W, border_color=T.BORDER,
            wrap="word", height=130,
        )
        paste_box.grid(row=2, column=0, sticky="nsew", pady=(0, 8))

        status_lbl = ctk.CTkLabel(
            outer, text="", font=T.FONT_SMALL, text_color=T.TEXT_SECONDARY,
        )
        status_lbl.grid(row=3, column=0, sticky="w", pady=(0, 4))

        results_scroll = ctk.CTkScrollableFrame(
            outer, fg_color="transparent", height=200,
        )
        results_scroll.grid(row=4, column=0, sticky="nsew", pady=(0, 8))
        results_scroll.grid_columnconfigure(0, weight=1)
        outer.grid_rowconfigure(4, weight=1)

        result_rows: list[dict] = []
        existing_names =[d.get("name", "") for d in self.saved_djs]

        def _parse():
            nonlocal result_rows
            for w in results_scroll.winfo_children():
                w.destroy()
            result_rows.clear()

            raw = paste_box.get("1.0", "end-1c").strip()
            if not raw:
                status_lbl.configure(text="Paste something first.", text_color=T.ERROR)
                return

            entries = self._parse_dj_links(raw)
            if not entries:
                status_lbl.configure(text="No URLs detected.", text_color=T.ERROR)
                return

            status_lbl.configure(
                text=f"{len(entries)} link(s) detected.",
                text_color=T.IMPORT_SUCCESS,
            )

            for i, (det_name, url) in enumerate(entries):
                row_frame = ctk.CTkFrame(results_scroll, **T.CARD)
                row_frame.pack(fill="x", padx=T.SCROLL_PAD_X, pady=(0, 6))
                row_frame.grid_columnconfigure(1, weight=1)

                short_url = url if len(url) <= 44 else url[:41] + "…"
                ctk.CTkLabel(
                    row_frame, text=short_url,
                    font=("Consolas", 10), text_color=T.TEXT_MUTED,
                ).grid(row=0, column=0, columnspan=3, sticky="w", padx=10, pady=(6, 2))

                mode_var   = ctk.StringVar(value="new")
                name_var   = ctk.StringVar(value=det_name)
                assign_var = ctk.StringVar(value=existing_names[0] if existing_names else "")

                name_entry = ctk.CTkEntry(
                    row_frame, textvariable=name_var,
                    placeholder_text="DJ name…",
                    height=T.WIDGET_H_XS, fg_color=T.PANEL_BG, border_color=T.BORDER,
                )
                assign_menu = ctk.CTkOptionMenu(
                    row_frame,
                    variable=assign_var,
                    values=existing_names if existing_names else ["—"],
                    height=T.WIDGET_H_XS,
                    **T.OPTION_MENU,
                )

                def _toggle_mode(val, ne=name_entry, am=assign_menu):
                    if val == "new":
                        am.grid_forget()
                        ne.grid(row=1, column=1, sticky="ew", padx=(0, 10), pady=(2, 6))
                    else:
                        ne.grid_forget()
                        am.grid(row=1, column=1, sticky="ew", padx=(0, 10), pady=(2, 6))

                mode_seg = ctk.CTkSegmentedButton(
                    row_frame,
                    values=["New DJ", "Assign to existing"],
                    variable=mode_var,
                    command=lambda val, mv=mode_var, ne=name_entry, am=assign_menu: _toggle_mode(val),
                    font=T.FONT_SMALL, height=T.WIDGET_H_XS,
                    fg_color=T.BORDER, selected_color=T.PRIMARY,
                    selected_hover_color=T.PRIMARY_HOVER,
                    unselected_color=T.BORDER,
                    unselected_hover_color=T.HOVER,
                    text_color=T.TEXT_PRIMARY,
                )
                mode_seg.grid(row=1, column=0, padx=(10, 6), pady=(2, 6))
                name_entry.grid(row=1, column=1, sticky="ew", padx=(0, 10), pady=(2, 6))

                if not existing_names:
                    mode_seg.configure(state="disabled")

                result_rows.append({
                    "url": url,
                    "name_var": name_var,
                    "mode_var": mode_var,
                    "assign_var": assign_var,
                    "name_entry": name_entry,
                })

        def _import():
            if not result_rows:
                status_lbl.configure(text="Nothing to import. Press Parse first.", text_color=T.ERROR)
                return

            added = 0
            updated = 0
            errors = []

            for row in result_rows:
                url   = row["url"]
                mode  = row["mode_var"].get()

                if mode == "new":
                    name = row["name_var"].get().strip()
                    if not name:
                        row["name_entry"].configure(border_color=T.ERROR)
                        errors.append("One or more new DJ names are blank.")
                        continue
                    if name.lower() in[d.get("name", "").lower() for d in self.saved_djs]:
                        for d in self.saved_djs:
                            if d.get("name", "").lower() == name.lower():
                                d["stream"] = url
                                updated += 1
                                break
                    else:
                        self.saved_djs.append({"name": name, "stream": url, "exact_link": False})
                        added += 1
                else:
                    target_name = row["assign_var"].get()
                    for d in self.saved_djs:
                        if d.get("name", "") == target_name:
                            d["stream"] = url
                            updated += 1
                            break

            if errors:
                status_lbl.configure(text=" | ".join(errors), text_color=T.ERROR)
                return

            self._save_library()
            self.refresh_dj_roster_ui()
            self.after(0, self._refresh_slot_combos)
            popup.destroy()

        btn_row = ctk.CTkFrame(outer, fg_color="transparent")
        btn_row.grid(row=5, column=0, sticky="e", pady=(0, 0))

        ctk.CTkButton(
            btn_row, text="Cancel", width=80, height=T.WIDGET_H_SM,
            **T.BTN_SECONDARY, font=T.FONT_BODY_BOLD,
            command=popup.destroy,
        ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            btn_row, text="Parse", width=80, height=T.WIDGET_H_SM,
            **T.BTN_SECONDARY, font=T.FONT_BODY_BOLD, text_color=T.ACCENT,
            command=_parse,
        ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            btn_row, text="Import", width=90, height=T.WIDGET_H_SM,
            **T.BTN_PRIMARY, font=T.FONT_BODY_BOLD,
            command=_import,
        ).pack(side="left")

        popup.bind("<Escape>", lambda e: popup.destroy())
        paste_box.focus_set()

    @staticmethod
    def _parse_dj_links(text: str) -> list[tuple[str, str]]:
        url_re = re.compile(r'https?://[^\s<>"]+', re.IGNORECASE)
        results: list[tuple[str, str]] =[]

        for line in text.splitlines():
            s = line.strip()
            if not s:
                continue

            s_clean = re.sub(r'<(https?://[^>]+)>', r'\1', s)
            urls_in_line = url_re.findall(s_clean)
            if not urls_in_line:
                continue
            url = urls_in_line[0]

            name_fragment = url_re.sub("", s_clean).strip().rstrip(":—-– ").strip()
            name_fragment = re.sub(r'\*\*(.+?)\*\*', r'\1', name_fragment)
            name_fragment = re.sub(r'\*([^*]+?)\*',  r'\1', name_fragment)
            name_fragment = re.sub(r'^[:\-–—]+\s*', '', name_fragment).strip()
            name_fragment = re.sub(r'\s*[:\-–—]+$', '', name_fragment).strip()

            if name_fragment:
                det_name = name_fragment
            else:
                path_parts =[p for p in url.rstrip('/').split('/') if p]
                raw_slug   = path_parts[-1] if path_parts else ""
                raw_slug   = raw_slug.split('?')[0]
                det_name   = raw_slug.replace('_', ' ').replace('-', ' ').title()

            results.append((det_name, url))

        return results

    def _delete_dj_from_roster(self, idx):
        if idx < len(self.saved_djs):
            name = self.saved_djs[idx].get("name", "this DJ")
            if messagebox.askyesno("Confirm Delete", f"Remove '{name}' from the roster?"):
                self.saved_djs.pop(idx)
                self._save_library()
                self.refresh_dj_roster_ui()
                self.after(0, self._refresh_slot_combos)

    def add_new_dj_to_roster(self):
        popup = ctk.CTkToplevel(self)
        popup.title("New DJ")
        popup.geometry("380x240")
        popup.resizable(False, False)
        popup.configure(fg_color=T.CARD_BG)
        popup.grab_set()
        popup.focus_force()

        self.update_idletasks()
        x = self.winfo_x() + (self.winfo_width()  - 380) // 2
        y = self.winfo_y() + (self.winfo_height() - 240) // 2
        popup.geometry(f"380x280+{x}+{y}")

        content = ctk.CTkFrame(popup, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=20, pady=16)
        content.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(content, text="NAME", font=T.FONT_SMALL_BOLD, text_color=T.TEXT_SECONDARY).grid(row=0, column=0, sticky="w", pady=(0, 2))
        name_var = ctk.StringVar()
        name_entry = ctk.CTkEntry(content, textvariable=name_var, height=T.WIDGET_H_SM,
                                   fg_color=T.PANEL_BG, border_color=T.BORDER)
        name_entry.grid(row=1, column=0, sticky="ew", pady=(0, 10))

        ctk.CTkLabel(content, text="🎙  STREAM LINK", font=T.FONT_SMALL_BOLD, text_color=T.TEXT_SECONDARY).grid(row=2, column=0, sticky="w", pady=(0, 2))
        stream_var = ctk.StringVar()
        ctk.CTkEntry(
            content, textvariable=stream_var,
            placeholder_text="https://stream.vrcdn.live/live/...",
            height=T.WIDGET_H_SM, fg_color=T.PANEL_BG, border_color=T.BORDER
        ).grid(row=3, column=0, sticky="ew", pady=(0, 6))

        exact_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            content, text="Use exact link (skip Quest/PC conversion)",
            variable=exact_var,
            font=T.FONT_BODY, text_color=T.TEXT_SECONDARY,
            fg_color=T.ACCENT, hover_color=T.PRIMARY,
            border_color=T.BORDER, checkmark_color=T.WHITE
        ).grid(row=4, column=0, sticky="w", pady=(0, 10))

        btn_row = ctk.CTkFrame(content, fg_color="transparent")
        btn_row.grid(row=5, column=0, sticky="e")

        def _save():
            name = name_var.get().strip()
            if not name:
                name_entry.configure(border_color=T.ERROR)
                return
            if name.lower() in[d.get("name", "").lower() for d in self.saved_djs]:
                name_entry.configure(border_color=T.ERROR)
                ctk.CTkLabel(content, text="Name already exists.",
                             font=T.FONT_SMALL, text_color=T.ERROR).grid(row=6, column=0, sticky="w")
                return
            self.saved_djs.append({"name": name, "stream": stream_var.get().strip(), "exact_link": exact_var.get()})
            self._save_library()
            self.refresh_dj_roster_ui()
            self.after(0, self._refresh_slot_combos)
            popup.destroy()

        ctk.CTkButton(
            btn_row, text="Cancel", width=80, height=T.WIDGET_H_SM,
            **T.BTN_SECONDARY, font=T.FONT_BODY_BOLD,
            command=popup.destroy
        ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            btn_row, text="", image=self.icon_save, width=T.ICON_BTN_W, height=T.WIDGET_H_SM,
            **T.BTN_SUCCESS,
            command=_save
        ).pack(side="left")

        popup.bind("<Return>", lambda e: _save())
        popup.bind("<Escape>", lambda e: popup.destroy())
        name_entry.focus_set()