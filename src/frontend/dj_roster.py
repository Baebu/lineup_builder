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

        # Hoist edit vars so header buttons can reference them
        name_var   = ctk.StringVar(value=dj.get("name", ""))
        stream_var = ctk.StringVar(value=dj.get("stream", ""))
        exact_var  = ctk.BooleanVar(value=bool(dj.get("exact_link", False)))

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

        del_btn = ctk.CTkButton(
            header, text="", image=self.icon_trash, width=32, height=32,
            fg_color="#7F1D1D", hover_color="#991B1B",
            command=lambda i=idx: self._delete_dj_from_roster(i)
        )
        del_btn.pack(side="right", padx=(0, 4))

        # ── Body (collapsed by default) ──
        body = ctk.CTkFrame(card, fg_color="#1E293B", corner_radius=6)

        ctk.CTkLabel(body, text="NAME", font=("Arial", 10, "bold"), text_color="#94A3B8").pack(anchor="w", padx=10, pady=(10, 2))
        ctk.CTkEntry(body, textvariable=name_var, fg_color="#0F172A", border_color="#334155", height=32).pack(fill="x", padx=10, pady=(0, 8))

        ctk.CTkLabel(body, text="🎙  STREAM LINK", font=("Arial", 10, "bold"), text_color="#94A3B8").pack(anchor="w", padx=10, pady=(0, 2))
        ctk.CTkEntry(
            body, textvariable=stream_var,
            placeholder_text="https://stream.vrcdn.live/live/...",
            fg_color="#0F172A", border_color="#334155", height=32
        ).pack(fill="x", padx=10, pady=(0, 6))

        ctk.CTkCheckBox(
            body, text="Use exact link (skip Quest/PC conversion)",
            variable=exact_var,
            font=("Arial", 11), text_color="#94A3B8",
            fg_color="#818CF8", hover_color="#4F46E5",
            border_color="#334155", checkmark_color="#FFFFFF"
        ).pack(anchor="w", padx=10, pady=(0, 10))

        # ── Fix 1: Mouse-wheel passthrough ────────────────────────────────
        # CTkScrollableFrame only captures scroll on its canvas; child widgets
        # (entries, checkboxes) swallow <MouseWheel> events.  Forward them all
        # back to the roster canvas so scrolling always works.
        _roster_canvas = self.dj_roster_scroll._parent_canvas

        def _forward_scroll(e):
            _roster_canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")

        def _bind_wheel(widget):
            widget.bind("<MouseWheel>", _forward_scroll, add="+")
            for child in widget.winfo_children():
                _bind_wheel(child)

        _bind_wheel(body)

        # ── Auto-save on any field change ──
        _autosave_job = [None]

        def _schedule_autosave(*_):
            if _autosave_job[0] is not None:
                self.after_cancel(_autosave_job[0])
            _autosave_job[0] = self.after(
                700, lambda: self._save_dj_card(idx, name_var, stream_var, exact_var, name_lbl)
            )

        name_var.trace_add("write", _schedule_autosave)
        stream_var.trace_add("write", _schedule_autosave)
        exact_var.trace_add("write", _schedule_autosave)

        ANIM_STEPS = 16
        ANIM_DELAY = 13  # ms per step (~16*13 ≈ 208ms total)

        # Fix 3+4: shared mutable state so toggle always collapses from the
        # correct full height even when interrupted mid-animation, and so we
        # can suppress the autohide scrollbar check during animation.
        _state = {
            "full_h": 0,       # canonical natural height of the body
            "animating": False, # True while expand/collapse is in progress
        }

        def _finish_anim():
            """Called when any animation completes — re-enable scrollbar check."""
            _state["animating"] = False
            # Trigger one clean scrollbar visibility recalculation now that
            # layout has settled, suppressing the per-step flicker.
            sf = self.dj_roster_scroll
            sf._parent_canvas.event_generate("<Configure>")

        def _do_expand(target_h, step=1):
            if not expanded.get():
                _finish_anim()
                return
            if step > ANIM_STEPS:
                body.configure(height=target_h)
                body.pack_propagate(True)
                _finish_anim()
                # Fix 2: scroll the card into view after fully expanding
                _scroll_into_view()
                return
            t = step / ANIM_STEPS
            # ease-out cubic: fast open, smooth gentle landing
            t_ease = 1 - (1 - t) ** 3
            body.configure(height=max(1, int(target_h * t_ease)))
            body.after(ANIM_DELAY, lambda: _do_expand(target_h, step + 1))

        def _do_collapse(from_h, step=1):
            if expanded.get():
                _finish_anim()
                return
            if step > ANIM_STEPS:
                body.pack_forget()
                _finish_anim()
                return
            t = step / ANIM_STEPS
            # ease-in-out cubic: smooth start AND end for a clean fold-away
            t_ease = t * t * (3 - 2 * t)
            body.configure(height=max(1, int(from_h * (1 - t_ease))))
            body.after(ANIM_DELAY, lambda: _do_collapse(from_h, step + 1))

        def _scroll_into_view():
            """Fix 2: nudge the roster canvas so the open card is visible."""
            canvas = self.dj_roster_scroll._parent_canvas
            bbox = canvas.bbox("all")
            if not bbox:
                return
            total_h = max(bbox[3] - bbox[1], 1)
            canvas_h = canvas.winfo_height()
            card_top = card.winfo_y()
            card_bot = card_top + card.winfo_height()
            view_bot = canvas.yview()[1] * total_h
            if card_bot > view_bot:
                new_top = max(0, (card_bot - canvas_h) / total_h)
                canvas.yview_moveto(min(new_top, 1.0))

        def toggle(event=None):
            if expanded.get():
                body.pack_propagate(False)
                # Fix 4: use the stored full natural height to avoid collapsing
                # from a partial height when interrupted mid-expand.
                cur_h = _state["full_h"] if _state["full_h"] > 0 else body.winfo_height()
                arrow_btn.configure(image=self.icon_chevron_up)
                expanded.set(False)
                _state["animating"] = True
                _do_collapse(cur_h)
            else:
                # Lock height to 1 BEFORE packing to prevent the full-height flash
                body.pack_propagate(False)
                body.configure(height=1)
                body.pack(fill="x", padx=6, pady=(0, 8))
                # winfo_reqheight reads internal layout requests without a render
                nat_h = body.winfo_reqheight()
                arrow_btn.configure(image=self.icon_chevron_down)
                expanded.set(True)
                _state["animating"] = True
                if nat_h >= 10:
                    _state["full_h"] = nat_h
                    body.after(1, lambda: _do_expand(nat_h))
                else:
                    # Fix 5: retry measure up to 5 times; reset state on failure
                    def _start_after_measure(attempt=0):
                        h = body.winfo_reqheight()
                        if h >= 10:
                            _state["full_h"] = h
                            _do_expand(h)
                        elif attempt < 5:
                            body.after(10, lambda: _start_after_measure(attempt + 1))
                        else:
                            # Geometry never settled — reset to collapsed cleanly
                            body.pack_forget()
                            arrow_btn.configure(image=self.icon_chevron_up)
                            expanded.set(False)
                            _finish_anim()
                    body.after(5, _start_after_measure)

        header.bind("<Button-1>", toggle)
        name_lbl.bind("<Button-1>", toggle)

        # Drag-and-drop: grip → add to lineup
        for w in (grip_btn,):
            w.bind("<B1-Motion>",       lambda e: self._on_dj_drag(e, name_lbl.cget("text")))
            w.bind("<ButtonRelease-1>", lambda e: self._end_dj_drag(e, name_lbl.cget("text")))

    def _save_dj_card(self, idx, name_var, stream_var, exact_var, name_lbl):
        new_name = name_var.get().strip()
        if not new_name:
            return
        old_name = self.saved_djs[idx].get("name", "")
        self.saved_djs[idx] = {
            "name": new_name,
            "stream": stream_var.get().strip(),
            "exact_link": exact_var.get(),
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
        popup.geometry(f"380x280+{x}+{y}")

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
        ).grid(row=3, column=0, sticky="ew", pady=(0, 6))

        exact_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            content, text="Use exact link (skip Quest/PC conversion)",
            variable=exact_var,
            font=("Arial", 11), text_color="#94A3B8",
            fg_color="#818CF8", hover_color="#4F46E5",
            border_color="#334155", checkmark_color="#FFFFFF"
        ).grid(row=4, column=0, sticky="w", pady=(0, 10))

        btn_row = ctk.CTkFrame(content, fg_color="transparent")
        btn_row.grid(row=5, column=0, sticky="e")

        def _save():
            name = name_var.get().strip()
            if not name:
                name_entry.configure(border_color="#EF4444")
                return
            if name.lower() in [d.get("name", "").lower() for d in self.saved_djs]:
                name_entry.configure(border_color="#EF4444")
                ctk.CTkLabel(content, text="Name already exists.",
                             font=("Arial", 10), text_color="#EF4444").grid(row=6, column=0, sticky="w")
                return
            self.saved_djs.append({"name": name, "stream": stream_var.get().strip(), "exact_link": exact_var.get()})
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
