"""
Module: bookings.py
Purpose: DJ discovery modal — opened from search button on each slot row.
Architecture: Mixin for App class.
"""

import threading
from datetime import datetime

import dearpygui.dearpygui as dpg

from ..styling.fonts import BODY, HEADER, HINT, LABEL, MUTED, styled_text
from ..ui.widgets import add_primary_button, popup_pos


class BookingsMixin:

    _cached_dj_list: list[dict] = []

    # ── Entry point (called from slot search button) ──────────────────────

    def _open_slot_booking_modal(self, slot):
        """Open a modal to find and book a DJ for the given slot."""
        win_tag = "slot_booking_modal"
        if dpg.does_item_exist(win_tag):
            dpg.delete_item(win_tag)

        sid = slot._id
        slot_time = ""
        if dpg.does_item_exist(f"slot_time_{sid}"):
            slot_time = dpg.get_value(f"slot_time_{sid}").strip()
        slot_dur = slot.duration_var.get()

        with dpg.window(
            tag=win_tag, label="Find a DJ",
            modal=True, autosize=True, no_resize=True,
            on_close=lambda: dpg.delete_item(win_tag),
            min_size=(380, 0),
            pos=popup_pos(width=380, height=420),
        ):
            styled_text("  FIND A DJ", HEADER)
            if slot_time and slot_time != "--:--":
                styled_text(f"  Slot: {slot_time}  ({slot_dur} min)", MUTED)
            dpg.add_spacer(height=4)

            # Genre filter
            dpg.add_input_text(
                tag="sbm_genre_filter", hint="Filter by genre...", width=-1,
                callback=lambda s, a: self._sbm_apply_filters(),
            )
            dpg.add_spacer(height=2)
            with dpg.group(horizontal=True):
                add_primary_button(
                    "Search", tag="sbm_search_btn", width=-1,
                    callback=lambda: self._sbm_fetch_djs(),
                )
            dpg.add_spacer(height=2)
            styled_text("", HINT, tag="sbm_status_label")
            dpg.add_separator()
            dpg.add_spacer(height=4)

            with dpg.child_window(tag="sbm_dj_scroll", height=300,
                                  border=False, autosize_x=True):
                styled_text("   Press Search to load DJs.", MUTED)

        # Store reference to the slot for booking
        self._sbm_active_slot = slot

        # Auto-fetch if we have a cached list
        if self._cached_dj_list:
            self._sbm_apply_filters()

    # ── Fetch ─────────────────────────────────────────────────────────────

    def _sbm_fetch_djs(self):
        """Fetch the full DJ list from the server in background."""
        if not self.api.base_url:
            self._sbm_set_status("Server URL not configured.")
            return

        self._sbm_set_status("Loading DJs...")

        def _do():
            try:
                result = self.api.dj_list()

                def _ok():
                    self._cached_dj_list = result
                    self._sbm_set_status("")
                    self._sbm_apply_filters()

                self._work_queue.put(_ok)
            except Exception:
                self._work_queue.put(
                    lambda: self._sbm_set_status("Failed to load DJ list."))

        threading.Thread(target=_do, daemon=True).start()

    # ── Filtering ─────────────────────────────────────────────────────────

    def _sbm_apply_filters(self):
        """Filter cached DJs by genre, then render in the modal scroll area."""
        container = "sbm_dj_scroll"
        if not dpg.does_item_exist(container):
            return
        dpg.delete_item(container, children_only=True)

        if not self._cached_dj_list:
            styled_text("   No registered DJs found.", MUTED, parent=container)
            return

        genre_q = ""
        if dpg.does_item_exist("sbm_genre_filter"):
            genre_q = dpg.get_value("sbm_genre_filter").strip().lower()

        # Get the active slot's computed time for availability matching
        slot = getattr(self, "_sbm_active_slot", None)
        slot_date = ""
        slot_time_str = ""
        if slot:
            sid = slot._id
            # Try to derive date from the event timestamp
            ts_tag = "dt_input"
            if dpg.does_item_exist(ts_tag):
                ts_val = dpg.get_value(ts_tag).strip()
                if ts_val:
                    try:
                        dt = datetime.strptime(ts_val, "%Y-%m-%d %H:%M")
                        slot_date = dt.strftime("%Y-%m-%d")
                    except ValueError:
                        pass
            # Get slot start time from the computed time label
            if dpg.does_item_exist(f"slot_time_{sid}"):
                t = dpg.get_value(f"slot_time_{sid}").strip()
                if t and t != "--:--":
                    slot_time_str = t

        results = []
        for dj in self._cached_dj_list:
            # Genre filter
            if genre_q:
                dj_genres = [g.lower() for g in dj.get("genres", [])]
                if not any(genre_q in g for g in dj_genres):
                    continue

            # Availability check
            avail = dj.get("availability", [])
            avail_match = None  # None = no date context to check
            if slot_date:
                if avail:
                    avail_match = self._sbm_check_availability(
                        avail, slot_date, slot_time_str)
                else:
                    avail_match = False

            results.append((dj, avail_match))

        if not results:
            styled_text("   No DJs match your filters.", MUTED, parent=container)
            return

        # Available first
        available = [(d, m) for d, m in results if m is True]
        rest = [(d, m) for d, m in results if m is not True]

        if slot_date and available:
            styled_text(f"   AVAILABLE ({len(available)})", LABEL, parent=container)
            dpg.add_spacer(height=2, parent=container)
        for dj, _ in available:
            self._sbm_render_dj_card(container, dj, available=True)

        if slot_date and rest:
            dpg.add_spacer(height=4, parent=container)
            styled_text(f"   OTHER ({len(rest)})", LABEL, parent=container)
            dpg.add_spacer(height=2, parent=container)
        for dj, m in rest:
            self._sbm_render_dj_card(
                container, dj,
                available=False if m is False else None,
            )

    def _sbm_check_availability(
        self, avail: list[dict], date_str: str, start_str: str
    ) -> bool:
        """Check if any availability entry covers the given date/time."""
        for entry in avail:
            if not isinstance(entry, dict):
                continue
            if entry.get("date", "") != date_str:
                continue
            if not start_str:
                return True
            try:
                req = self._sbm_parse_time(start_str)
                a_start = self._sbm_parse_time(entry.get("start", ""))
                a_end = self._sbm_parse_time(entry.get("end", ""))
                if a_start <= req < a_end:
                    return True
            except (ValueError, TypeError):
                continue
        return False

    @staticmethod
    def _sbm_parse_time(time_str: str) -> int:
        """Parse '8:00 PM' or '20:00' to minutes since midnight."""
        time_str = time_str.strip().upper()
        for fmt in ("%I:%M %p", "%H:%M"):
            try:
                t = datetime.strptime(time_str, fmt)
                return t.hour * 60 + t.minute
            except ValueError:
                continue
        return 0

    # ── Rendering ─────────────────────────────────────────────────────────

    def _sbm_render_dj_card(self, parent: str, dj: dict, available: bool | None):
        """Render a single DJ row in the modal."""
        name = dj.get("name", "Unknown")
        genres = dj.get("genres", [])
        avail_entries = dj.get("availability", [])

        with dpg.group(parent=parent):
            with dpg.table(header_row=False, borders_innerH=False,
                           borders_innerV=False, borders_outerH=False,
                           borders_outerV=False, pad_outerX=False):
                dpg.add_table_column(width_stretch=True)
                dpg.add_table_column(width_fixed=True)
                with dpg.table_row():
                    with dpg.group():
                        styled_text(f"   {name}", BODY)
                        if genres:
                            styled_text(f"   {', '.join(genres)}", MUTED)
                        if avail_entries:
                            dates = sorted(
                                e.get("date", "") for e in avail_entries
                                if isinstance(e, dict) and e.get("date")
                            )
                            if dates:
                                styled_text(
                                    f"   Available: {dates[0]}"
                                    + (f" +{len(dates)-1} more" if len(dates) > 1 else ""),
                                    MUTED,
                                )
                    with dpg.group():
                        if available is True:
                            styled_text("OPEN", HINT)
                        elif available is False:
                            styled_text("—", MUTED)
                        add_primary_button(
                            "Book", width=60,
                            callback=lambda s=None, a=None, d=dj: self._sbm_open_confirm(d),
                        )
            dpg.add_separator()

    # ── Booking confirm popup ─────────────────────────────────────────────

    def _sbm_open_confirm(self, dj: dict):
        """Open a nested confirmation popup to send a booking request."""
        win_tag = "sbm_confirm_win"
        if dpg.does_item_exist(win_tag):
            dpg.delete_item(win_tag)

        dj_name = dj.get("name", "")
        slot = getattr(self, "_sbm_active_slot", None)

        # Pre-fill from event/slot context
        event_title = ""
        if dpg.does_item_exist("event_title_input"):
            event_title = dpg.get_value("event_title_input").strip()

        slot_date = ""
        slot_time = ""
        slot_dur = 60
        if slot:
            sid = slot._id
            slot_dur = int(slot.duration_var.get() or 60)
            if dpg.does_item_exist("dt_input"):
                ts = dpg.get_value("dt_input").strip()
                if ts:
                    try:
                        dt = datetime.strptime(ts, "%Y-%m-%d %H:%M")
                        slot_date = dt.strftime("%Y-%m-%d")
                    except ValueError:
                        pass
            if dpg.does_item_exist(f"slot_time_{sid}"):
                t = dpg.get_value(f"slot_time_{sid}").strip()
                if t and t != "--:--":
                    slot_time = t

        with dpg.window(
            tag=win_tag, label=f"Book {dj_name}",
            modal=True, autosize=True, no_resize=True, no_scrollbar=True,
            on_close=lambda: dpg.delete_item(win_tag),
            pos=popup_pos(width=330, height=300),
        ):
            styled_text(f"  Book {dj_name}", HEADER)
            dpg.add_spacer(height=4)

            _LABEL_W = 62
            with dpg.table(header_row=False, borders_innerH=False,
                           borders_innerV=False, borders_outerH=False,
                           borders_outerV=False, pad_outerX=False):
                dpg.add_table_column(init_width_or_weight=_LABEL_W, width_fixed=True)
                dpg.add_table_column(width_stretch=True)
                with dpg.table_row():
                    styled_text("   EVENT", LABEL)
                    dpg.add_input_text(
                        tag="bk_confirm_event", width=260,
                        default_value=event_title, hint="Event title...",
                    )
                with dpg.table_row():
                    styled_text("   DATE", LABEL)
                    dpg.add_input_text(
                        tag="bk_confirm_date", width=260,
                        default_value=slot_date,
                    )
                with dpg.table_row():
                    styled_text("   TIME", LABEL)
                    dpg.add_input_text(
                        tag="bk_confirm_time", width=260,
                        default_value=slot_time,
                    )
                with dpg.table_row():
                    styled_text("   MINS", LABEL)
                    dpg.add_input_int(
                        tag="bk_confirm_duration", width=260,
                        default_value=slot_dur, min_value=15, max_value=480,
                        min_clamped=True, max_clamped=True,
                    )
                with dpg.table_row():
                    styled_text("   MSG", LABEL)
                    dpg.add_input_text(
                        tag="bk_confirm_msg", width=260,
                        hint="Optional message...",
                        multiline=True, height=50,
                    )

            dpg.add_spacer(height=4)
            add_primary_button(
                "Send Booking Request", tag="bk_confirm_send_btn", width=-1,
                callback=lambda: self._sbm_send(dj_name, win_tag),
            )
            dpg.add_spacer(height=2)
            styled_text("", HINT, tag="bk_confirm_status")

    def _sbm_send(self, dj_name: str, win_tag: str):
        """Send the booking request from the confirm popup."""
        if not self.api.base_url:
            dpg.set_value("bk_confirm_status", "   Server URL not configured.")
            return

        event_title = dpg.get_value("bk_confirm_event").strip()
        event_date = dpg.get_value("bk_confirm_date").strip()
        start_time = dpg.get_value("bk_confirm_time").strip()
        duration = dpg.get_value("bk_confirm_duration")
        message = dpg.get_value("bk_confirm_msg").strip()

        group_name = ""
        for label in ("DISCORD", "VRC GROUP"):
            p = getattr(self, "persistent_links", {}).get(label, {})
            if isinstance(p, dict) and p.get("link"):
                group_name = p["link"]
                break
        if not group_name:
            group_name = event_title

        dpg.set_value("bk_confirm_status", "   Sending...")
        dpg.configure_item("bk_confirm_send_btn", enabled=False)

        def _do():
            try:
                result = self.api.create_booking(
                    dj_name=dj_name,
                    group_name=group_name,
                    event_title=event_title,
                    event_date=event_date,
                    start_time=start_time,
                    duration=duration,
                    message=message,
                )

                def _ok():
                    dpg.set_value("bk_confirm_status",
                                  f"   Booking #{result['id']} sent!")
                    dpg.configure_item("bk_confirm_send_btn", enabled=True)
                    # Fill the slot name with the booked DJ
                    slot = getattr(self, "_sbm_active_slot", None)
                    if slot:
                        slot.name_var.set(dj_name)
                        if dpg.does_item_exist(f"slot_name_{slot._id}"):
                            dpg.set_value(f"slot_name_{slot._id}", dj_name)
                        self._schedule_update()

                self._work_queue.put(_ok)
            except Exception as exc:
                detail = getattr(exc, "detail", str(exc))

                def _err():
                    dpg.set_value("bk_confirm_status", f"   {detail}")
                    dpg.configure_item("bk_confirm_send_btn", enabled=True)

                self._work_queue.put(_err)

        threading.Thread(target=_do, daemon=True).start()

    # ── Status helper ─────────────────────────────────────────────────────

    def _sbm_set_status(self, text: str):
        def _update():
            if dpg.does_item_exist("sbm_status_label"):
                dpg.set_value("sbm_status_label", f"   {text}" if text else "")
        self._work_queue.put(_update)
