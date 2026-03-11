/**
 * DragDropManager — handles two drag interactions:
 *
 *   1. Slot reordering: drag a slot row by its handle to reorder within #slots-container.
 *   2. DJ card → slot: drop a DJ card onto a slot name input to fill it.
 *
 * Mirrors desktop DragDropMixin.
 */
export class DragDropManager {
  /**
   * @param {import('../models/event-bus.js').EventBus} bus
   * @param {import('../models/lineup-model.js').LineupModel} model
   * @param {import('./slot-manager.js').SlotManager} slots
   */
  constructor(bus, model, slots) {
    this._bus = bus;
    this._model = model;
    this._slots = slots;
    this._dragSrc = null; // slot row element being dragged
  }

  init() {
    const container = document.getElementById("slots-container");
    if (!container) return;

    // Slot → slot reordering (event delegation on the container)
    container.addEventListener("dragstart", (e) => this._onSlotDragStart(e));
    container.addEventListener("dragover", (e) => this._onSlotDragOver(e));
    container.addEventListener("drop", (e) => this._onSlotDrop(e));
    container.addEventListener("dragend", (e) => this._onSlotDragEnd(e));

    // DJ card dropped onto a slot name input or open container area
    container.addEventListener("dragover", (e) => {
      if (e.dataTransfer.types.includes("text/dj-name")) {
        e.preventDefault();
        e.dataTransfer.dropEffect = "copy";
        const input = e.target.closest(".slot-row__name");
        if (input) input.classList.add("drop-target");
      }
    });

    container.addEventListener("dragleave", (e) => {
      const input = e.target.closest(".slot-row__name");
      if (input) input.classList.remove("drop-target");
    });

    container.addEventListener("drop", (e) => {
      const djName = e.dataTransfer.getData("text/dj-name");
      if (!djName) return;
      const input = e.target.closest(".slot-row__name");
      if (input) {
        // Drop onto existing slot name → fill it
        input.classList.remove("drop-target");
        input.value = djName;
        input.dispatchEvent(new Event("input", { bubbles: true }));
        const row = input.closest(".slot-row");
        if (row) this._slots.flashSlot(row);
      } else {
        // Drop onto container area (not a specific slot) → create new slot
        e.preventDefault();
        this._slots.addSlotWithName(djName);
      }
    });
  }

  // ── Slot reordering ────────────────────────────────────────────────────

  _onSlotDragStart(e) {
    const row = e.target.closest(".slot-row");
    const handle = e.target.closest(".slot-row__handle");
    // Only allow drag when initiated from the handle
    if (!row || !handle) {
      e.preventDefault();
      return;
    }
    this._dragSrc = row;
    e.dataTransfer.effectAllowed = "move";
    e.dataTransfer.setData("text/slot-row-id", row.dataset.rowId ?? "");
    row.classList.add("slot-row--dragging");
  }

  _onSlotDragOver(e) {
    if (!this._dragSrc) return;
    // Ignore DJ-name drags in this handler
    if (e.dataTransfer.types.includes("text/dj-name")) return;

    e.preventDefault();
    e.dataTransfer.dropEffect = "move";

    const target = e.target.closest(".slot-row");
    if (!target || target === this._dragSrc) return;

    // Visual indicator
    const container = document.getElementById("slots-container");
    container.querySelectorAll(".slot-row").forEach((r) => r.classList.remove("drop-above", "drop-below"));

    const rect = target.getBoundingClientRect();
    const midY = rect.top + rect.height / 2;
    if (e.clientY < midY) {
      target.classList.add("drop-above");
    } else {
      target.classList.add("drop-below");
    }
  }

  _onSlotDrop(e) {
    if (!this._dragSrc) return;
    if (e.dataTransfer.types.includes("text/dj-name")) return;

    e.preventDefault();

    const target = e.target.closest(".slot-row");
    if (!target || target === this._dragSrc) return;

    const container = document.getElementById("slots-container");
    container.querySelectorAll(".slot-row").forEach((r) => r.classList.remove("drop-above", "drop-below"));

    const rect = target.getBoundingClientRect();
    const midY = rect.top + rect.height / 2;
    if (e.clientY < midY) {
      target.before(this._dragSrc);
    } else {
      target.after(this._dragSrc);
    }

    this._slots.syncOrderFromDOM();
    this._slots.flashSlot(this._dragSrc);
  }

  _onSlotDragEnd(e) {
    const container = document.getElementById("slots-container");
    container?.querySelectorAll(".slot-row").forEach((r) => {
      r.classList.remove("slot-row--dragging", "drop-above", "drop-below");
    });
    this._dragSrc = null;
  }
}
