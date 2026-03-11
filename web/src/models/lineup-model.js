/**
 * LineupModel — pure JS port of desktop/src/backend/models/lineup_model.py
 *
 * Mutable runtime model. Every setter publishes "model_changed" on the bus
 * so subscribers (output panel, auto-save, etc.) can react.
 */

export class SlotData {
  constructor({ name = "", genre = "", duration = 60 } = {}) {
    this.name = name;
    this.genre = genre;
    this.duration = Number(duration) || 60;
  }

  clone() {
    return new SlotData({ name: this.name, genre: this.genre, duration: this.duration });
  }

  toObject() {
    return { name: this.name, genre: this.genre, duration: this.duration };
  }
}

export class DJInfo {
  constructor({ name = "", stream = "", exactLink, exact_link } = {}) {
    this.name = name;
    this.stream = stream;
    this.exactLink = Boolean(exactLink ?? exact_link ?? false);
  }

  clone() {
    return new DJInfo({ name: this.name, stream: this.stream, exactLink: this.exactLink });
  }

  toObject() {
    return { name: this.name, stream: this.stream, exactLink: this.exactLink };
  }
}

/**
 * An immutable snapshot of the full event state — passed to OutputGenerator.
 */
export class EventSnapshot {
  constructor({
    title = "",
    vol = "",
    groupName = "",
    collab = false,
    collabWith = "",
    timestamp = "",
    genres = [],
    slots = [],
    namesOnly = false,
    outputFormat = "discord",
    streamLinkFormat = "",
    savedDjs = [],
    socialLinks = {},
    discordRoleMentions = [],
  } = {}) {
    this.title = title;
    this.vol = vol;
    this.groupName = groupName;
    this.collab = collab;
    this.collabWith = collabWith;
    this.timestamp = timestamp;
    this.genres = [...genres];
    this.slots = slots.map((s) => (s instanceof SlotData ? s.clone() : new SlotData(s)));
    this.namesOnly = namesOnly;
    this.outputFormat = outputFormat;
    this.streamLinkFormat = streamLinkFormat;
    this.savedDjs = savedDjs.map((d) => (d instanceof DJInfo ? d.clone() : new DJInfo(d)));
    this.socialLinks = { ...socialLinks };
    this.discordRoleMentions = [...discordRoleMentions];
  }

  get startDatetime() {
    if (!this.timestamp) return new Date();
    const d = new Date(this.timestamp.replace(" ", "T"));
    return isNaN(d.getTime()) ? new Date() : d;
  }

  get fullTitle() {
    let base = /^\d+$/.test(this.vol) ? `${this.title} VOL.${this.vol}` : this.title;
    if (this.collab && this.collabWith) {
      base += ` x ${this.collabWith}`;
    }
    return base;
  }
}

/**
 * The mutable runtime model backing the editor UI.
 */
export class LineupModel {
  constructor(bus) {
    this._bus = bus;

    this.title = "";
    this.vol = "";
    this.groupName = "";
    this.collab = false;
    this.collabWith = "";
    this.timestamp = "";
    this.genres = [];
    this.slots = [];
    this.namesOnly = false;
    this.outputFormat = "discord";
    this.streamLinkFormat = ""; // "" | "quest" | "pc"
    this.savedDjs = [];
    this.socialLinks = {};
    this.discordRoleMentions = []; // [{id, name}]
  }

  // ── Snapshot ──────────────────────────────────────────────────────────

  snapshot() {
    return new EventSnapshot({
      title: this.title,
      vol: this.vol,
      groupName: this.groupName,
      collab: this.collab,
      collabWith: this.collabWith,
      timestamp: this.timestamp,
      genres: [...this.genres],
      slots: this.slots.map((s) => s instanceof SlotData ? s.clone() : new SlotData(s)),
      namesOnly: this.namesOnly,
      outputFormat: this.outputFormat,
      streamLinkFormat: this.streamLinkFormat,
      savedDjs: this.savedDjs.map((d) => d instanceof DJInfo ? d.clone() : new DJInfo(d)),
      socialLinks: { ...this.socialLinks },
      discordRoleMentions: this.discordRoleMentions.map((r) => ({ ...r })),
    });
  }

  // ── Serialization ──────────────────────────────────────────────────────

  toObject() {
    return {
      title: this.title,
      vol: this.vol,
      groupName: this.groupName,
      collab: this.collab,
      collabWith: this.collabWith,
      timestamp: this.timestamp,
      genres: [...this.genres],
      slots: this.slots.map((s) => s.toObject()),
      namesOnly: this.namesOnly,
      outputFormat: this.outputFormat,
      streamLinkFormat: this.streamLinkFormat,
      socialLinks: { ...this.socialLinks },
      discordRoleMentions: this.discordRoleMentions.map((r) => ({ ...r })),
    };
  }

  loadFromObject(data) {
    this.title = data.title ?? "";
    this.vol = data.vol ?? "";
    this.groupName = data.groupName ?? "";
    this.collab = Boolean(data.collab);
    this.collabWith = data.collabWith ?? "";
    this.timestamp = data.timestamp ?? "";
    this.genres = Array.isArray(data.genres) ? [...data.genres] : [];
    this.slots = Array.isArray(data.slots)
      ? data.slots.map((s) => new SlotData(s))
      : [];
    this.namesOnly = Boolean(data.namesOnly);
    this.outputFormat = data.outputFormat ?? "discord";
    this.streamLinkFormat = data.streamLinkFormat ?? "";
    this.socialLinks = data.socialLinks ? { ...data.socialLinks } : {};
    this.discordRoleMentions = Array.isArray(data.discordRoleMentions)
      ? data.discordRoleMentions.map((r) => ({ ...r }))
      : [];
    this._notify();
  }

  clear() {
    this.loadFromObject({});
  }

  // ── Change notification ───────────────────────────────────────────────

  notify() {
    this._notify();
  }

  _notify() {
    this._bus.publish("model_changed");
  }
}
