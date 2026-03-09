"""
Module: bookings.py
Purpose: Bookings tab — browse DJs by availability and genre, send booking requests.
Architecture: Mixin for App class.
"""

import threading
from datetime import datetime

import dearpygui.dearpygui as dpg

from ..styling.fonts import BODY, HEADER, HINT, LABEL, MUTED, Icon, styled_text
from ..ui.widgets import add_icon_button, add_primary_button
from ..ui.date_time_picker import add_date_row, add_time_row


class BookingsMixin:

    _cached_dj_list: list[dict] = []

    # ── Fetch ─────────────────────────────────────────────────────────────

    def _bookings_fetch_djs(self):
        """Fetch the full DJ list from the server in background."""
        if not self.api.base_url:
            self._bookings_set_status("Server URL not configured.")
            return

        self._bookings_set_status("Loading DJs...")

        def _do():
            try:
                result = self.api.dj_list()

                def _ok():
                    self._cached_dj_list = result
                    self._bookings_set_status("")
                    self._bookings_apply_filters()

                self._work_queue.put(_ok)
            except Exception:
                self._work_queue.put(
                    lambda: self._bookings_set_status("Failed to load DJ list."))

        threading.Thread(target=_do, daemon=True).start()

    # ── Filtering ─────────────────────────────────────────────────────────

    def _bookings_apply_filters(self):
        """Filter cached DJs by selected date/time and genre, then render."""
        container = "bookings_dj_scroll"
        if not dpg.does_item_exist(container):
            return
        dpg.delete_item(container, children_only=True)

        if not self._cached_dj_list:
            styled_text("   No registered DJs found.\n   Press Refresh to load.",
                        MUTED, parent=container)
            return

        # Read filter values
        date_str = dpg.get_value("bookings_filter_date").strip() if dpg.does_item_exist("bookings_filter_date") else ""
        start_str = dpg.get_value("bookings_filter_start") if dpg.does_item_exist("bookings_filter_start") else ""
        genre_q = dpg.get_value("bookings_genre_search").strip().lower() if dpg.does_item_exist("bookings_genre_search") else ""

        results = []
        for dj in self._cached_dj_list:
            # Genre filter
            if genre_q:
                dj_genres = [g.lower() for g in dj.get("genres", [])]
                if not any(genre_q in g for g in dj_genres):
                    continue

            # Availability filter
            avail = dj.get("availability", [])
            avail_match = True
            if date_str and avail:
                avail_match = self._bookings_check_availability(
                    avail, date_str, start_str)
            elif date_str and not avail:
                avail_match = False

            results.append((dj, avail_match))

        if not results:
            styled_text("   No DJs match your filters.", MUTED, parent=container)
            return

        # Show available DJs first, then others
        available = [(dj, m) for dj, m in results if m]
        unavailable = [(dj, m) for dj, m in results if not m]

        if date_str and available:
            styled_text(f"   AVAILABLE ({len(available)})", LABEL, parent=container)
            dpg.add_spacer(height=2, parent=container)

        for dj, _ in available:
            self._bookings_render_dj_card(container, dj, available=True)

        if date_str and unavailable:
            dpg.add_spacer(height=6, parent=container)
            styled_text(f"   OTHER ({len(unavailable)})", LABEL, parent=container)
            dpg.add_spacer(height=2, parent=container)

        if not date_str:
            for dj, _ in unavailable:
                self._bookings_render_dj_card(container, dj, available=None)
        else:
            for dj, _ in unavailable:
                self._bookings_render_dj_card(container, dj, available=False)

    def _bookings_check_availability(
        self, avail: list[dict], date_str: str, start_str: str
    ) -> bool:
        """Check if any availability entry covers the given date/time."""
        for entry in avail:
            if not isinstance(entry, dict):
                continue
            entry_date = entry.get("date", "")
            if entry_date != date_str:
                continue
            if not start_str:
                return True  # date match is enough if no time specified
            # Parse start/end times
            try:
                req_time = self._bookings_parse_time(start_str)
                avail_start = self._bookings_parse_time(entry.get("start", ""))
                avail_end = self._bookings_parse_time(entry.get("end", ""))
                if avail_start <= req_time < avail_end:
                    return True
            except (ValueError, TypeError):
                continue
        return False

    @staticmethod
    def _bookings_parse_time(time_str: str) -> int:
        """Parse a time string like '8:00 PM' to minutes since midnight."""
        time_str = time_str.strip().upper()
        for fmt in ("%I:%M %p", "%H:%M"):
            try:
                t = datetime.strptime(time_str, fmt)
                return t.hour * 60 + t.minute
            except ValueError:
                continue
        return 0

    # ── Rendering ─────────────────────────────────────────────────────────

    def _bookings_render_dj_card(self, parent: str, dj: dict, available: bool | None):
        """Render a single DJ card in the bookings scroll area."""
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
                            # Show next availability date
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
                            callback=lambda s=None, a=None, d=dj: self._bookings_open_confirm(d),
                        )
            dpg.add_separator()

    # ── Booking confirm popup ─────────────────────────────────────────────

    def _bookings_open_confirm(self, dj: dict):
        """Open a confirmation popup to send a booking to the selected DJ."""
        win_tag = "bookings_confirm_win"
        if dpg.does_item_exist(win_tag):
            dpg.delete_item(win_tag)

        dj_name = dj.get("name", "")
        date_val = dpg.get_value("bookings_filter_date").strip() if dpg.does_item_exist("bookings_filter_date") else ""
        time_val = dpg.get_value("bookings_filter_start") if dpg.does_item_exist("bookings_filter_start") else ""

        with dpg.window(
            tag=win_tag, label=f"Book {dj_name}",
            modal=True, autosize=True, no_resize=True, no_scrollbar=True,
            on_close=lambda: dpg.delete_item(win_tag),
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
                        default_value=dpg.get_value("event_title_input").strip()
                        if dpg.does_item_exist("event_title_input") else "",
                        hint="Event title...",
                    )
                with dpg.table_row():
                    styled_text("   DATE", LABEL)
                    dpg.add_input_text(
                        tag="bk_confirm_date", width=260,
                        default_value=date_val,
                    )
                with dpg.table_row():
                    styled_text("   TIME", LABEL)
                    dpg.add_input_text(
                        tag="bk_confirm_time", width=260,
                        default_value=time_val,
                    )
                with dpg.table_row():
                    styled_text("   MINS", LABEL)
                    dpg.add_input_int(
                        tag="bk_confirm_duration", width=260,
                        default_value=60, min_value=15, max_value=480,
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
                callback=lambda: self._bookings_send(dj_name, win_tag),
            )
            dpg.add_spacer(height=2)
            styled_text("", HINT, tag="bk_confirm_status")

    def _bookings_send(self, dj_name: str, win_tag: str):
        """Send the booking from the confirm popup."""
        if not self.api.base_url:
            dpg.set_value("bk_confirm_status", "   Server URL not configured.")
            return

        event_title = dpg.get_value("bk_confirm_event").strip()
        event_date = dpg.get_value("bk_confirm_date").strip()
        start_time = dpg.get_value("bk_confirm_time").strip()
        duration = dpg.get_value("bk_confirm_duration")
        message = dpg.get_value("bk_confirm_msg").strip()

        # Derive group name from persistent links
        group_name = ""
        for label in ("DISCORD", "VRC GROUP"):
            p = getattr(self, "persistent_links", {}).get(label, {})
            if isinstance(p, dict) and p.get("link"):
                group_name = p["link"]
                break
        if not group_name:
            group_name = dpg.get_value("event_title_input").strip() if dpg.does_item_exist("event_title_input") else ""

        dpg.set_value("bk_confirm_status", "   Sending...")
        dpg.configure_item("bk_confirm_send_btn", enabled=False)

        def _do():
            try:
                from src.backend.services.api_client import APIError
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

                self._work_queue.put(_ok)
            except Exception as exc:
                detail = getattr(exc, "detail", str(exc))

                def _err():
                    dpg.set_value("bk_confirm_status", f"   {detail}")
                    dpg.configure_item("bk_confirm_send_btn", enabled=True)

                self._work_queue.put(_err)

        threading.Thread(target=_do, daemon=True).start()

    # ── Status helper ─────────────────────────────────────────────────────

    def _bookings_set_status(self, text: str):
        """Update the bookings tab status label."""
        def _update():
            if dpg.does_item_exist("bookings_status_label"):
                dpg.set_value("bookings_status_label", f"   {text}" if text else "")
        self._work_queue.put(_update)
