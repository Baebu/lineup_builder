/**
 * EventsManager — save / load / delete / duplicate named event lineups.
 *
 * Renders saved events list in #saved-events-list.
 * Events are stored via StorageManager under "lineup_events".
 *
 * Mirrors desktop EventsMixin.
 */
import { showToast } from "./toast.js";

export class EventsManager {
  /**
   * @param {import('../models/event-bus.js').EventBus} bus
   * @param {import('../models/lineup-model.js').LineupModel} model
   * @param {import('../services/storage.js').StorageManager} storage
   */
  constructor(bus, model, storage) {
    this._bus = bus;
    this._model = model;
    this._storage = storage;
    this._onLoad = null; // callback set by App for wiring slot rebuild
  }

  init() {
    this._list = document.getElementById("saved-events-list");
    document.getElementById("btn-save-event")?.addEventListener("click", () => this._saveCurrentEvent());
    document.getElementById("btn-new-event")?.addEventListener("click", () => this._newEvent());
    document.getElementById("btn-saved-events-drawer")?.addEventListener("click", () => this._toggleDrawer());
    this.refresh();
  }

  /** App sets this so EventsManager can trigger a full UI reload. */
  setLoadCallback(fn) {
    this._onLoad = fn;
  }

  // ── Public ─────────────────────────────────────────────────────────────

  refresh() {
    if (!this._list) return;
    this._list.innerHTML = "";

    const events = this._storage.getEvents();
    const names = Object.keys(events).sort();

    const countEl = document.getElementById("saved-events-count");
    if (countEl) {
      countEl.hidden = names.length === 0;
      countEl.textContent = names.length;
    }

    if (!names.length) {
      const empty = document.createElement("p");
      empty.className = "muted-text";
      empty.textContent = "No saved events.";
      this._list.appendChild(empty);
    } else {
      names.forEach((name) => {
        this._list.appendChild(this._buildEventCard(name, events[name]));
      });
    }
  }

  // ── Private ────────────────────────────────────────────────────────────

  _toggleDrawer() {
    const drawer = document.getElementById("saved-events-drawer");
    const body = this._list;
    if (!drawer || !body) return;
    const opening = !drawer.classList.contains("open");
    drawer.classList.toggle("open", opening);
    body.hidden = !opening;
    const chevron = drawer.querySelector(".discord-drawer__chevron");
    if (chevron) chevron.textContent = opening ? "expand_less" : "expand_more";
  }

  _buildEventCard(name, data) {
    const card = document.createElement("div");
    card.className = "event-card";

    const nameEl = document.createElement("span");
    nameEl.className = "event-card__name";
    nameEl.textContent = name;

    const actions = document.createElement("div");
    actions.className = "event-card__actions";

    const loadBtn = document.createElement("button");
    loadBtn.className = "btn btn--icon";
    loadBtn.title = "Load";
    loadBtn.innerHTML = '<span class="material-symbols-rounded">folder_open</span>';
    loadBtn.addEventListener("click", () => this._loadEvent(name, data));

    const dupBtn = document.createElement("button");
    dupBtn.className = "btn btn--icon";
    dupBtn.title = "Duplicate";
    dupBtn.innerHTML = '<span class="material-symbols-rounded">content_copy</span>';
    dupBtn.addEventListener("click", () => this._duplicateEvent(name, data));

    const delBtn = document.createElement("button");
    delBtn.className = "btn btn--icon btn--danger";
    delBtn.title = "Delete";
    delBtn.innerHTML = '<span class="material-symbols-rounded">delete</span>';
    delBtn.addEventListener("click", () => this._confirmDeleteEvent(name));

    actions.append(loadBtn, dupBtn, delBtn);
    card.append(nameEl, actions);
    return card;
  }

  _saveCurrentEvent() {
    const currentName = this._model.title?.trim() || "Untitled Event";
    this._showNameDialog(currentName, "Save Event", (name) => {
      if (!name?.trim()) return;
      const key = name.trim();

      const existing = this._storage.getEvents();
      if (existing[key]) {
        this._confirmOverwrite(key, () => {
          this._doSave(key);
        });
      } else {
        this._doSave(key);
      }
    });
  }

  _doSave(name) {
    this._storage.saveEvent(name, this._model.toObject());
    this.refresh();
    this._showToast(`Saved "${name}"`);
  }

  _loadEvent(name, data) {
    const hasContent = this._model.title?.trim() ||
      this._model.slots.some((s) => s.name?.trim() || s.genre?.trim());

    const doLoad = () => {
      this._model.loadFromObject(data);
      this._onLoad?.();
      this._showToast(`Loaded "${name}"`);
    };

    if (hasContent) {
      this._confirmDialog(
        `Load "${name}"? Unsaved changes will be lost.`,
        "Load", "Cancel",
        doLoad
      );
    } else {
      doLoad();
    }
  }

  _duplicateEvent(name, data) {
    const newName = `${name} (copy)`;
    this._showNameDialog(newName, "Duplicate Event", (n) => {
      if (!n?.trim()) return;
      this._storage.saveEvent(n.trim(), { ...data });
      this.refresh();
    });
  }

  _confirmDeleteEvent(name) {
    this._confirmDialog(
      `Delete "${name}"? This cannot be undone.`,
      "Delete", "Cancel",
      () => {
        this._storage.deleteEvent(name);
        this.refresh();
      }
    );
  }

  _newEvent() {
    const hasContent = this._model.title?.trim() ||
      this._model.slots.some((s) => s.name?.trim());

    const doNew = () => {
      this._model.clear();
      this._onLoad?.();
    };

    if (hasContent) {
      this._confirmDialog("Start a new event? Unsaved changes will be lost.", "New Event", "Cancel", doNew);
    } else {
      doNew();
    }
  }

  _confirmOverwrite(name, onConfirm) {
    this._confirmDialog(`"${name}" already exists. Overwrite it?`, "Overwrite", "Cancel", onConfirm);
  }

  // ── Modal helpers (use shared overlay directly to avoid circular deps) ──

  _confirmDialog(message, confirmLabel, cancelLabel, onConfirm) {
    const overlay = document.getElementById("modal-overlay");
    const container = document.getElementById("modal-container");
    if (!overlay || !container) return;

    container.innerHTML = `
      <div class="modal__body">
        <p class="modal__message">${this._esc(message)}</p>
        <div class="modal__actions">
          <button class="btn btn--secondary" id="_ev-cancel">${this._esc(cancelLabel)}</button>
          <button class="btn btn--primary" id="_ev-confirm">${this._esc(confirmLabel)}</button>
        </div>
      </div>`;
    overlay.hidden = false;

    const close = () => { overlay.hidden = true; container.innerHTML = ""; };
    container.querySelector("#_ev-confirm")?.addEventListener("click", () => { close(); onConfirm?.(); });
    container.querySelector("#_ev-cancel")?.addEventListener("click", close);
  }

  _showNameDialog(defaultName, title, onSave) {
    const overlay = document.getElementById("modal-overlay");
    const container = document.getElementById("modal-container");
    if (!overlay || !container) return;

    container.innerHTML = `
      <div class="modal__body">
        <h3 class="modal__title">${this._esc(title)}</h3>
        <input class="input" id="_ev-name" type="text"
               value="${this._esc(defaultName)}" placeholder="Event name" />
        <div class="modal__actions">
          <button class="btn btn--secondary" id="_ev-cancel">Cancel</button>
          <button class="btn btn--primary" id="_ev-save">Save</button>
        </div>
      </div>`;
    overlay.hidden = false;

    const close = () => { overlay.hidden = true; container.innerHTML = ""; };
    const input = container.querySelector("#_ev-name");

    const save = () => {
      const val = input?.value?.trim() ?? "";
      close();
      onSave(val);
    };

    container.querySelector("#_ev-save")?.addEventListener("click", save);
    container.querySelector("#_ev-cancel")?.addEventListener("click", close);
    input?.addEventListener("keydown", (e) => { if (e.key === "Enter") save(); });
    requestAnimationFrame(() => { input?.select(); });
  }

  _showToast(message) {
    showToast(message, "success");
  }

  _esc(str) {
    return String(str ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }
}
