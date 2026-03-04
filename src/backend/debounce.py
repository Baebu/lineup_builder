class DebounceMixin:
    """Debounce helpers that coalesce rapid widget-trace callbacks."""

    def _schedule_update(self, delay: int = 150):
        """Debounce update_output: cancel any pending rebuild and reschedule."""
        if self._update_job is not None:
            self.after_cancel(self._update_job)
        self._update_job = self.after(delay, self._run_scheduled_update)

    def _run_scheduled_update(self):
        self._update_job = None
        self.update_output()
        self._schedule_auto_save()
        if self.event_title_var.get().strip():
            self._schedule_auto_event_save(delay=3000)

    def _schedule_roster_refresh(self, delay: int = 120):
        """Debounce refresh_dj_roster_ui so rapid typing only triggers one rebuild."""
        if self._roster_job is not None:
            self.after_cancel(self._roster_job)
        self._roster_job = self.after(delay, self._run_scheduled_roster_refresh)

    def _run_scheduled_roster_refresh(self):
        self._roster_job = None
        self.refresh_dj_roster_ui()

    def _schedule_save_library(self, delay: int = 500):
        """Debounce _save_library so rapid mutations coalesce into one write."""
        if self._save_lib_job is not None:
            self.after_cancel(self._save_lib_job)
        self._save_lib_job = self.after(delay, self._run_scheduled_save_library)

    def _run_scheduled_save_library(self):
        self._save_lib_job = None
        self._save_library()

    def _schedule_auto_save(self, delay: int = 5000):
        """Debounce _save_auto_state so rapid edits coalesce into one write."""
        if self._auto_save_job is not None:
            self.after_cancel(self._auto_save_job)
        self._auto_save_job = self.after(delay, self._run_scheduled_auto_save)

    def _run_scheduled_auto_save(self):
        self._auto_save_job = None
        self._save_auto_state()

    def _schedule_auto_event_save(self, delay: int = 1500):
        """Debounce auto-save of the current event to lineup_events.yaml."""
        if self._auto_event_save_job is not None:
            self.after_cancel(self._auto_event_save_job)
        self._auto_event_save_job = self.after(delay, self._run_scheduled_auto_event_save)

    def _run_scheduled_auto_event_save(self):
        self._auto_event_save_job = None
        self._auto_event_save()

    def _refresh_slot_combos(self):
        """Update all slot name-entry dropdowns in one deferred pass."""
        names = self.get_dj_names()
        for slot in self.slots:
            slot.name_entry.configure(values=names)
