/**
 * CloudSync — server-first data sync with localStorage fallback.
 *
 * Port of desktop/src/backend/data_manager.py cloud-sync logic.
 *
 * When a Discord user is signed in, data is loaded from the server first
 * and pushed back on every save. localStorage serves as the offline fallback.
 */

import { DJInfo } from "../models/lineup-model.js";

export class CloudSync {
  /**
   * @param {import('./api-client.js').ApiClient} api
   * @param {import('./storage.js').StorageManager} storage
   */
  constructor(api, storage) {
    this.api = api;
    this.storage = storage;
    this._discordId = "";
  }

  /** Set the signed-in Discord user ID. Empty string = signed out. */
  setDiscordId(id) {
    this._discordId = String(id || "");
  }

  get isSignedIn() {
    return Boolean(this._discordId);
  }

  // ── Load (server-first, localStorage fallback) ────────────────────────

  /**
   * Load library + events. Tries the server first when signed in,
   * then falls back to localStorage.
   * @returns {{ djs: object[], genres: string[], events: object }}
   */
  async loadAll() {
    let serverData = {};

    if (this.isSignedIn) {
      try {
        const resp = await this.api.getAllUserData(this._discordId);
        serverData = resp.data ?? resp ?? {};
      } catch (e) {
        console.warn("CloudSync: could not fetch cloud data:", e);
      }
    }

    // ── Library ─────────────────────────────────────────────────────────
    let lib = serverData.library;
    if (!lib || !Object.keys(lib).length) {
      lib = { djs: this.storage.getDjs(), genres: this.storage.getGenres() };
    }

    const djs = CloudSync._normalizeDjs(lib.djs ?? []);
    const genres = lib.genres ?? [];

    // Persist to localStorage so offline works next time
    this.storage.saveLibrary({ djs, genres });

    // ── Events ──────────────────────────────────────────────────────────
    let events = serverData.events;
    if (!events || !Object.keys(events).length) {
      events = this.storage.getEvents();
    } else {
      // Merge: server events into local (server wins on conflicts)
      const local = this.storage.getEvents();
      events = { ...local, ...events };
    }

    // Persist merged events locally
    for (const [name, data] of Object.entries(events)) {
      this.storage.saveEvent(name, data);
    }

    return { djs, genres, events };
  }

  // ── Save (local + async server push) ──────────────────────────────────

  /**
   * Save library data locally and push to server.
   * @param {{ djs: object[], genres: string[] }} data
   */
  saveLibrary(data) {
    this.storage.saveLibrary(data);
    this._pushToServer("library", data);
  }

  /**
   * Save events data locally and push to server.
   * @param {object} data
   */
  saveEvents(data) {
    // Persist each event locally
    for (const [name, eventData] of Object.entries(data)) {
      this.storage.saveEvent(name, eventData);
    }
    this._pushToServer("events", data);
  }

  /**
   * Save a single event locally and push the full events collection to server.
   * @param {string} name
   * @param {object} data
   */
  saveEvent(name, data) {
    this.storage.saveEvent(name, data);
    this._pushToServer("events", this.storage.getEvents());
  }

  /**
   * Delete a single event locally and push the updated collection to server.
   * @param {string} name
   */
  deleteEvent(name) {
    this.storage.deleteEvent(name);
    this._pushToServer("events", this.storage.getEvents());
  }

  /**
   * Rename an event locally and push the updated collection to server.
   * @param {string} oldName
   * @param {string} newName
   * @param {object} data
   */
  renameEvent(oldName, newName, data) {
    this.storage.renameEvent(oldName, newName, data);
    this._pushToServer("events", this.storage.getEvents());
  }

  // ── Internal ──────────────────────────────────────────────────────────

  /**
   * Push a data blob to the server in the background.
   * Failures are logged but not thrown (fire-and-forget, same as desktop).
   */
  _pushToServer(key, value) {
    if (!this.isSignedIn) return;

    this.api.putUserData(this._discordId, key, value).catch((e) => {
      console.warn(`CloudSync: push "${key}" failed:`, e);
    });
  }

  /**
   * Normalize DJ entries from server data (handles legacy formats).
   * Mirrors desktop data_manager.py's DJ normalization logic.
   */
  static _normalizeDjs(raw) {
    const result = [];
    for (const d of raw) {
      if (typeof d === "string") {
        if (d) result.push({ name: d, stream: "", exactLink: false });
      } else if (typeof d === "object" && d !== null) {
        const name = d.name || "";
        if (!name) continue;
        result.push({
          name,
          stream: d.stream ?? d.goggles ?? d.link ?? "",
          exactLink: Boolean(d.exactLink ?? d.exact_link ?? false),
        });
      }
    }
    return result;
  }
}
