/**
 * ThemeManager — applies CSS custom property tokens from a settings object.
 *
 * Port of desktop SettingsMixin.apply_theme().
 */

const DEFAULT_SETTINGS = {
  primary_color:   "#7c3aed",
  primary_hover:   "#6d28d9",
  secondary_color: "#2d1b5c",
  secondary_hover: "#4c288a",
  success_color:   "#059669",
  success_hover:   "#047857",
  danger_color:    "#dc2626",
  danger_hover:    "#b91c1c",
  accent_color:    "#c4b5fd",
  panel_bg:        "#160d2e",
  card_bg:         "#09051a",
  border_color:    "#3b1f6e",
  hover_color:     "#4c288a",
  scrollbar_color: "#3b1f6e",
  text_primary:    "#ede9fe",
  text_secondary:  "#c4b5fd",
};

const SLATE_SETTINGS = {
  primary_color:   "#4f46e5",
  primary_hover:   "#4338ca",
  secondary_color: "#334155",
  secondary_hover: "#475569",
  success_color:   "#059669",
  success_hover:   "#047857",
  danger_color:    "#dc2626",
  danger_hover:    "#b91c1c",
  accent_color:    "#818cf8",
  panel_bg:        "#1e293b",
  card_bg:         "#0f172a",
  border_color:    "#334155",
  hover_color:     "#475569",
  scrollbar_color: "#475569",
  text_primary:    "#cbd5e1",
  text_secondary:  "#94a3b8",
};

export const BUILTIN_PRESETS = [
  {
    name: "Slate",
    settings: { ...SLATE_SETTINGS },
  },
  {
    name: "Midnight Blue",
    settings: {
      ...DEFAULT_SETTINGS,
      primary_color:   "#3b82f6",
      primary_hover:   "#2563eb",
      accent_color:    "#93c5fd",
      panel_bg:        "#0d1526",
      card_bg:         "#060d1a",
      border_color:    "#1e3a5f",
      hover_color:     "#1e3a5f",
      scrollbar_color: "#1e3a5f",
      text_primary:    "#e2e8f0",
      text_secondary:  "#93c5fd",
    },
  },
  {
    name: "OLED Black",
    settings: {
      ...DEFAULT_SETTINGS,
      primary_color:   "#6366f1",
      primary_hover:   "#4f46e5",
      accent_color:    "#a5b4fc",
      panel_bg:        "#111111",
      card_bg:         "#000000",
      border_color:    "#27272a",
      hover_color:     "#3f3f46",
      scrollbar_color: "#27272a",
      text_primary:    "#f4f4f5",
      text_secondary:  "#a1a1aa",
    },
  },
  {
    name: "Crimson",
    settings: {
      ...DEFAULT_SETTINGS,
      primary_color:   "#e11d48",
      primary_hover:   "#be123c",
      accent_color:    "#fda4af",
      secondary_color: "#3d1f27",
      secondary_hover: "#5c2d3a",
      panel_bg:        "#1a0d11",
      card_bg:         "#0d0608",
      border_color:    "#4c1d30",
      hover_color:     "#5c2d3a",
      scrollbar_color: "#4c1d30",
      text_primary:    "#fce7f3",
      text_secondary:  "#fda4af",
    },
  },
  {
    name: "Amber",
    settings: {
      ...DEFAULT_SETTINGS,
      primary_color:   "#d97706",
      primary_hover:   "#b45309",
      accent_color:    "#fcd34d",
      secondary_color: "#2d1f07",
      secondary_hover: "#3d2c0e",
      panel_bg:        "#1c1508",
      card_bg:         "#0e0b04",
      border_color:    "#44300a",
      hover_color:     "#5c4114",
      scrollbar_color: "#44300a",
      text_primary:    "#fef3c7",
      text_secondary:  "#fcd34d",
    },
  },
  {
    name: "Forest",
    settings: {
      ...DEFAULT_SETTINGS,
      primary_color:   "#059669",
      primary_hover:   "#047857",
      success_color:   "#d97706",
      success_hover:   "#b45309",
      accent_color:    "#6ee7b7",
      secondary_color: "#0d2b1f",
      secondary_hover: "#163d2c",
      panel_bg:        "#0b1f17",
      card_bg:         "#04100b",
      border_color:    "#1a4030",
      hover_color:     "#1e5039",
      scrollbar_color: "#1a4030",
      text_primary:    "#d1fae5",
      text_secondary:  "#6ee7b7",
    },
  },
  {
    name: "Ocean",
    settings: {
      ...DEFAULT_SETTINGS,
      primary_color:   "#0891b2",
      primary_hover:   "#0e7490",
      accent_color:    "#67e8f9",
      secondary_color: "#0c2233",
      secondary_hover: "#14344d",
      panel_bg:        "#091d2c",
      card_bg:         "#040e16",
      border_color:    "#164e63",
      hover_color:     "#1a607a",
      scrollbar_color: "#164e63",
      text_primary:    "#cffafe",
      text_secondary:  "#67e8f9",
    },
  },
  {
    name: "Violet (Default)",
    settings: { ...DEFAULT_SETTINGS },
  },
];

/** Map settings keys → CSS variable names */
const TOKEN_MAP = {
  primary_color:   "--color-primary",
  primary_hover:   "--color-primary-hover",
  secondary_color: "--color-secondary",
  secondary_hover: "--color-secondary-hover",
  success_color:   "--color-success",
  success_hover:   "--color-success-hover",
  danger_color:    "--color-danger",
  danger_hover:    "--color-danger-hover",
  accent_color:    "--color-accent",
  panel_bg:        "--color-panel-bg",
  card_bg:         "--color-card-bg",
  border_color:    "--color-border",
  hover_color:     "--color-hover",
  scrollbar_color: "--color-scrollbar",
  text_primary:    "--color-text-primary",
  text_secondary:  "--color-text-secondary",
};

export class ThemeManager {
  constructor(bus, storage) {
    this._bus = bus;
    this._storage = storage;
    /** @type {Object} current settings token map */
    this.settings = { ...DEFAULT_SETTINGS };
    this._userPresets = [];
  }

  init() {
    const saved = this._storage.getSettings();
    if (saved?.preset) {
      const match = BUILTIN_PRESETS.find((p) => p.name === saved.preset);
      if (match) this.settings = { ...match.settings };
    } else if (saved && saved.primary_color) {
      // custom token overrides saved directly
      this.settings = { ...DEFAULT_SETTINGS, ...saved };
    }
    this._userPresets = saved?.user_presets ?? [];
    this.apply();
  }

  /** Apply current settings to CSS custom properties on :root */
  apply() {
    const root = document.documentElement.style;
    for (const [key, cssVar] of Object.entries(TOKEN_MAP)) {
      const value = this.settings[key];
      if (value) root.setProperty(cssVar, value);
    }
    this._bus.publish("theme_changed", { settings: this.settings });
  }

  applyPreset(name) {
    const preset =
      BUILTIN_PRESETS.find((p) => p.name === name) ??
      this._userPresets.find((p) => p.name === name);
    if (!preset) return;
    this.settings = { ...preset.settings };
    this.apply();
    this._saveSettings(name);
  }

  /** Active preset name, or null if custom */
  activePresetName() {
    return (
      BUILTIN_PRESETS.find((p) => p.settings.panel_bg === this.settings.panel_bg)?.name ??
      this._userPresets.find((p) => p.settings.panel_bg === this.settings.panel_bg)?.name ??
      null
    );
  }

  /** Apply an arbitrary settings object (e.g. a user preset). */
  applySettings(settings) {
    this.settings = { ...DEFAULT_SETTINGS, ...settings };
    this.apply();
  }

  /** Return a shallow copy of the current settings token map. */
  currentSettings() {
    return { ...this.settings };
  }

  allPresets() {
    return [...BUILTIN_PRESETS, ...this._userPresets];
  }

  _saveSettings(presetName) {
    const existing = this._storage.getSettings();
    this._storage.saveSettings({ ...existing, preset: presetName });
  }
}
