/**
 * OutputGenerator — pure JS port of desktop/src/backend/output/output_generator.py
 *
 * Stateless — every method is a static function of an EventSnapshot.
 */

const LINK_ORDER = ["TIMELINE", "VRCPOP", "X", "IG", "DISCORD", "VRC GROUP"];

export class OutputGenerator {
  /**
   * Return formatted output string for snap.outputFormat.
   * @param {import('../models/lineup-model.js').EventSnapshot} snap
   * @returns {string}
   */
  static generate(snap) {
    if (snap.outputFormat === "local") return OutputGenerator._generatePlain(snap);
    return OutputGenerator._generateDiscord(snap);
  }

  /**
   * Return array of "HH:MM" strings, one per slot, for UI time labels.
   * @param {import('../models/lineup-model.js').EventSnapshot} snap
   * @returns {string[]}
   */
  static computeSlotTimes(snap) {
    const start = snap.startDatetime;
    const times = [];
    let ptr = new Date(start.getTime());
    for (const slot of snap.slots) {
      times.push(OutputGenerator._formatHHMM(ptr));
      ptr = new Date(ptr.getTime() + slot.duration * 60 * 1000);
    }
    return times;
  }

  /**
   * Convert a VRCDN link to quest or pc format. Non-VRCDN links pass through.
   * @param {string} link
   * @param {"quest"|"pc"} fmt
   * @returns {string}
   */
  static vrcdnConvert(link, fmt) {
    if (!link) return link;
    const m = link.match(
      /^(?:https:\/\/stream\.vrcdn\.live\/live\/|rtspt:\/\/stream\.vrcdn\.live\/live\/)(.+?)(?:\.live\.ts)?$/
    );
    if (!m) return link;
    const key = m[1];
    if (fmt === "quest") return `https://stream.vrcdn.live/live/${key}.live.ts`;
    return `rtspt://stream.vrcdn.live/live/${key}`;
  }

  // ── Private builders ──────────────────────────────────────────────────

  static _generateDiscord(snap) {
    const djLookup = new Map(snap.savedDjs.map((d) => [d.name, d]));
    const lines = [];

    if (snap.title) lines.push(`# ${snap.fullTitle}`);
    if (snap.groupName) lines.push(`## ${snap.groupName}`);

    const start = snap.startDatetime;
    const unix = Math.floor(start.getTime() / 1000);
    lines.push(`# <t:${unix}:F> (<t:${unix}:R>)`);

    if (snap.genres.length) lines.push(`## ${snap.genres.join(" // ")}`);
    lines.push("### LINEUP");

    let ptr = new Date(start.getTime());
    let idx = 0;
    for (const slot of snap.slots) {
      idx++;
      const name = slot.name || String(idx);
      if (snap.namesOnly) {
        lines.push(name);
      } else {
        const genreStr = slot.genre ? ` (${slot.genre})` : "";
        const ts = Math.floor(ptr.getTime() / 1000);
        lines.push(`<t:${ts}:t> | **${name}**${genreStr}`);
      }
      if (snap.streamLinkFormat) {
        const dj = djLookup.get(slot.name?.trim());
        if (dj?.stream) {
          const link = dj.exactLink
            ? dj.stream
            : OutputGenerator.vrcdnConvert(dj.stream, snap.streamLinkFormat);
          lines.push("```\n" + link + "\n```");
        }
      }
      ptr = new Date(ptr.getTime() + slot.duration * 60 * 1000);
    }

    if (snap.socialLinks) {
      const parts = LINK_ORDER
        .filter((label) => snap.socialLinks[label]?.trim())
        .map((label) => `[${label}](${snap.socialLinks[label]})`);
      if (parts.length) {
        lines.push("");
        lines.push(parts.join(" | "));
      }
    }

    // Role mentions at the bottom of discord output
    if (snap.discordRoleMentions?.length) {
      lines.push("");
      lines.push(snap.discordRoleMentions.map((r) => `<@&${r.id}>`).join(" "));
    }

    return lines.join("\n");
  }

  static _generatePlain(snap) {
    const djLookup = new Map(snap.savedDjs.map((d) => [d.name, d]));
    const lines = [];

    if (snap.title) lines.push(snap.fullTitle);
    if (snap.groupName) lines.push(snap.groupName);

    const start = snap.startDatetime;
    const tz = OutputGenerator._localTzAbbr();
    lines.push(`${OutputGenerator._formatDate(start)} @ ${OutputGenerator._formatHHMM(start)} (${tz})`);

    if (snap.genres.length) lines.push(snap.genres.join(" // "));
    lines.push("LINEUP");

    let ptr = new Date(start.getTime());
    let idx = 0;
    for (const slot of snap.slots) {
      idx++;
      const name = slot.name || String(idx);
      if (snap.namesOnly) {
        lines.push(name);
      } else {
        const genreStr = slot.genre ? ` (${slot.genre})` : "";
        lines.push(`${OutputGenerator._formatHHMM(ptr)} | ${name}${genreStr}`);
      }
      if (snap.streamLinkFormat) {
        const dj = djLookup.get(slot.name?.trim());
        if (dj?.stream) {
          const link = dj.exactLink
            ? dj.stream
            : OutputGenerator.vrcdnConvert(dj.stream, snap.streamLinkFormat);
          lines.push(link);
        }
      }
      ptr = new Date(ptr.getTime() + slot.duration * 60 * 1000);
    }

    // Social links (plain-text format: "LABEL: url | LABEL: url")
    if (snap.socialLinks) {
      const parts = LINK_ORDER
        .filter((label) => snap.socialLinks[label]?.trim())
        .map((label) => `${label}: ${snap.socialLinks[label]}`);
      if (parts.length) {
        lines.push("");
        lines.push(parts.join(" | "));
      }
    }

    return lines.join("\n");
  }

  static _generateStreamLinks(snap, fmt) {
    const djLookup = new Map(snap.savedDjs.map((d) => [d.name, d]));
    const links = [];

    for (const slot of snap.slots) {
      const name = slot.name?.trim();
      if (!name) continue;
      const dj = djLookup.get(name);
      if (dj?.stream) {
        const link = dj.exactLink
          ? dj.stream
          : OutputGenerator.vrcdnConvert(dj.stream, fmt);
        links.push(link);
      }
    }

    if (!links.length) return "";
    return links.map((l) => `\`\`\`\n${l}\n\`\`\``).join("\n");
  }

  // ── Utilities ─────────────────────────────────────────────────────────

  static _formatHHMM(date) {
    const h = String(date.getHours()).padStart(2, "0");
    const m = String(date.getMinutes()).padStart(2, "0");
    return `${h}:${m}`;
  }

  static _formatDate(date) {
    const y = date.getFullYear();
    const m = String(date.getMonth() + 1).padStart(2, "0");
    const d = String(date.getDate()).padStart(2, "0");
    return `${y}-${m}-${d}`;
  }

  static _localTzAbbr() {
    try {
      const tz = Intl.DateTimeFormat().resolvedOptions().timeZone;
      // Get abbreviated name from locale string
      const parts = new Intl.DateTimeFormat("en-US", {
        timeZoneName: "short",
      }).formatToParts(new Date());
      const tzPart = parts.find((p) => p.type === "timeZoneName");
      return tzPart ? tzPart.value : tz;
    } catch {
      return "UTC";
    }
  }
}
