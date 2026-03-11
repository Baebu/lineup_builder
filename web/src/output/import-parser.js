/**
 * ImportParser — JS port of desktop/src/frontend/mixins/import_parser.py
 *
 * Parses Discord-markdown or plain-text output back into event data.
 * Pure functions — no DOM dependencies (except openImportDialog).
 */

const SOCIAL_LABELS = new Set(["TIMELINE", "VRCPOP", "X", "IG", "DISCORD", "VRC GROUP"]);

// ── Public entry point ──────────────────────────────────────────────────

/**
 * Open the Import Event modal. Calls onImport(parsedData) on success.
 * @param {import('../ui/modal-manager.js').ModalManager} modal
 * @param {(parsed: object) => void} onImport
 */
export function openImportDialog(modal, onImport) {
  const container = modal.custom(`
    <div class="modal__body">
      <h3 class="modal__title">Import Event</h3>
      <p class="modal__message" style="margin-bottom:0.5rem">
        Paste a Discord or plain-text formatted event below.
        Supports: titles, timestamps, genres, lineup slots.
      </p>
      <textarea class="input" id="import-paste"
        style="width:100%;min-height:120px;resize:vertical;font-family:monospace;font-size:13px"
        placeholder="Paste event text here..."></textarea>
      <p id="import-status" style="font-size:13px;color:var(--color-text-secondary);min-height:18px"></p>
      <div class="modal__actions">
        <button class="btn btn--secondary" id="import-preview">Preview</button>
        <button class="btn btn--secondary" id="import-cancel">Cancel</button>
        <button class="btn btn--primary" id="import-confirm">Import</button>
      </div>
    </div>`);

  const pasteEl = container.querySelector("#import-paste");
  const statusEl = container.querySelector("#import-status");

  const setStatus = (msg) => { if (statusEl) statusEl.textContent = msg; };

  container.querySelector("#import-preview")?.addEventListener("click", () => {
    const raw = pasteEl?.value?.trim() ?? "";
    if (!raw) { setStatus("Paste something first."); return; }
    const parsed = parseEventText(raw);
    if (!parsed) { setStatus("Could not recognise any event data."); return; }
    const n = parsed.slots?.length ?? 0;
    const title = parsed.title || "Untitled";
    const genres = parsed.genres?.join(", ") || "—";
    setStatus(`"${title}" — ${n} slot(s) — Genres: ${genres}`);
  });

  container.querySelector("#import-confirm")?.addEventListener("click", () => {
    const raw = pasteEl?.value?.trim() ?? "";
    if (!raw) { setStatus("Paste something first."); return; }
    const parsed = parseEventText(raw);
    if (!parsed) { setStatus("Could not recognise any event data."); return; }
    modal.close();
    onImport(parsed);
  });

  container.querySelector("#import-cancel")?.addEventListener("click", () => modal.close());

  requestAnimationFrame(() => pasteEl?.focus());
}

// ── Parser ──────────────────────────────────────────────────────────────

/**
 * Auto-detect format and parse into event data object.
 * @returns {{ title, vol, timestamp, genres, slots, namesOnly, socialLinks } | null}
 */
export function parseEventText(text) {
  const lines = text.trim().split("\n").map((l) => l.trim()).filter(Boolean);
  if (!lines.length) return null;
  const isDiscord = lines.some((l) => /<t:\d+:/.test(l));
  return isDiscord ? parseDiscord(lines) : parsePlain(lines);
}

// ── Discord format parser ───────────────────────────────────────────────

function parseDiscord(lines) {
  const parsed = { title: "", vol: "", timestamp: "", genres: [], slots: [], namesOnly: false, socialLinks: {} };
  const slotTimes = [];
  let inLineup = false;

  for (const line of lines) {
    // Social links: "[LABEL](url) | [LABEL](url)"
    const social = extractSocialLinks(line);
    if (Object.keys(social).length) {
      Object.assign(parsed.socialLinks, social);
      continue;
    }

    // Event timestamp: "# <t:UNIX:F> (<t:UNIX:R>)"
    const tsMatch = line.match(/<t:(\d+):F>/);
    if (tsMatch && !parsed.timestamp) {
      const dt = new Date(parseInt(tsMatch[1], 10) * 1000);
      parsed.timestamp = formatTimestamp(dt);
      continue;
    }

    // Slot with timestamp: "<t:UNIX:t> | **Name** (Genre)"
    const slotMatch = line.match(/^<t:(\d+):t>\s*\|\s*(.+)$/);
    if (slotMatch) {
      const unix = parseInt(slotMatch[1], 10);
      const rest = slotMatch[2].replace(/\*\*(.+?)\*\*/g, "$1").trim();
      const [name, genre] = extractNameGenre(rest);
      slotTimes.push(unix);
      parsed.slots.push({ name, genre, duration: 60 });
      continue;
    }

    // Section header: "### LINEUP"
    if (/^#{0,3}\s*LINEUP\s*$/i.test(line)) {
      inLineup = true;
      continue;
    }

    // Genre line: "## Genre1 // Genre2"
    if (line.includes("//") && !inLineup) {
      const genreText = line.replace(/^#+\s*/, "").trim();
      parsed.genres = genreText.split("//").map((g) => g.trim()).filter(Boolean);
      continue;
    }

    // Title: "# Night Beats VOL.3" (no timestamp on this line)
    const titleMatch = line.match(/^#+\s+(.+)$/);
    if (titleMatch && !parsed.title && !/<t:/.test(line)) {
      splitTitleVol(titleMatch[1].trim(), parsed);
      continue;
    }

    // Names-only slot: plain text inside LINEUP section
    if (inLineup && !/^#+/.test(line)) {
      parsed.namesOnly = true;
      parsed.slots.push({ name: line, genre: "", duration: 60 });
    }
  }

  computeSlotDurations(parsed.slots, slotTimes);
  return (parsed.title || parsed.slots.length) ? parsed : null;
}

// ── Plain-text parser ───────────────────────────────────────────────────

function parsePlain(lines) {
  const parsed = { title: "", vol: "", timestamp: "", genres: [], slots: [], namesOnly: false, socialLinks: {} };
  const slotTimes = [];
  let inLineup = false;

  for (const line of lines) {
    // Timestamp: "YYYY-MM-DD @ HH:MM (TZ)"
    const tsMatch = line.match(/^(\d{4}-\d{2}-\d{2})\s*@\s*(\d{1,2}:\d{2})/);
    if (tsMatch && !parsed.timestamp) {
      const hm = tsMatch[2].padStart(5, "0");
      parsed.timestamp = `${tsMatch[1]} ${hm}`;
      continue;
    }

    // Section header: "LINEUP"
    if (/^LINEUP\s*$/i.test(line)) {
      inLineup = true;
      continue;
    }

    if (inLineup) {
      // Timed slot: "HH:MM | DJ Name (Genre)"
      const slotMatch = line.match(/^(\d{1,2}:\d{2})\s*\|\s*(.+)$/);
      if (slotMatch) {
        const [name, genre] = extractNameGenre(slotMatch[2].trim());
        const unix = timeStrToUnix(slotMatch[1], parsed.timestamp);
        if (unix !== null) slotTimes.push(unix);
        parsed.slots.push({ name, genre, duration: 60 });
        continue;
      }
      // Names-only slot
      parsed.namesOnly = true;
      parsed.slots.push({ name: line, genre: "", duration: 60 });
      continue;
    }

    // Genre line: "Genre1 // Genre2"
    if (line.includes("//")) {
      parsed.genres = line.split("//").map((g) => g.trim()).filter(Boolean);
      continue;
    }

    // Title: first unrecognised line before LINEUP
    if (!parsed.title) {
      splitTitleVol(line, parsed);
    }
  }

  computeSlotDurations(parsed.slots, slotTimes);
  return (parsed.title || parsed.slots.length) ? parsed : null;
}

// ── Helpers ──────────────────────────────────────────────────────────────

function extractSocialLinks(line) {
  const result = {};
  const re = /\[([^\]]+)\]\((https?:\/\/[^)]+)\)/g;
  let m;
  while ((m = re.exec(line)) !== null) {
    const label = m[1].toUpperCase();
    if (SOCIAL_LABELS.has(label)) result[label] = m[2];
  }
  return result;
}

function splitTitleVol(candidate, parsed) {
  const m = candidate.match(/\s+VOL\.(\d+)\s*$/i);
  if (m) {
    parsed.vol = m[1];
    parsed.title = candidate.slice(0, m.index).trim();
  } else {
    parsed.title = candidate;
  }
}

function extractNameGenre(rest) {
  let name = rest.trim();
  let genre = "";

  // "(Genre)" or "[Genre]" at end
  const bracketMatch = name.match(/\s*[\(\[]([^\)\]]+)[\)\]]\s*$/);
  if (bracketMatch) {
    genre = bracketMatch[1].trim();
    name = name.slice(0, bracketMatch.index).trim();
    return [name, genre];
  }

  // " - Genre" or " – Genre" trailing suffix
  const dashMatch = name.match(/\s+[-–]\s+(.+)$/);
  if (dashMatch) {
    const possible = name.slice(0, dashMatch.index).trim();
    if (possible) {
      genre = dashMatch[1].trim();
      name = possible;
    }
  }

  return [name, genre];
}

function timeStrToUnix(timeStr, timestampCtx) {
  try {
    const [h, m] = timeStr.split(":").map(Number);
    let dateStr = "";
    if (timestampCtx) {
      dateStr = timestampCtx.split(" ")[0];
    } else {
      const now = new Date();
      dateStr = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}-${String(now.getDate()).padStart(2, "0")}`;
    }
    const dt = new Date(`${dateStr}T${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}:00`);
    return isNaN(dt.getTime()) ? null : Math.floor(dt.getTime() / 1000);
  } catch {
    return null;
  }
}

function computeSlotDurations(slots, slotTimes) {
  if (!slotTimes.length || slotTimes.length !== slots.length) return;

  // Handle midnight wrap-around
  for (let i = 1; i < slotTimes.length; i++) {
    if (slotTimes[i] <= slotTimes[i - 1]) slotTimes[i] += 86400;
  }

  for (let i = 0; i < slotTimes.length; i++) {
    if (i + 1 < slotTimes.length) {
      const diff = Math.floor((slotTimes[i + 1] - slotTimes[i]) / 60);
      if (diff > 0 && diff <= 480) slots[i].duration = diff;
    }
  }
}

function formatTimestamp(dt) {
  const y = dt.getFullYear();
  const mo = String(dt.getMonth() + 1).padStart(2, "0");
  const d = String(dt.getDate()).padStart(2, "0");
  const h = String(dt.getHours()).padStart(2, "0");
  const mi = String(dt.getMinutes()).padStart(2, "0");
  return `${y}-${mo}-${d} ${h}:${mi}`;
}
