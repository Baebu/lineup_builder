/**
 * StorageManager — localStorage-based persistence.
 *
 * Keys:
 *   lineup_library   → { djs: DJInfo[], genres: string[] }
 *   lineup_events    → { [name]: EventObject }
 *   lineup_settings  → { ...settings }
 *   lineup_autosave  → { ...event state | cleanClose: true }
 */

const KEYS = {
  library: "lineup_library",
  events: "lineup_events",
  settings: "lineup_settings",
  autosave: "lineup_autosave",
};

export class StorageManager {
  constructor() {
    this._cache = {};
  }

  load() {
    for (const [k, key] of Object.entries(KEYS)) {
      try {
        const raw = localStorage.getItem(key);
        this._cache[k] = raw ? JSON.parse(raw) : null;
      } catch {
        this._cache[k] = null;
      }
    }
  }

  _persist(key, data) {
    try {
      localStorage.setItem(KEYS[key], JSON.stringify(data));
      this._cache[key] = data;
    } catch (e) {
      console.warn("StorageManager: failed to persist", key, e);
    }
  }

  // ── Library (DJs + Genres) ────────────────────────────────────────────

  getDjs() {
    return this._cache.library?.djs ?? [];
  }

  getGenres() {
    return this._cache.library?.genres ?? [];
  }

  saveLibrary({ djs, genres }) {
    const lib = this._cache.library ?? {};
    this._persist("library", {
      djs: djs ?? lib.djs ?? [],
      genres: genres ?? lib.genres ?? [],
    });
  }

  saveDjs(djs) {
    const lib = this._cache.library ?? {};
    this._persist("library", { ...lib, djs });
  }

  saveGenres(genres) {
    const lib = this._cache.library ?? {};
    this._persist("library", { ...lib, genres });
  }

  // ── Saved Events ──────────────────────────────────────────────────────

  getEvents() {
    return this._cache.events ?? {};
  }

  saveEvent(name, data) {
    const events = { ...(this._cache.events ?? {}) };
    events[name] = data;
    this._persist("events", events);
  }

  deleteEvent(name) {
    const events = { ...(this._cache.events ?? {}) };
    delete events[name];
    this._persist("events", events);
  }

  renameEvent(oldName, newName, data) {
    const events = { ...(this._cache.events ?? {}) };
    delete events[oldName];
    events[newName] = data;
    this._persist("events", events);
  }

  // ── Settings ──────────────────────────────────────────────────────────

  getSettings() {
    return this._cache.settings ?? {};
  }

  saveSettings(settings) {
    this._persist("settings", settings);
  }

  // ── Auto-save ─────────────────────────────────────────────────────────

  getAutoSave() {
    return this._cache.autosave ?? null;
  }

  saveAutoState(state) {
    try {
      localStorage.setItem(KEYS.autosave, JSON.stringify(state));
      this._cache.autosave = state;
    } catch {
      // quota exceeded — silently skip
    }
  }

  // ── DJ Session ────────────────────────────────────────────────────────

  getDjSession() {
    try {
      const raw = localStorage.getItem("lineup_dj_session");
      return raw ? JSON.parse(raw) : null;
    } catch {
      return null;
    }
  }

  setDjSession(session) {
    try {
      localStorage.setItem("lineup_dj_session", JSON.stringify(session));
    } catch {
      // ignore
    }
  }

  clearDjSession() {
    localStorage.removeItem("lineup_dj_session");
  }
}
