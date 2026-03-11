/**
 * RosterManager — renders the DJ library in LOCAL and BOOKED sections.
 *
 * LOCAL  — the user's saved DJ library (persisted to storage).
 * BOOKED — DJs fetched from the server booking history for the current club.
 *
 * Mirrors desktop RosterMixin (LOCAL + BOOKED split).
 */
import { DJInfo } from "../models/lineup-model.js";

export class RosterManager {
  /**
   * @param {import('../models/event-bus.js').EventBus} bus
   * @param {import('../models/lineup-model.js').LineupModel} model
   * @param {import('../services/storage.js').StorageManager} storage
   * @param {import('../services/api-client.js').ApiClient} [api]
   */
  constructor(bus, model, storage, api = null) {
    this._bus = bus;
    this._model = model;
    this._storage = storage;
    this._api = api;
    this._filter = "";
    this._bookedDjs = [];
    this._bookedLoading = false;
  }

  init() {
    this._localList = document.getElementById("roster-local-list");
    this._bookedList = document.getElementById("roster-booked-list");
    this._searchInput = document.getElementById("roster-search");

    document.getElementById("btn-add-dj")?.addEventListener("click", () => this._showAddDialog());
    document.getElementById("btn-import-dj-links")?.addEventListener("click", () => this._showBulkImportDialog());

    this._searchInput?.addEventListener("input", (e) => {
      this._filter = e.target.value.toLowerCase();
      this.refresh();
    });

    this._bus.subscribe("model_changed", () => this.refresh());

    // Edit DJ from slot — triggered by SlotManager
    this._bus.subscribe("edit_dj", (data) => {
      if (data?.index != null) this._showEditDialog(data.index);
    });

    this.refresh();
    this._fetchBookedDjs();
  }

  // ── Public ─────────────────────────────────────────────────────────────

  refresh() {
    this._refreshLocalList();
    this._refreshBookedList();
  }

  // ── LOCAL section ──────────────────────────────────────────────────────

  _refreshLocalList() {
    if (!this._localList) return;
    this._localList.innerHTML = "";

    const djs = this._model.savedDjs;
    const filter = this._filter;
    const visible = filter
      ? djs.filter((d) => d.name.toLowerCase().includes(filter))
      : djs;

    if (!visible.length) {
      const empty = document.createElement("p");
      empty.className = "muted-text";
      empty.textContent = filter ? "No DJs match your search." : "No DJs yet — add one above.";
      this._localList.appendChild(empty);
      return;
    }

    visible.forEach((dj) => {
      const realIdx = this._model.savedDjs.indexOf(dj);
      this._localList.appendChild(this._buildCard(dj, realIdx));
    });
  }

  // ── BOOKED section ─────────────────────────────────────────────────────

  _refreshBookedList() {
    if (!this._bookedList) return;
    this._bookedList.innerHTML = "";

    const filter = this._filter;
    const visible = filter
      ? this._bookedDjs.filter((d) => d.name.toLowerCase().includes(filter))
      : this._bookedDjs;

    if (!visible.length) {
      const empty = document.createElement("p");
      empty.className = "muted-text";
      if (this._bookedLoading) {
        empty.textContent = "Loading booking history...";
      } else if (!this._api) {
        empty.textContent = "Server not connected.";
      } else if (filter) {
        empty.textContent = "No booked DJs match your search.";
      } else {
        empty.textContent = "No booking history found.";
      }
      this._bookedList.appendChild(empty);
      return;
    }

    visible.forEach((dj) => {
      this._bookedList.appendChild(this._buildBookedCard(dj));
    });
  }

  _buildBookedCard(dj) {
    const card = document.createElement("div");
    card.className = "dj-card";
    card.draggable = true;
    card.dataset.djName = dj.name;

    card.addEventListener("dragstart", (e) => {
      e.dataTransfer.setData("text/dj-name", dj.name);
      e.dataTransfer.effectAllowed = "copy";
      card.classList.add("dragging");
    });
    card.addEventListener("dragend", () => card.classList.remove("dragging"));

    const icon = document.createElement("span");
    icon.className = "material-symbols-rounded dj-card__icon";
    icon.textContent = "person";

    const info = document.createElement("div");
    info.className = "dj-card__info";

    const name = document.createElement("span");
    name.className = "dj-card__name";
    name.textContent = dj.name;

    const badge = document.createElement("span");
    badge.className = "dj-card__link muted-text";
    badge.textContent = "BOOKED";

    info.append(name, badge);

    const actions = document.createElement("div");
    actions.className = "dj-card__actions";

    const alreadyLocal = this._model.savedDjs.some(
      (d) => d.name.toLowerCase() === dj.name.toLowerCase()
    );

    if (!alreadyLocal) {
      const saveBtn = document.createElement("button");
      saveBtn.className = "btn btn--icon";
      saveBtn.title = "Save to LOCAL";
      saveBtn.innerHTML = '<span class="material-symbols-rounded">save</span>';
      saveBtn.addEventListener("click", (e) => {
        e.stopPropagation();
        this._saveBookedToLocal(dj);
      });
      actions.append(saveBtn);
    }

    card.append(icon, info, actions);
    return card;
  }

  _saveBookedToLocal(dj) {
    if (this._model.savedDjs.some((d) => d.name.toLowerCase() === dj.name.toLowerCase())) return;
    this._model.savedDjs.push(new DJInfo({ name: dj.name, stream: dj.stream ?? "", exactLink: dj.exactLink ?? false }));
    this._persist();
    this.refresh();
  }

  async _fetchBookedDjs() {
    if (!this._api) return;
    const groupName = this._model.groupName?.trim();
    if (!groupName) return;

    this._bookedLoading = true;
    this._refreshBookedList();

    try {
      const bookings = await this._api.listGroupBookings(groupName);
      const seen = new Set();
      this._bookedDjs = (Array.isArray(bookings) ? bookings : []).filter((dj) => {
        const key = dj.name?.toLowerCase();
        if (!key || seen.has(key)) return false;
        seen.add(key);
        return true;
      });
    } catch {
      this._bookedDjs = [];
    } finally {
      this._bookedLoading = false;
      this._refreshBookedList();
    }
  }

  // ── DJ card (LOCAL) ────────────────────────────────────────────────────

  _buildCard(dj, idx) {
    const card = document.createElement("div");
    card.className = "dj-card";
    card.draggable = true;
    card.dataset.djName = dj.name;

    card.addEventListener("dragstart", (e) => {
      e.dataTransfer.setData("text/dj-name", dj.name);
      e.dataTransfer.effectAllowed = "copy";
      card.classList.add("dragging");
    });
    card.addEventListener("dragend", () => card.classList.remove("dragging"));

    const icon = document.createElement("span");
    icon.className = "material-symbols-rounded dj-card__icon";
    icon.textContent = "person";

    const info = document.createElement("div");
    info.className = "dj-card__info";

    const name = document.createElement("span");
    name.className = "dj-card__name";
    name.textContent = dj.name;

    const link = document.createElement("span");
    link.className = "dj-card__link muted-text";
    link.textContent = dj.stream ? (dj.exactLink ? "(exact link)" : dj.stream) : "No stream link";

    info.append(name, link);

    const actions = document.createElement("div");
    actions.className = "dj-card__actions";

    const editBtn = document.createElement("button");
    editBtn.className = "btn btn--icon";
    editBtn.title = "Edit";
    editBtn.innerHTML = '<span class="material-symbols-rounded">edit</span>';
    editBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      this._showEditDialog(idx);
    });

    const delBtn = document.createElement("button");
    delBtn.className = "btn btn--icon btn--danger";
    delBtn.title = "Remove";
    delBtn.innerHTML = '<span class="material-symbols-rounded">delete</span>';
    delBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      this._deleteDj(idx);
    });

    actions.append(editBtn, delBtn);
    card.append(icon, info, actions);
    return card;
  }

  _showAddDialog() {
    this._showDjDialog(null, null, (name, stream, exactLink) => {
      if (!name.trim()) return;
      this._model.savedDjs.push(new DJInfo({ name: name.trim(), stream, exactLink }));
      this._persist();
      this.refresh();
    });
  }

  _showEditDialog(idx) {
    const dj = this._model.savedDjs[idx];
    if (!dj) return;
    this._showDjDialog(dj.name, dj.stream, (name, stream, exactLink) => {
      if (!name.trim()) return;
      this._model.savedDjs[idx] = new DJInfo({ name: name.trim(), stream, exactLink });
      this._persist();
      this.refresh();
    }, dj.exactLink);
  }

  _showDjDialog(defaultName, defaultStream, onSave, defaultExact = false) {
    const overlay = document.getElementById("modal-overlay");
    const container = document.getElementById("modal-container");
    if (!overlay || !container) return;

    const exactChecked = defaultExact ? "checked" : "";
    container.innerHTML = `
      <div class="modal__body">
        <h3 class="modal__title">${defaultName ? "Edit DJ" : "Add DJ"}</h3>
        <label class="label">Name</label>
        <input class="input" id="dj-dialog-name" type="text"
               value="${this._esc(defaultName ?? "")}" placeholder="DJ name" />
        <label class="label" style="margin-top:0.75rem">Stream Link</label>
        <input class="input" id="dj-dialog-stream" type="text"
               value="${this._esc(defaultStream ?? "")}" placeholder="VRCDN or custom URL" />
        <div class="checkbox-row" style="margin-top:0.5rem">
          <input type="checkbox" id="dj-dialog-exact" ${exactChecked} />
          <label for="dj-dialog-exact">Use link as-is (exact link)</label>
        </div>
        <div class="modal__actions">
          <button class="btn btn--secondary" id="dj-dialog-cancel">Cancel</button>
          <button class="btn btn--primary" id="dj-dialog-save">Save</button>
        </div>
      </div>`;
    overlay.hidden = false;

    const close = () => { overlay.hidden = true; container.innerHTML = ""; };

    const save = () => {
      const name = container.querySelector("#dj-dialog-name")?.value ?? "";
      const stream = container.querySelector("#dj-dialog-stream")?.value?.trim() ?? "";
      const exact = container.querySelector("#dj-dialog-exact")?.checked ?? false;
      close();
      onSave(name, stream, exact);
    };

    container.querySelector("#dj-dialog-save")?.addEventListener("click", save);
    container.querySelector("#dj-dialog-cancel")?.addEventListener("click", close);
    container.querySelector("#dj-dialog-name")?.addEventListener("keydown", (e) => {
      if (e.key === "Enter") save();
    });

    requestAnimationFrame(() => container.querySelector("#dj-dialog-name")?.focus());
  }

  // ── Bulk DJ Link Import ──────────────────────────────────────────────

  _showBulkImportDialog() {
    const overlay = document.getElementById("modal-overlay");
    const container = document.getElementById("modal-container");
    if (!overlay || !container) return;

    container.innerHTML = `
      <div class="modal__body" style="width:500px;max-width:90vw">
        <h3 class="modal__title">Import DJ Links</h3>
        <p class="muted-text">Paste text containing DJ names and stream links. Accepted formats:<br>
          <code>DJ Name - https://link</code> or <code>DJ Name https://link</code></p>
        <textarea class="input" id="bulk-import-text" rows="10"
                  placeholder="DJ Alpha - https://vrcdn.live/alpha&#10;DJ Beta https://vrcdn.live/beta&#10;DJ Gamma"
                  style="width:100%;resize:vertical;font-family:monospace;font-size:var(--text-sm)"></textarea>
        <div id="bulk-import-preview" style="margin-top:0.5rem"></div>
        <div class="modal__actions">
          <button class="btn btn--secondary" id="bulk-import-cancel">Cancel</button>
          <button class="btn btn--secondary" id="bulk-import-parse">Preview</button>
          <button class="btn btn--primary" id="bulk-import-save">Import</button>
        </div>
      </div>`;
    overlay.hidden = false;

    const close = () => { overlay.hidden = true; container.innerHTML = ""; };
    let parsed = [];

    container.querySelector("#bulk-import-cancel")?.addEventListener("click", close);

    container.querySelector("#bulk-import-parse")?.addEventListener("click", () => {
      const text = container.querySelector("#bulk-import-text")?.value ?? "";
      parsed = this._parseBulkLinks(text);
      const preview = container.querySelector("#bulk-import-preview");
      if (!preview) return;
      if (!parsed.length) {
        preview.innerHTML = '<p class="muted-text">No DJ entries found.</p>';
        return;
      }
      preview.innerHTML = parsed.map((p) =>
        `<div class="field-row" style="padding:2px 0">
          <span style="flex:1">${this._esc(p.name)}</span>
          <span class="muted-text" style="flex:1;text-overflow:ellipsis;overflow:hidden">${this._esc(p.stream || "—")}</span>
        </div>`
      ).join("");
    });

    container.querySelector("#bulk-import-save")?.addEventListener("click", () => {
      const text = container.querySelector("#bulk-import-text")?.value ?? "";
      if (!parsed.length) parsed = this._parseBulkLinks(text);
      if (!parsed.length) return;

      let added = 0;
      for (const entry of parsed) {
        const exists = this._model.savedDjs.some(
          (d) => d.name.toLowerCase() === entry.name.toLowerCase()
        );
        if (!exists) {
          this._model.savedDjs.push(new DJInfo({
            name: entry.name,
            stream: entry.stream,
            exactLink: false,
          }));
          added++;
        }
      }
      this._persist();
      this.refresh();
      close();
    });

    requestAnimationFrame(() => container.querySelector("#bulk-import-text")?.focus());
  }

  _parseBulkLinks(text) {
    const results = [];
    const lines = text.split(/\n/).map((l) => l.trim()).filter(Boolean);
    const urlRe = /https?:\/\/\S+/i;

    for (const line of lines) {
      const urlMatch = line.match(urlRe);
      let name, stream = "";
      if (urlMatch) {
        stream = urlMatch[0];
        name = line.slice(0, urlMatch.index).replace(/[\s\-–—]+$/, "").trim();
      } else {
        name = line.replace(/[\s\-–—]+$/, "").trim();
      }
      if (name) results.push({ name, stream });
    }
    return results;
  }

  _deleteDj(idx) {
    this._model.savedDjs.splice(idx, 1);
    this._persist();
    this.refresh();
  }

  _persist() {
    this._storage.saveDjs(this._model.savedDjs.map((d) => d.toObject()));
    this._model.notify();
  }

  _esc(str) {
    return String(str ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }
}
