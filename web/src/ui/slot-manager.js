/**
 * SlotManager — renders and manages lineup slots in #slots-container.
 *
 * Each slot row:
 *   • Drag handle for reordering
 *   • Computed time label
 *   • Duration dropdown (15–120 min in 15-min steps)
 *   • DJ name input with autocomplete suggestions
 *   • LINK indicator (green if DJ has stream, red if not)
 *   • Edit DJ button
 *   • Genre input
 *   • Delete button
 *
 * Mirrors desktop SlotMixin / SlotState / slot_ui.py.
 */
import { SlotData } from "../models/lineup-model.js";
import { OutputGenerator } from "../output/output-generator.js";

const DURATION_OPTIONS = [15, 30, 45, 60, 75, 90, 105, 120];
let _nextId = 1;

export class SlotManager {
  /**
   * @param {import('../models/event-bus.js').EventBus} bus
   * @param {import('../models/lineup-model.js').LineupModel} model
   * @param {import('../services/storage.js').StorageManager} storage
   */
  constructor(bus, model, storage) {
    this._bus = bus;
    this._model = model;
    this._storage = storage;
    this._container = null;
    this._slotIds = [];
    this._activeSuggest = null; // currently-open suggestion dropdown
  }

  init() {
    this._container = document.getElementById("slots-container");

    document.getElementById("btn-add-slot")?.addEventListener("click", () => {
      this._addSlot();
    });

    this._bus.subscribe("model_changed", () => {
      this._updateTimeLabels();
      this._updateAllLinkIndicators();
      this._updateConflicts();
    });

    // Dismiss autocomplete when clicking elsewhere
    document.addEventListener("click", (e) => {
      if (this._activeSuggest && !this._activeSuggest.contains(e.target)) {
        this._closeSuggestions();
      }
    });
  }

  // ── Public API ─────────────────────────────────────────────────────────

  rebuildFromModel() {
    if (!this._container) return;
    this._container.innerHTML = "";
    this._slotIds = [];
    for (const slot of this._model.slots) {
      this._renderSlot(slot);
    }
    this._updateTimeLabels();
    this._updateAllLinkIndicators();
  }

  getSlotRows() {
    return [...this._container.querySelectorAll(".slot-row")];
  }

  syncOrderFromDOM() {
    const newSlots = [];
    const rows = this.getSlotRows();
    for (const row of rows) {
      const idx = parseInt(row.dataset.slotIdx, 10);
      if (!isNaN(idx) && this._model.slots[idx]) {
        newSlots.push(this._model.slots[idx]);
      }
    }
    this._model.slots = newSlots;
    this._reindexRows();
    this._model.notify();
  }

  /** Flash accent border on a slot row for visual feedback (e.g. after drag-drop). */
  flashSlot(row) {
    row.classList.add("slot-row--flash");
    setTimeout(() => row.classList.remove("slot-row--flash"), 400);
  }

  /** Create a new slot pre-filled with a DJ name (used by DragDropManager). */
  addSlotWithName(name) {
    const slot = new SlotData();
    slot.name = name;
    this._addSlot(slot);
    // Flash the newly added row
    const container = document.getElementById("slots-container");
    const lastRow = container?.lastElementChild;
    if (lastRow) this.flashSlot(lastRow);
  }

  // ── Private ────────────────────────────────────────────────────────────

  _addSlot(slotData = null) {
    const slot = slotData ?? new SlotData();
    this._model.slots.push(slot);
    this._renderSlot(slot);
    this._updateTimeLabels();
    this._model.notify();
  }

  _renderSlot(slot) {
    const idx = this._model.slots.indexOf(slot);
    const id = _nextId++;

    const row = document.createElement("div");
    row.className = "slot-row";
    row.dataset.slotIdx = idx;
    row.dataset.rowId = id;
    row.draggable = true;

    // Build duration <select> options
    const durVal = slot.duration ?? 60;
    const durOptions = DURATION_OPTIONS.map(
      (d) => `<option value="${d}" ${d === durVal ? "selected" : ""}>${d}</option>`
    ).join("");
    // If custom duration not in list, add it
    const hasCustom = !DURATION_OPTIONS.includes(durVal);
    const extraOpt = hasCustom
      ? `<option value="${durVal}" selected>${durVal}</option>`
      : "";

    row.innerHTML = `
      <span class="slot-row__handle material-symbols-rounded" title="Drag to reorder">drag_indicator</span>
      <span class="slot-row__time">--:--</span>
      <select class="select select--sm slot-row__duration" data-field="duration" title="Duration (minutes)">
        ${durOptions}${extraOpt}
      </select>
      <div class="slot-row__name-wrapper">
        <input class="input input--sm slot-row__name" placeholder="DJ Name"
               value="${this._esc(slot.name)}" data-field="name" autocomplete="off" />
        <div class="slot-row__suggest" hidden></div>
      </div>
      <span class="slot-row__conflict" hidden title="">
        <span class="material-symbols-rounded">warning</span>
      </span>
      <span class="slot-row__link-indicator" title="Stream link status">
        <span class="material-symbols-rounded">link</span>
      </span>
      <button class="btn btn--icon slot-row__edit" title="Edit DJ">
        <span class="material-symbols-rounded">edit</span>
      </button>
      <input class="input input--sm slot-row__genre" placeholder="Genre"
             value="${this._esc(slot.genre)}" data-field="genre" />
      <button class="btn btn--icon btn--danger slot-row__delete" title="Remove slot">
        <span class="material-symbols-rounded">delete</span>
      </button>`;

    // ── Field change → model sync ──
    const nameInput = row.querySelector(".slot-row__name");
    const genreInput = row.querySelector(".slot-row__genre");
    const durSelect = row.querySelector(".slot-row__duration");

    nameInput?.addEventListener("input", () => {
      const s = this._model.slots[parseInt(row.dataset.slotIdx, 10)];
      if (!s) return;
      s.name = nameInput.value;
      this._model.notify();
      this._updateLinkIndicator(row, s);
      this._showSuggestions(row, nameInput.value);
    });

    genreInput?.addEventListener("input", () => {
      const s = this._model.slots[parseInt(row.dataset.slotIdx, 10)];
      if (!s) return;
      s.genre = genreInput.value;
      this._model.notify();
    });

    durSelect?.addEventListener("change", () => {
      const s = this._model.slots[parseInt(row.dataset.slotIdx, 10)];
      if (!s) return;
      s.duration = parseInt(durSelect.value, 10) || 60;
      this._model.notify();
    });

    // ── Autocomplete: show all DJs on focus (if input not empty, filter) ──
    nameInput?.addEventListener("focus", () => {
      this._showSuggestions(row, nameInput.value);
    });

    // ── Edit DJ button ──
    row.querySelector(".slot-row__edit")?.addEventListener("click", () => {
      const s = this._model.slots[parseInt(row.dataset.slotIdx, 10)];
      if (!s) return;
      this._editDjFromSlot(s.name?.trim());
    });

    // ── Delete ──
    row.querySelector(".slot-row__delete")?.addEventListener("click", () => {
      const slotIdx = parseInt(row.dataset.slotIdx, 10);
      this._model.slots.splice(slotIdx, 1);
      row.remove();
      this._reindexRows();
      this._model.notify();
    });

    this._container.appendChild(row);
    this._slotIds.push(id);
    this._updateLinkIndicator(row, slot);
  }

  // ── Autocomplete ─────────────────────────────────────────────────────

  _showSuggestions(row, query) {
    const suggestEl = row.querySelector(".slot-row__suggest");
    if (!suggestEl) return;

    const q = (query ?? "").trim().toLowerCase();
    const allNames = this._model.savedDjs.map((d) => d.name);
    const matches = q
      ? allNames.filter((n) => n.toLowerCase().includes(q))
      : allNames;

    if (!matches.length) {
      suggestEl.hidden = true;
      this._activeSuggest = null;
      return;
    }

    suggestEl.innerHTML = "";
    for (const name of matches.slice(0, 8)) {
      const item = document.createElement("div");
      item.className = "suggest-item";
      item.textContent = name;
      item.addEventListener("mousedown", (e) => {
        e.preventDefault(); // prevent blur before click fires
        const nameInput = row.querySelector(".slot-row__name");
        if (nameInput) {
          nameInput.value = name;
          nameInput.dispatchEvent(new Event("input", { bubbles: true }));
        }
        this._closeSuggestions();
      });
      suggestEl.appendChild(item);
    }
    suggestEl.hidden = false;
    this._activeSuggest = suggestEl;
  }

  _closeSuggestions() {
    if (this._activeSuggest) {
      this._activeSuggest.hidden = true;
      this._activeSuggest = null;
    }
  }

  // ── LINK indicator ───────────────────────────────────────────────────

  _updateLinkIndicator(row, slot) {
    const indicator = row.querySelector(".slot-row__link-indicator");
    if (!indicator) return;
    const name = (slot.name ?? "").trim();
    const dj = this._model.savedDjs.find(
      (d) => d.name.toLowerCase() === name.toLowerCase()
    );
    const hasStream = !!(dj && dj.stream);
    indicator.classList.toggle("slot-row__link-indicator--active", hasStream);
    indicator.title = hasStream ? `Stream: ${dj.stream}` : "No stream link";
  }

  _updateAllLinkIndicators() {
    const rows = this.getSlotRows();
    rows.forEach((row) => {
      const idx = parseInt(row.dataset.slotIdx, 10);
      const s = this._model.slots[idx];
      if (s) this._updateLinkIndicator(row, s);
    });
  }

  // ── Edit DJ from slot ────────────────────────────────────────────────

  _editDjFromSlot(name) {
    if (!name) return;
    const idx = this._model.savedDjs.findIndex(
      (d) => d.name.toLowerCase() === name.toLowerCase()
    );
    if (idx >= 0) {
      // Publish event so RosterManager can open its edit dialog
      this._bus.publish("edit_dj", { index: idx });
    } else {
      // DJ not in roster — add then edit
      this._model.savedDjs.push({ name, stream: "", exactLink: false });
      this._bus.publish("roster_changed");
      const newIdx = this._model.savedDjs.length - 1;
      this._bus.publish("edit_dj", { index: newIdx });
    }
  }

  // ── Helpers ──────────────────────────────────────────────────────────

  _reindexRows() {
    const rows = this.getSlotRows();
    rows.forEach((row, i) => { row.dataset.slotIdx = i; });
  }

  // ── Conflict detection ───────────────────────────────────────────────

  /**
   * Compute { name (lowercase), start (ms), end (ms) } windows for a
   * slots array + ISO/datetime-local timestamp string.
   */
  _slotWindows(timestamp, slots) {
    if (!timestamp || !slots?.length) return [];
    const ts = timestamp.replace(" ", "T");
    const startMs = new Date(ts).getTime();
    if (isNaN(startMs)) return [];
    const windows = [];
    let ptr = startMs;
    for (let i = 0; i < slots.length; i++) {
      const slot = slots[i];
      const dur = (Number(slot.duration) || 60) * 60000;
      const name = (slot.name ?? "").trim();
      if (name) windows.push({ name: name.toLowerCase(), display: name, slotIdx: i, start: ptr, end: ptr + dur });
      ptr += dur;
    }
    return windows;
  }

  _updateConflicts() {
    const rows = this.getSlotRows();
    if (!rows.length) return;

    // Build current event windows
    const current = this._slotWindows(this._model.timestamp, this._model.slots);

    // Map: slotIdx → array of conflict messages
    const msgs = new Map();
    const addMsg = (idx, msg) => {
      if (!msgs.has(idx)) msgs.set(idx, []);
      msgs.get(idx).push(msg);
    };

    // 1. Same-lineup duplicates
    const seen = new Map(); // name → first slotIdx
    for (const w of current) {
      if (seen.has(w.name)) {
        const firstIdx = seen.get(w.name);
        addMsg(firstIdx, `"${w.display}" is also in slot ${w.slotIdx + 1}`);
        addMsg(w.slotIdx, `"${w.display}" is also in slot ${firstIdx + 1}`);
      } else {
        seen.set(w.name, w.slotIdx);
      }
    }

    // 2. Cross-event conflicts
    if (this._storage) {
      const savedEvents = this._storage.getEvents();
      for (const [evtName, evt] of Object.entries(savedEvents)) {
        const other = this._slotWindows(evt.timestamp, evt.slots);
        if (!other.length) continue;
        // Quick overall overlap check
        const curStart = current[0]?.start;
        const curEnd = current[current.length - 1]?.end;
        const otherStart = other[0]?.start;
        const otherEnd = other[other.length - 1]?.end;
        if (!curStart || !otherStart || curEnd <= otherStart || otherEnd <= curStart) continue;
        // Slot-level check
        for (const cw of current) {
          for (const ow of other) {
            if (cw.name !== ow.name) continue;
            if (cw.end <= ow.start || ow.end <= cw.start) continue;
            const fmt = (ms) => {
              const d = new Date(ms);
              return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
            };
            addMsg(cw.slotIdx, `Conflicts with "${evtName}" (${fmt(ow.start)}–${fmt(ow.end)})`);
          }
        }
      }
    }

    // Apply to rows
    rows.forEach((row) => {
      const idx = parseInt(row.dataset.slotIdx, 10);
      const indicator = row.querySelector(".slot-row__conflict");
      if (!indicator) return;
      const rowMsgs = msgs.get(idx);
      if (rowMsgs?.length) {
        indicator.title = rowMsgs.join("\n");
        indicator.hidden = false;
        row.classList.add("slot-row--conflict");
      } else {
        indicator.hidden = true;
        indicator.title = "";
        row.classList.remove("slot-row--conflict");
      }
    });
  }

  _updateTimeLabels() {
    const rows = this.getSlotRows();
    if (!rows.length) return;

    const snap = this._model.snapshot();
    const times = OutputGenerator.computeSlotTimes(snap);

    rows.forEach((row, i) => {
      const label = row.querySelector(".slot-row__time");
      if (label) label.textContent = times[i] ?? "--:--";
    });

    this._updateConflicts();
  }

  _esc(str) {
    return String(str ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }
}
