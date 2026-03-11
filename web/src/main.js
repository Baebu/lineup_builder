/**
 * Main entry point for Lineup Builder Web.
 *
 * Wires up the EventBus, LineupModel, and all UI managers.
 */
import { EventBus } from "./models/event-bus.js";
import { LineupModel, SlotData, DJInfo } from "./models/lineup-model.js";
import { StorageManager } from "./services/storage.js";
import { ApiClient } from "./services/api-client.js";
import { CloudSync } from "./services/cloud-sync.js";
import { OutputGenerator } from "./output/output-generator.js";
import { ThemeManager } from "./ui/theme-manager.js";
import { TabManager } from "./ui/tab-manager.js";
import { SlotManager } from "./ui/slot-manager.js";
import { RosterManager } from "./ui/roster-manager.js";
import { GenreManager } from "./ui/genre-manager.js";
import { EventsManager } from "./ui/events-manager.js";
import { OutputManager } from "./ui/output-manager.js";
import { SettingsManager } from "./ui/settings-manager.js";
import { ModalManager } from "./ui/modal-manager.js";
import { DragDropManager } from "./ui/drag-drop-manager.js";
import { ResizeManager } from "./ui/resize-manager.js";
import { DiscordManager } from "./ui/discord-manager.js";
import { DJManager } from "./ui/dj-manager.js";
import { ClubManager } from "./ui/club-manager.js";
import { AuthManager } from "./ui/auth-manager.js";
import { ImageStorageService } from "./services/image-storage.js";
import { openImportDialog } from "./output/import-parser.js";

class App {
  constructor() {
    // Core services
    this.bus = new EventBus();
    this.model = new LineupModel(this.bus);
    this.storage = new StorageManager();
    this.api = new ApiClient();
    this.cloud = new CloudSync(this.api, this.storage);
    this.images = new ImageStorageService();
    this.outputGen = new OutputGenerator();

    // UI managers
    this.theme = new ThemeManager(this.bus, this.storage);
    this.tabs = new TabManager();
    this.modal = new ModalManager();
    this.slots = new SlotManager(this.bus, this.model, this.storage);
    this.roster = new RosterManager(this.bus, this.model, this.storage, this.api);
    this.genres = new GenreManager(this.bus, this.model, this.storage);
    this.events = new EventsManager(this.bus, this.model, this.storage);
    this.output = new OutputManager(this.bus, this.model, this.outputGen);
    this.settings = new SettingsManager(this.bus, this.storage, this.theme);
    this.dragDrop = new DragDropManager(this.bus, this.model, this.slots);
    this.resize = new ResizeManager();
    this.discord = new DiscordManager(this.bus, this.model, this.api, this.modal, this.images);
    this.dj = new DJManager(this.bus, this.api, this.modal, this.storage, this.images, this.tabs);
    this.club = new ClubManager(this.bus, this.api, this.modal, this.storage, this.tabs);
    this.auth = new AuthManager(this.api, this.modal, this.storage, this.bus);
  }

  init() {
    // Load persisted data
    this.storage.load();
    this._loadData();

    // Wire EventsManager load callback → sync UI after model is loaded
    this.events.setLoadCallback(() => this._syncUIFromModel());

    // Initialize all UI managers
    this.theme.init();
    this.tabs.init();
    this.slots.init();
    this.roster.init();
    this.genres.init();
    this.events.init();
    this.output.init();
    this.settings.init();
    this.dragDrop.init();
    this.resize.init();
    this.discord.init();
    this.dj.init();
    this.club.init();
    this.auth.init();
    this.modal.init();

    // Bind top-level event inputs to model
    this._bindEventInputs();
    this._initSocialLinks();

    // Wire Import button
    document.getElementById("btn-import")?.addEventListener("click", () => {
      openImportDialog(this.modal, (parsed) => this._applyParsedEvent(parsed));
    });

    // Check for auto-save recovery
    this._checkAutoSave();

    // Start auto-save timer
    this._startAutoSave();

    // Listen for model changes → update output
    this.bus.subscribe("model_changed", () => this.output.update());

    // Refresh club-link toggle previews when club data is updated
    this.bus.subscribe("club_updated", () => {
      document.querySelectorAll("[data-social-preview]").forEach((el) => {
        const label = el.dataset.socialPreview;
        if (label === "DISCORD") {
          const url = this.storage.getSettings()?.club_discord ?? "";
          el.textContent = url || "Configure in Club tab";
          el.classList.toggle("social-link-preview--empty", !url);
        } else if (label === "VRC GROUP") {
          const url = this.storage.getSettings()?.club_vrc_group_url ?? "";
          el.textContent = url || "Configure in Club tab";
          el.classList.toggle("social-link-preview--empty", !url);
        }
      });
    });

    // Listen for post_loaded (discord history item loaded into editor) → sync input fields
    this.bus.subscribe("post_loaded", () => this._syncUIFromModel());

    // Listen for library changes → push to cloud
    this.bus.subscribe("library_changed", () => {
      const data = { djs: this.model.savedDjs.map((d) => d.toObject()), genres: this.model.genres };
      this.cloud.saveLibrary(data);
    });

    // Wire collapsible fieldset sections
    this._initCollapsibleSections();
  }

  _initCollapsibleSections() {
    document.addEventListener("click", (e) => {
      const toggle = e.target.closest(".fieldset__toggle");
      if (!toggle) return;
      const fieldset = toggle.closest(".fieldset--collapsible");
      if (!fieldset) return;

      const expanded = toggle.getAttribute("aria-expanded") === "true";
      toggle.setAttribute("aria-expanded", String(!expanded));
      fieldset.classList.toggle("fieldset--collapsed", expanded);

      // Persist collapsed state
      const key = fieldset.dataset.section;
      if (key) {
        const collapsed = JSON.parse(localStorage.getItem("lineup_sections") || "{}");
        collapsed[key] = expanded; // true means now collapsed
        localStorage.setItem("lineup_sections", JSON.stringify(collapsed));
      }
    });

    // Restore saved collapsed states
    const collapsed = JSON.parse(localStorage.getItem("lineup_sections") || "{}");
    for (const [key, isCollapsed] of Object.entries(collapsed)) {
      if (!isCollapsed) continue;
      const fieldset = document.querySelector(`.fieldset--collapsible[data-section="${key}"]`);
      if (!fieldset) continue;
      fieldset.classList.add("fieldset--collapsed");
      const toggle = fieldset.querySelector(".fieldset__toggle");
      if (toggle) toggle.setAttribute("aria-expanded", "false");
    }
  }

  _initSocialLinks() {
    const labels = ["TIMELINE", "VRCPOP", "X", "IG"];
    const container = document.getElementById("social-links-container");
    if (!container) return;

    container.innerHTML = "";
    for (const label of labels) {
      const row = document.createElement("div");
      row.className = "field-row";
      row.innerHTML = `
        <label class="field-label" style="width:72px">${label}</label>
        <input data-social-label="${label}" class="input input--sm"
               style="flex:1" placeholder="https://..." />`;
      container.appendChild(row);

      const input = row.querySelector(`[data-social-label="${label}"]`);
      input?.addEventListener("input", () => {
        this.model.socialLinks[label] = input.value;
        this.model.notify();
      });
    }

    // DISCORD and VRC GROUP pull from the club tab — render as include-toggles
    this._initClubLinkToggle(container, "DISCORD", () => this.storage.getSettings()?.club_discord ?? "");
    this._initClubLinkToggle(container, "VRC GROUP", () => this.storage.getSettings()?.club_vrc_group_url ?? "");
  }

  _initClubLinkToggle(container, label, getUrl) {
    const row = document.createElement("div");
    row.className = "field-row";
    row.innerHTML = `
      <label class="field-label" style="width:72px">${label}</label>
      <button class="btn btn--sm social-link-toggle" data-social-toggle="${label}" aria-pressed="false">Include</button>
      <span class="social-link-preview" data-social-preview="${label}"></span>`;
    container.appendChild(row);

    const btn = row.querySelector(`[data-social-toggle="${label}"]`);
    const preview = row.querySelector(`[data-social-preview="${label}"]`);

    const refreshPreview = () => {
      const url = getUrl();
      if (url) {
        preview.textContent = url;
        preview.classList.remove("social-link-preview--empty");
      } else {
        preview.textContent = "Configure in Club tab";
        preview.classList.add("social-link-preview--empty");
      }
    };

    btn?.addEventListener("click", () => {
      const wasOn = btn.getAttribute("aria-pressed") === "true";
      const turnOn = !wasOn;
      btn.setAttribute("aria-pressed", String(turnOn));
      btn.classList.toggle("social-link-toggle--on", turnOn);
      this.model.socialLinks[label] = turnOn ? (getUrl() || "") : "";
      this.model.notify();
    });

    refreshPreview();
    return refreshPreview;
  }

  _bindEventInputs() {
    const $ = (id) => document.getElementById(id);

    const sync = () => {
      this.model.title = $("event-title").value;
      this.model.vol = $("event-vol").value;
      this.model.groupName = $("group-name").value;
      this.model.collabWith = $("collab-with").value;

      const dt = $("event-datetime")?.value;
      if (dt) {
        // datetime-local gives "YYYY-MM-DDTHH:MM" — convert to "YYYY-MM-DD HH:MM"
        this.model.timestamp = dt.replace("T", " ");
      }
      this.model.namesOnly = $("names-only").checked;
      this.model.notify();
    };

    // Attach input listeners
    for (const id of [
      "event-title",
      "event-vol",
      "group-name",
      "collab-with",
      "event-datetime",
    ]) {
      $(id)?.addEventListener("input", sync);
    }

    $("names-only")?.addEventListener("change", sync);
  }

  /**
   * Load library + events. Server-first when signed in, localStorage fallback.
   * Mirrors desktop data_manager.load_data().
   */
  async _loadData() {
    try {
      const { djs, genres } = await this.cloud.loadAll();
      this.model.savedDjs = djs.map((d) => new DJInfo(d));
      this.model.genres = genres ?? [];
    } catch (e) {
      console.warn("_loadData: cloud load failed, using localStorage:", e);
      this.model.savedDjs = this.storage.getDjs().map((d) => new DJInfo(d));
      this.model.genres = this.storage.getGenres();
    }
  }

  _checkAutoSave() {
    const state = this.storage.getAutoSave();
    if (!state || state.cleanClose) return;

    const hasContent =
      state.title?.trim() ||
      state.slots?.some((s) => s.name?.trim() || s.genre?.trim());
    if (!hasContent) return;

    const label = state.title?.trim()
      ? `Unsaved lineup found — "${state.title.trim()}". Restore it?`
      : "An unsaved lineup was found. Restore it?";

    this.modal.confirm(label, "Restore", "Discard", () => {
      this._loadAutoSaveState(state);
    });
  }

  _loadAutoSaveState(state) {
    this.model.loadFromObject(state);
    this._syncUIFromModel();
  }

  _syncUIFromModel() {
    // Sync top-level input fields from model state
    const $ = (id) => document.getElementById(id);
    $("event-title").value = this.model.title;
    $("event-vol").value = this.model.vol;
    $("group-name").value = this.model.groupName;
    $("collab-with").value = this.model.collabWith;
    $("names-only").checked = this.model.namesOnly;

    if (this.model.timestamp) {
      // Model stores "YYYY-MM-DD HH:MM" — convert to "YYYY-MM-DDTHH:MM" for datetime-local
      $("event-datetime").value = this.model.timestamp.replace(" ", "T");
    } else {
      $("event-datetime").value = "";
    }

    // Sync social links
    document.querySelectorAll("[data-social-label]").forEach((input) => {
      input.value = this.model.socialLinks[input.dataset.socialLabel] ?? "";
    });

    // Sync club-link toggle buttons
    document.querySelectorAll("[data-social-toggle]").forEach((btn) => {
      const label = btn.dataset.socialToggle;
      const isOn = !!(this.model.socialLinks[label]);
      btn.setAttribute("aria-pressed", String(isOn));
      btn.classList.toggle("social-link-toggle--on", isOn);
    });

    this.slots.rebuildFromModel();
    this.genres.refresh();
    this.model.notify();
  }

  _applyParsedEvent(parsed) {
    if (!parsed) return;

    if (parsed.title) this.model.title = parsed.title;
    if (parsed.vol) this.model.vol = parsed.vol;
    if (parsed.timestamp) this.model.timestamp = parsed.timestamp;
    if (parsed.genres?.length) this.model.genres = parsed.genres;
    if (parsed.namesOnly != null) this.model.namesOnly = parsed.namesOnly;

    if (parsed.socialLinks && Object.keys(parsed.socialLinks).length) {
      Object.assign(this.model.socialLinks, parsed.socialLinks);
    }

    if (parsed.slots?.length) {
      this.model.slots = parsed.slots.map((s) => new SlotData({
        name: s.name ?? "",
        genre: s.genre ?? "",
        duration: s.duration ?? 60,
      }));
    }

    // Add DJ names to saved library (LOCAL) if not already present
    if (parsed.slots?.length) {
      for (const slot of parsed.slots) {
        const name = slot.name?.trim();
        if (name && !this.model.savedDjs.some((d) => d.name === name)) {
          this.model.savedDjs.push({ name, stream: "", exactLink: false });
        }
      }
      this.storage.saveDjs(this.model.savedDjs);
    }

    this._syncUIFromModel();
  }

  _startAutoSave() {
    setInterval(() => {
      this.storage.saveAutoState(this.model.toObject());
    }, 5000);

    // Mark clean close on page unload
    window.addEventListener("beforeunload", () => {
      this.storage.saveAutoState({ cleanClose: true });
    });
  }
}

// Boot
document.addEventListener("DOMContentLoaded", () => {
  const app = new App();
  app.init();
  window.__app = app; // debug access
});
