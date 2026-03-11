/**
 * GenreManager — manages genre tags in the Event tab.
 *
 * Features:
 *   • Add new genre via input + button (or Enter key)
 *   • Delete genre tag
 *   • Toggle genre active/inactive (active genres appear on the event snapshot)
 *   • Persists genre list to storage
 *
 * Mirrors desktop GenreMixin.
 */
export class GenreManager {
  /**
   * @param {import('../models/event-bus.js').EventBus} bus
   * @param {import('../models/lineup-model.js').LineupModel} model
   * @param {import('../services/storage.js').StorageManager} storage
   */
  constructor(bus, model, storage) {
    this._bus = bus;
    this._model = model;
    this._storage = storage;

    /** All known genre tags (master list from library). */
    this._allGenres = [];
    /** Currently-active genre names (subset shown in event output). */
    this._activeGenres = new Set();
    this._filter = "";
    this._eventFilter = "";
  }

  init() {
    // Event tab elements
    this._eventTags = document.getElementById("genre-tags");
    this._eventEntry = document.getElementById("genre-entry");

    // Load saved genres
    this._allGenres = [...(this._storage.getGenres() ?? [])];
    this._activeGenres = new Set(this._model.genres ?? []);

    // Event tab: add genre
    document.getElementById("btn-add-genre")?.addEventListener("click", () => this._addFromInput(this._eventEntry));
    this._eventEntry?.addEventListener("keydown", (e) => {
      if (e.key === "Enter") this._addFromInput(this._eventEntry);
    });
    // Event tab: filter and show matching genres
    this._eventEntry?.addEventListener("input", (e) => {
      this._eventFilter = e.target.value.toLowerCase();
      this._refreshEventTags();
    });

    this.refresh();
  }

  // ── Public ─────────────────────────────────────────────────────────────

  refresh() {
    this._refreshEventTags();
  }

  // ── Event tab genres (#genre-tags) ─────────────────────────────────────

  _refreshEventTags() {
    if (!this._eventTags) return;
    this._eventTags.innerHTML = "";

    const filter = this._eventFilter;
    const visible = filter
      ? this._allGenres.filter((g) => g.toLowerCase().includes(filter))
      : this._allGenres;

    if (!visible.length) {
      const empty = document.createElement("p");
      empty.className = "muted-text";
      empty.textContent = filter ? "No genres match." : "No genres yet — add one.";
      this._eventTags.appendChild(empty);
      return;
    }

    for (const genre of visible) {
      this._eventTags.appendChild(this._buildTag(genre, false));
    }
  }

  // ── Shared ─────────────────────────────────────────────────────────────

  _buildTag(genre, showDelete) {
    const tag = document.createElement("span");
    tag.className = "genre-tag" + (this._activeGenres.has(genre) ? " genre-tag--active" : "");
    tag.textContent = genre;

    tag.addEventListener("click", () => this._toggleGenre(genre));

    if (showDelete) {
      const delBtn = document.createElement("button");
      delBtn.className = "genre-tag__delete";
      delBtn.title = "Remove genre";
      delBtn.innerHTML = '<span class="material-symbols-rounded">close</span>';
      delBtn.addEventListener("click", (e) => {
        e.stopPropagation();
        this._deleteGenre(genre);
      });
      tag.appendChild(delBtn);
    }

    return tag;
  }

  _addFromInput(input) {
    const val = input?.value?.trim() ?? "";
    if (!val) return;
    if (this._allGenres.some((g) => g.toLowerCase() === val.toLowerCase())) {
      // Already exists — just activate it
      this._activeGenres.add(
        this._allGenres.find((g) => g.toLowerCase() === val.toLowerCase())
      );
      if (input) input.value = "";
      this._syncModel();
      this.refresh();
      return;
    }
    this._allGenres.push(val);
    this._activeGenres.add(val);
    if (input) input.value = "";
    this._eventFilter = "";
    this._persist();
    this.refresh();
  }

  _toggleGenre(genre) {
    if (this._activeGenres.has(genre)) {
      this._activeGenres.delete(genre);
    } else {
      this._activeGenres.add(genre);
    }
    this._syncModel();
    this.refresh();
  }

  _deleteGenre(genre) {
    this._allGenres = this._allGenres.filter((g) => g !== genre);
    this._activeGenres.delete(genre);
    this._persist();
    this.refresh();
  }

  _syncModel() {
    this._model.genres = [...this._activeGenres];
    this._model.notify();
  }

  _persist() {
    this._storage.saveGenres(this._allGenres);
    this._syncModel();
  }
}
