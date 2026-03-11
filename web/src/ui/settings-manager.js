/**
 * SettingsManager — settings drawer: theme presets, user presets, color pickers.
 *
 * Wires #btn-settings to open/close the drawer.
 * Populates #theme-preset <select> with built-in + user presets.
 * Adds per-token color pickers matching desktop settings_manager.py.
 * Delegates theme application to ThemeManager, and persists settings via storage.
 *
 * Mirrors desktop SettingsMixin.
 */
import { BUILTIN_PRESETS } from "./theme-manager.js";

/** Human-readable labels for token keys, grouped. */
const COLOR_GROUPS = [
  {
    label: "Backgrounds",
    tokens: [
      ["panel_bg", "Panel"],
      ["card_bg", "Card / Input"],
      ["border_color", "Borders"],
      ["hover_color", "Hover"],
      ["scrollbar_color", "Scrollbar"],
    ],
  },
  {
    label: "Text",
    tokens: [
      ["text_primary", "Primary"],
      ["text_secondary", "Secondary"],
      ["accent_color", "Accent"],
    ],
  },
  {
    label: "Buttons",
    tokens: [
      ["primary_color", "Primary"],
      ["primary_hover", "Primary Hover"],
      ["secondary_color", "Secondary"],
      ["secondary_hover", "Secondary Hover"],
      ["success_color", "Success"],
      ["success_hover", "Success Hover"],
      ["danger_color", "Danger"],
      ["danger_hover", "Danger Hover"],
    ],
  },
];

export class SettingsManager {
  /**
   * @param {import('../models/event-bus.js').EventBus} bus
   * @param {import('../services/storage.js').StorageManager} storage
   * @param {import('./theme-manager.js').ThemeManager} theme
   */
  constructor(bus, storage, theme) {
    this._bus = bus;
    this._storage = storage;
    this._theme = theme;
    this._colorInputs = {};
  }

  init() {
    this._overlay = document.getElementById("settings-overlay");
    this._drawer = document.getElementById("settings-drawer");
    this._presetSelect = document.getElementById("theme-preset");

    document.getElementById("btn-settings")?.addEventListener("click", () => this._open());
    document.getElementById("btn-close-settings")?.addEventListener("click", () => this._close());
    this._overlay?.addEventListener("click", (e) => {
      if (e.target === this._overlay) this._close();
    });
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && !this._overlay?.hidden) this._close();
    });

    this._buildDrawerBody();
    this._populatePresets();
  }

  // ── Private ────────────────────────────────────────────────────────────

  _open() {
    this._syncColorInputs();
    if (this._overlay) this._overlay.hidden = false;
    requestAnimationFrame(() => this._drawer?.classList.add("drawer--open"));
  }

  _close() {
    this._drawer?.classList.remove("drawer--open");
    setTimeout(() => {
      if (this._overlay) this._overlay.hidden = true;
    }, 250);
  }

  _buildDrawerBody() {
    const body = this._drawer?.querySelector(".drawer__body");
    if (!body) return;

    // Preset section
    const section = body.querySelector(".section");
    if (!section) return;

    // Preset action buttons
    const actRow = document.createElement("div");
    actRow.className = "preset-actions";
    actRow.style.cssText = "margin-top:0.5rem;display:flex;gap:0.5rem";

    const saveBtn = document.createElement("button");
    saveBtn.className = "btn btn--primary btn--sm";
    saveBtn.textContent = "Save as Preset";
    saveBtn.addEventListener("click", () => this._saveUserPreset());

    const delBtn = document.createElement("button");
    delBtn.className = "btn btn--danger btn--sm";
    delBtn.id = "btn-delete-preset";
    delBtn.textContent = "Delete Preset";
    delBtn.addEventListener("click", () => this._deleteUserPreset());

    actRow.append(saveBtn, delBtn);
    section.appendChild(actRow);

    this._presetSelect?.addEventListener("change", () => this._onPresetChange());

    // Color picker groups
    for (const group of COLOR_GROUPS) {
      const sec = document.createElement("section");
      sec.className = "section";

      const title = document.createElement("label");
      title.className = "label";
      title.textContent = group.label;
      sec.appendChild(title);

      for (const [key, label] of group.tokens) {
        const row = document.createElement("div");
        row.className = "color-picker-row";

        const lbl = document.createElement("span");
        lbl.className = "color-picker-label";
        lbl.textContent = label;

        const picker = document.createElement("input");
        picker.type = "color";
        picker.className = "color-picker-input";
        picker.dataset.tokenKey = key;
        picker.addEventListener("input", () => this._onColorChange(key, picker.value));

        this._colorInputs[key] = picker;

        row.append(lbl, picker);
        sec.appendChild(row);
      }

      body.appendChild(sec);
    }
  }

  _syncColorInputs() {
    const current = this._theme.currentSettings();
    for (const [key, input] of Object.entries(this._colorInputs)) {
      if (current[key]) input.value = current[key];
    }
  }

  _onColorChange(key, value) {
    const current = this._theme.currentSettings();
    current[key] = value;
    this._theme.applySettings(current);
  }

  _populatePresets() {
    if (!this._presetSelect) return;
    this._presetSelect.innerHTML = "";

    const builtinGroup = document.createElement("optgroup");
    builtinGroup.label = "Built-in";
    BUILTIN_PRESETS.forEach((p) => {
      const opt = document.createElement("option");
      opt.value = `builtin:${p.name}`;
      opt.textContent = p.name;
      builtinGroup.appendChild(opt);
    });
    this._presetSelect.appendChild(builtinGroup);

    const saved = this._storage.getSettings();
    const userPresets = Array.isArray(saved?.user_presets) ? saved.user_presets : [];

    if (userPresets.length) {
      const userGroup = document.createElement("optgroup");
      userGroup.label = "My Presets";
      userPresets.forEach((p) => {
        const opt = document.createElement("option");
        opt.value = `user:${p.name}`;
        opt.textContent = p.name;
        userGroup.appendChild(opt);
      });
      this._presetSelect.appendChild(userGroup);
    }

    const activeName = saved?.active_preset ?? BUILTIN_PRESETS[0].name;
    const match = [...this._presetSelect.options].find((o) => o.textContent === activeName);
    if (match) this._presetSelect.value = match.value;

    this._onPresetChange();
  }

  _onPresetChange() {
    const val = this._presetSelect?.value ?? "";
    const delBtn = document.getElementById("btn-delete-preset");
    if (delBtn) delBtn.disabled = val.startsWith("builtin:");

    const settings = this._resolveSettings(val);
    if (settings) {
      this._theme.applySettings(settings);
      this._persistActivePreset(val);
      this._syncColorInputs();
    }
  }

  _resolveSettings(val) {
    if (val.startsWith("builtin:")) {
      const name = val.slice(8);
      return BUILTIN_PRESETS.find((p) => p.name === name)?.settings ?? null;
    }
    if (val.startsWith("user:")) {
      const name = val.slice(5);
      const saved = this._storage.getSettings();
      return (saved?.user_presets ?? []).find((p) => p.name === name)?.settings ?? null;
    }
    return null;
  }

  _saveUserPreset() {
    const name = window.prompt("Enter a name for this preset:");
    if (!name?.trim()) return;

    const saved = this._storage.getSettings() ?? {};
    const userPresets = Array.isArray(saved.user_presets) ? [...saved.user_presets] : [];
    const current = this._theme.currentSettings();
    const existing = userPresets.findIndex((p) => p.name === name.trim());
    if (existing >= 0) {
      userPresets[existing] = { name: name.trim(), settings: current };
    } else {
      userPresets.push({ name: name.trim(), settings: current });
    }

    this._storage.saveSettings({ ...saved, user_presets: userPresets });
    this._populatePresets();

    const opt = [...(this._presetSelect?.options ?? [])].find((o) => o.textContent === name.trim());
    if (opt) {
      this._presetSelect.value = opt.value;
      this._onPresetChange();
    }
  }

  _deleteUserPreset() {
    const val = this._presetSelect?.value ?? "";
    if (!val.startsWith("user:")) return;
    const name = val.slice(5);

    if (!confirm(`Delete preset "${name}"?`)) return;

    const saved = this._storage.getSettings() ?? {};
    const userPresets = (saved.user_presets ?? []).filter((p) => p.name !== name);
    this._storage.saveSettings({ ...saved, user_presets: userPresets });
    this._populatePresets();
  }

  _persistActivePreset(val) {
    const saved = this._storage.getSettings() ?? {};
    const name = val.startsWith("builtin:") ? val.slice(8) : val.startsWith("user:") ? val.slice(5) : val;
    this._storage.saveSettings({ ...saved, active_preset: name });
  }
}
