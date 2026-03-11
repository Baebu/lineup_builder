/**
 * DiscordManager — manages Discord server/channel selection, role mentions,
 * embed image, posting to channels, and scheduled posting.
 */
import { showToast } from "./toast.js";

export class DiscordManager {
  /**
   * @param {import('../models/event-bus.js').EventBus} bus
   * @param {import('../models/lineup-model.js').LineupModel} model
   * @param {import('../services/api-client.js').ApiClient} api
   * @param {import('./modal-manager.js').ModalManager} modal
   */
  /**
   * @param {import('../services/image-storage.js').ImageStorageService} images
   */
  constructor(bus, model, api, modal, images) {
    this._bus = bus;
    this._model = model;
    this._api = api;
    this._modal = modal;
    this._images = images;

    this._guilds = [];
    this._channels = [];
    this._roles = [];
    this._selectedGuildId = "";
    this._selectedChannelId = "";
    this._roleFilter = "";
    this._embedImageUrl = "";

    // Cached drawer data — keyed by id for O(1) action lookup
    this._scheduledMap = new Map();
    this._sentMap = new Map();
    this._refreshTimer = null;
  }

  init() {
    this._guildSelect = document.getElementById("discord-guild-select");
    this._channelSelect = document.getElementById("discord-channel-select");
    this._rolesSection = document.getElementById("discord-roles-section");
    this._rolesList = document.getElementById("discord-roles-list");
    this._roleSearch = document.getElementById("discord-role-search");
    this._embedImageInput = document.getElementById("discord-embed-image");

    this._guildSelect?.addEventListener("change", () => this._onGuildChange());
    this._channelSelect?.addEventListener("change", () => this._onChannelChange());

    document.getElementById("btn-refresh-guilds")?.addEventListener("click", () => {
      this.fetchGuilds();
    });

    this._roleSearch?.addEventListener("input", () => {
      this._roleFilter = this._roleSearch.value.toLowerCase();
      this._renderRoles();
    });

    this._embedImageInput?.addEventListener("input", () => {
      this._embedImageUrl = this._embedImageInput.value.trim();
      this._updateEmbedImagePreview(this._embedImageUrl);
    });

    document.getElementById("btn-clear-embed-image")?.addEventListener("click", () => {
      this._embedImageUrl = "";
      if (this._embedImageInput) this._embedImageInput.value = "";
      this._updateEmbedImagePreview("");
    });

    this._initEmbedImageUploader();

    document.getElementById("btn-discord-post")?.addEventListener("click", () => {
      this._postEmbed();
    });

    document.getElementById("btn-discord-post-text")?.addEventListener("click", () => {
      this._postText();
    });

    document.getElementById("btn-discord-schedule")?.addEventListener("click", () => {
      this._schedulePost();
    });

    document.getElementById("btn-scheduled-drawer")?.addEventListener("click", () => {
      this._toggleDrawer("discord-scheduled-drawer", "discord-scheduled-list");
    });

    document.getElementById("btn-sent-drawer")?.addEventListener("click", () => {
      this._toggleDrawer("discord-sent-drawer", "discord-sent-list");
    });

    // Event delegation — one listener per drawer body covers all items
    document.getElementById("discord-scheduled-list")
      ?.addEventListener("click", (e) => this._onScheduledAction(e));
    document.getElementById("discord-sent-list")
      ?.addEventListener("click", (e) => this._onSentAction(e));

    this.fetchGuilds();
    this._fetchBotStatus();
    // Drawers are lazy-loaded on first open — no fetch on init
  }

  // ── Guild / Channel / Roles ─────────────────────────────────────────

  async fetchGuilds() {
    showToast("Loading servers...", "info");
    try {
      this._guilds = await this._api.getDiscordGuilds();
      this._populateGuilds();
    } catch {
      this._guilds = [];
      this._populateGuilds();
      showToast("Could not connect to bot server", "error");
    }
  }

  _populateGuilds() {
    if (!this._guildSelect) return;
    const current = this._selectedGuildId;
    this._guildSelect.innerHTML = '<option value="">Select server...</option>';
    for (const g of this._guilds) {
      const opt = document.createElement("option");
      opt.value = g.id;
      opt.textContent = g.name;
      this._guildSelect.appendChild(opt);
    }
    if (current && this._guilds.some((g) => g.id === current)) {
      this._guildSelect.value = current;
    }
  }

  async _onGuildChange() {
    this._selectedGuildId = this._guildSelect.value;
    this._selectedChannelId = "";
    this._channels = [];
    this._roles = [];

    if (!this._selectedGuildId) {
      this._rolesSection?.setAttribute("hidden", "");
      this._channelSelect.innerHTML = '<option value="">Select channel...</option>';
      this._clearRoleMentions();
      return;
    }

    showToast("Loading channels & roles...", "info");
    try {
      const [channels, roles] = await Promise.all([
        this._api.getGuildChannels(this._selectedGuildId),
        this._api.getGuildRoles(this._selectedGuildId),
      ]);
      this._channels = channels;
      this._roles = roles;
      this._populateChannels();
      this._rolesSection?.removeAttribute("hidden");
      this._renderRoles();
    } catch {
      this._channels = [];
      this._roles = [];
      this._populateChannels();
      showToast("Failed to fetch server data", "error");
    }
  }

  _populateChannels() {
    if (!this._channelSelect) return;
    this._channelSelect.innerHTML = '<option value="">Select channel...</option>';
    for (const ch of this._channels) {
      const opt = document.createElement("option");
      opt.value = ch.channel_id;
      opt.textContent = `#${ch.channel_name}`;
      this._channelSelect.appendChild(opt);
    }
  }

  _onChannelChange() {
    this._selectedChannelId = this._channelSelect.value;
  }

  // ── Roles ───────────────────────────────────────────────────────────

  _renderRoles() {
    if (!this._rolesList) return;
    this._rolesList.innerHTML = "";

    const selected = new Set(this._model.discordRoleMentions.map((r) => r.id));
    const filtered = this._roleFilter
      ? this._roles.filter((r) => r.name.toLowerCase().includes(this._roleFilter))
      : this._roles;

    if (!filtered.length) {
      const empty = document.createElement("span");
      empty.className = "muted-text";
      empty.textContent = this._roles.length ? "No matching roles." : "No roles available.";
      this._rolesList.appendChild(empty);
      return;
    }

    for (const role of filtered) {
      const label = document.createElement("label");
      label.className = "discord-role-item";

      const cb = document.createElement("input");
      cb.type = "checkbox";
      cb.checked = selected.has(role.id);
      cb.addEventListener("change", () => this._toggleRole(role, cb.checked));

      const dot = document.createElement("span");
      dot.className = "discord-role-dot";
      if (role.color && role.color !== "#000000") {
        dot.style.background = role.color;
      }

      const name = document.createElement("span");
      name.className = "discord-role-name";
      name.textContent = role.name;

      label.append(cb, dot, name);
      this._rolesList.appendChild(label);
    }
  }

  _toggleRole(role, checked) {
    const mentions = this._model.discordRoleMentions;
    if (checked) {
      if (!mentions.some((r) => r.id === role.id)) {
        mentions.push({ id: role.id, name: role.name });
      }
    } else {
      this._model.discordRoleMentions = mentions.filter((r) => r.id !== role.id);
    }
    this._model.notify();
  }

  _clearRoleMentions() {
    this._model.discordRoleMentions = [];
    this._model.notify();
  }

  // ── Bot Status ──────────────────────────────────────────────────────

  async _fetchBotStatus() {
    try {
      const status = await this._api.getBotStatus();
      if (status.connected) {
        showToast(`Connected as ${status.user}`, "success");
      } else {
        showToast("Bot not connected", "error");
      }
    } catch {
      // Silently ignore — fetchGuilds already shows connection errors
    }
  }

  // ── Build Embed Data ────────────────────────────────────────────────

  _buildEmbedData() {
    const snap = this._model.snapshot();
    return {
      title: snap.fullTitle,
      vol: snap.vol,
      timestamp: snap.timestamp,
      genres: snap.genres,
      slots: snap.slots.map((s) => ({
        name: s.name,
        genre: s.genre,
        duration: s.duration,
      })),
      names_only: snap.namesOnly,
      social_links: snap.socialLinks,
    };
  }

  // ── Post to Channel ─────────────────────────────────────────────────

  async _postEmbed() {
    if (!this._selectedChannelId) {
      showToast("Select a channel first", "error");
      return;
    }
    const data = this._buildEmbedData();
    if (!data.slots.length) {
      showToast("Add at least one slot to the lineup first", "error");
      return;
    }

    showToast("Posting embed...", "info");
    try {
      await this._api.postEmbed(
        this._selectedChannelId,
        data,
        this._embedImageUrl,
      );
      showToast("Embed posted!", "success");
      this._refreshDrawers();
    } catch (err) {
      showToast(`Post failed: ${err.message}`, "error");
    }
  }

  async _postText() {
    if (!this._selectedChannelId) {
      showToast("Select a channel first", "error");
      return;
    }

    const preview = document.getElementById("output-preview");
    const content = preview?.textContent ?? "";
    if (!content) {
      showToast("Output is empty", "error");
      return;
    }

    showToast("Posting message...", "info");
    try {
      await this._api.postMessage(this._selectedChannelId, content);
      showToast("Message posted!", "success");
    } catch (err) {
      showToast(`Post failed: ${err.message}`, "error");
    }
  }

  // ── Scheduled Posts ─────────────────────────────────────────────────

  async _schedulePost() {
    if (!this._selectedChannelId) {
      showToast("Select a channel first", "error");
      return;
    }

    const dtInput = document.getElementById("discord-schedule-datetime");
    const dtValue = dtInput?.value;
    if (!dtValue) {
      showToast("Select a date and time first", "error");
      return;
    }

    const postAt = new Date(dtValue);
    if (isNaN(postAt.getTime()) || postAt <= new Date()) {
      showToast("Schedule time must be in the future", "error");
      return;
    }

    showToast("Scheduling post...", "info");
    try {
      await this._api.createScheduledPost(
        postAt.toISOString(),
        this._selectedChannelId,
        this._buildEmbedData(),
        this._embedImageUrl,
      );
      showToast("Post scheduled!", "success");
      if (dtInput) dtInput.value = "";
      this._refreshDrawers();
    } catch (err) {
      showToast(`Schedule failed: ${err.message}`, "error");
    }
  }

  // ── History Drawers ─────────────────────────────────────────────────

  _toggleDrawer(drawerId, bodyId) {
    const drawer = document.getElementById(drawerId);
    const body = document.getElementById(bodyId);
    if (!drawer || !body) return;
    const opening = !drawer.classList.contains("open");
    drawer.classList.toggle("open", opening);
    body.hidden = !opening;
    const chevron = drawer.querySelector(".discord-drawer__chevron");
    if (chevron) chevron.textContent = opening ? "expand_less" : "expand_more";
    // Fetch on open; skip if already populated
    if (opening) {
      if (bodyId === "discord-scheduled-list") this._refreshScheduled();
      else if (bodyId === "discord-sent-list") this._refreshSent();
    }
  }

  // Debounced combined refresh (used after mutating actions)
  _refreshDrawers() {
    if (this._refreshTimer) return; // already queued
    this._refreshTimer = setTimeout(async () => {
      this._refreshTimer = null;
      const scheduledOpen = !document.getElementById("discord-scheduled-list")?.hidden;
      const sentOpen = !document.getElementById("discord-sent-list")?.hidden;
      await Promise.allSettled([
        scheduledOpen ? this._refreshScheduled() : this._refreshScheduledCount(),
        sentOpen      ? this._refreshSent()       : this._refreshSentCount(),
      ]);
    }, 200);
  }

  async _refreshScheduled() {
    try {
      const posts = await this._api.listScheduledPosts();
      this._scheduledMap = new Map(posts.map((p) => [p.id, p]));
      this._renderScheduledList(posts);
    } catch { /* bot not connected */ }
  }

  async _refreshSent() {
    try {
      const posts = await this._api.getSentPosts();
      this._sentMap = new Map(posts.map((p) => [p.id, p]));
      this._renderSentList(posts);
    } catch { /* bot not connected */ }
  }

  async _refreshScheduledCount() {
    try {
      const posts = await this._api.listScheduledPosts();
      this._scheduledMap = new Map(posts.map((p) => [p.id, p]));
      const el = document.getElementById("scheduled-count");
      if (el) { el.textContent = posts.length; el.hidden = posts.length === 0; }
    } catch { /* silent */ }
  }

  async _refreshSentCount() {
    try {
      const posts = await this._api.getSentPosts();
      this._sentMap = new Map(posts.map((p) => [p.id, p]));
      const el = document.getElementById("sent-count");
      if (el) { el.textContent = posts.length; el.hidden = posts.length === 0; }
    } catch { /* silent */ }
  }

  _renderScheduledList(posts) {
    const container = document.getElementById("discord-scheduled-list");
    const countEl = document.getElementById("scheduled-count");
    if (!container) return;

    if (countEl) {
      countEl.textContent = posts.length;
      countEl.hidden = posts.length === 0;
    }

    if (!posts.length) {
      container.innerHTML = '<span class="muted-text" style="padding:8px;display:block;font-size:12px">No scheduled posts</span>';
      return;
    }

    container.innerHTML = posts.map((p) => this._buildScheduledItem(p)).join("");
  }

  _renderSentList(posts) {
    const container = document.getElementById("discord-sent-list");
    const countEl = document.getElementById("sent-count");
    if (!container) return;

    if (countEl) {
      countEl.textContent = posts.length;
      countEl.hidden = posts.length === 0;
    }

    if (!posts.length) {
      container.innerHTML = '<span class="muted-text" style="padding:8px;display:block;font-size:12px">No sent posts</span>';
      return;
    }

    container.innerHTML = posts.map((p) => this._buildSentItem(p)).join("");
  }

  // ── Event delegation handlers (one listener per drawer) ─────────────

  async _onScheduledAction(e) {
    const btn = e.target.closest("[data-action]");
    if (!btn) return;
    const item = btn.closest(".discord-history-item");
    const postId = item?.dataset.postId;
    const post = postId ? this._scheduledMap.get(postId) : null;
    const action = btn.dataset.action;

    if (action === "load" && post) {
      this._loadPostIntoEditor(post);
    } else if (action === "reschedule-toggle") {
      const row = item?.querySelector(".discord-history-item__reschedule");
      if (row) {
        row.hidden = !row.hidden;
        if (!row.hidden && post) {
          const local = new Date(post.post_at_utc);
          const offset = local.getTimezoneOffset() * 60000;
          row.querySelector("[data-reschedule-input]").value =
            new Date(local - offset).toISOString().slice(0, 16);
        }
      }
    } else if (action === "reschedule-save" && post) {
      const input = item?.querySelector("[data-reschedule-input]");
      const newTime = input?.value;
      if (!newTime) return;
      const dt = new Date(newTime);
      if (isNaN(dt.getTime()) || dt <= new Date()) {
        showToast("Time must be in the future", "error");
        return;
      }
      btn.disabled = true;
      try {
        await this._api.updateScheduledPost(post.id, { post_at_utc: dt.toISOString() });
        showToast("Rescheduled!", "success");
        await this._refreshScheduled();
      } catch (err) {
        showToast(`Reschedule failed: ${err.message}`, "error");
        btn.disabled = false;
      }
    } else if (action === "cancel" && post) {
      if (!confirm(`Cancel scheduled post "${post.title || "Untitled"}"?`)) return;
      btn.disabled = true;
      try {
        await this._api.cancelScheduledPost(post.id);
        await this._refreshScheduled();
        showToast("Scheduled post cancelled", "success");
      } catch {
        showToast("Failed to cancel post", "error");
        btn.disabled = false;
      }
    }
  }

  async _onSentAction(e) {
    const btn = e.target.closest("[data-action]");
    if (!btn) return;
    const item = btn.closest(".discord-history-item");
    const postId = item?.dataset.postId;
    const post = postId ? this._sentMap.get(postId) : null;
    const action = btn.dataset.action;

    if (action === "load" && post) {
      this._loadPostIntoEditor(post);
    } else if (action === "resend" && post) {
      btn.disabled = true;
      showToast("Resending...", "info");
      try {
        await this._api.resendPost(post.id);
        showToast("Resent!", "success");
        await this._refreshSent();
      } catch (err) {
        showToast(`Resend failed: ${err.message}`, "error");
        btn.disabled = false;
      }
    } else if (action === "delete" && post) {
      btn.disabled = true;
      try {
        await this._api.deleteSentPost(post.id);
        await this._refreshSent();
      } catch {
        showToast("Failed to remove from history", "error");
        btn.disabled = false;
      }
    }
  }

  _buildScheduledItem(post) {
    const time = new Date(post.post_at_utc).toLocaleString();
    const title = this._esc(post.title || "Untitled");
    return `
      <div class="discord-history-item" data-post-id="${this._esc(post.id)}">
        <div class="discord-history-item__header">
          <span class="discord-history-item__title">${title}</span>
          <div class="discord-history-item__actions">
            <button class="btn btn--icon" title="Load into editor" data-action="load">
              <span class="material-symbols-rounded" style="font-size:16px">edit</span>
            </button>
            <button class="btn btn--icon" title="Reschedule" data-action="reschedule-toggle">
              <span class="material-symbols-rounded" style="font-size:16px">schedule</span>
            </button>
            <button class="btn btn--icon" title="Cancel post" data-action="cancel" style="color:var(--error,#f44)">
              <span class="material-symbols-rounded" style="font-size:16px">close</span>
            </button>
          </div>
        </div>
        <div class="discord-history-item__meta">
          <span class="material-symbols-rounded" style="font-size:12px;vertical-align:-2px">schedule</span>
          ${this._esc(time)}
        </div>
        ${this._buildPreviewHtml(post)}
        <div class="discord-history-item__reschedule" hidden>
          <div class="field-row" style="margin-top:6px;gap:4px">
            <input type="datetime-local" class="input input--sm" data-reschedule-input style="flex:1" />
            <button class="btn btn--primary btn--sm" data-action="reschedule-save">Update</button>
          </div>
        </div>
      </div>`;
  }

  _buildSentItem(post) {
    const time = new Date(post.sent_at).toLocaleString();
    const title = this._esc(post.title || "Untitled");
    const channel = post.channel_name ? `#${post.channel_name}` : "";
    const guild = post.guild_name || "";
    const location = [guild, channel].filter(Boolean).join(" / ");
    return `
      <div class="discord-history-item" data-post-id="${this._esc(post.id)}">
        <div class="discord-history-item__header">
          <span class="discord-history-item__title">${title}</span>
          <div class="discord-history-item__actions">
            <button class="btn btn--icon" title="Load into editor" data-action="load">
              <span class="material-symbols-rounded" style="font-size:16px">edit</span>
            </button>
            <button class="btn btn--icon" title="Resend to same channel" data-action="resend">
              <span class="material-symbols-rounded" style="font-size:16px">send</span>
            </button>
            <button class="btn btn--icon" title="Remove from history" data-action="delete" style="color:var(--error,#f44)">
              <span class="material-symbols-rounded" style="font-size:16px">close</span>
            </button>
          </div>
        </div>
        <div class="discord-history-item__meta">
          <span>${this._esc(time)}</span>
          ${location ? `<span class="discord-history-item__channel">${this._esc(location)}</span>` : ""}
        </div>
        ${this._buildPreviewHtml(post)}
      </div>`;
  }

  _buildPreviewHtml(post) {
    const d = post.embed_data || {};
    const title = d.title || post.title || "";
    const vol = d.vol || "";
    const fullTitle = vol ? `${title} VOL.${vol}` : title;
    const rawTs = d.timestamp || "";
    const ts = rawTs
      ? new Date(rawTs.replace(" ", "T")).toLocaleString(undefined, {
          month: "short", day: "numeric", hour: "2-digit", minute: "2-digit",
        })
      : "";
    const genres = (d.genres || []).join(", ");
    const slots = d.slots || [];
    const names = slots.slice(0, 5).map((s) => s.name || "TBA").filter(Boolean).join(", ");
    const more = slots.length > 5 ? ` +${slots.length - 5}` : "";

    const rows = [];
    if (fullTitle) rows.push(`<div class="discord-embed-preview__title">${this._esc(fullTitle)}</div>`);
    if (ts) rows.push(`<div>${this._esc(ts)}</div>`);
    if (genres) rows.push(`<div>${this._esc(genres)}</div>`);
    if (names) rows.push(`<div>${this._esc(names + more)}</div>`);

    return `<div class="discord-embed-preview">${rows.join("")}</div>`;
  }

  _loadPostIntoEditor(post) {
    const d = post.embed_data || {};
    const current = this._model.toObject();

    this._model.loadFromObject({
      ...current,
      title:       d.title       ?? current.title,
      vol:         d.vol         ?? current.vol,
      timestamp:   d.timestamp   ?? current.timestamp,
      genres:      d.genres?.length   ? [...d.genres]   : current.genres,
      namesOnly:   d.names_only  != null ? d.names_only : current.namesOnly,
      socialLinks: Object.keys(d.social_links || {}).length
                     ? { ...d.social_links }
                     : current.socialLinks,
      slots:       d.slots?.length
                     ? d.slots.map((s) => ({ name: s.name ?? "", genre: s.genre ?? "", duration: s.duration ?? 60 }))
                     : current.slots,
    });

    const imgUrl = post.image_url || d.image_url || "";
    if (this._embedImageInput) {
      this._embedImageInput.value = imgUrl;
      this._embedImageUrl = imgUrl;
      this._updateEmbedImagePreview(imgUrl);
    }

    this._bus.publish("post_loaded");
    showToast("Loaded into editor", "success");
  }

  // ── Embed image uploader ───────────────────────────────────────────

  _initEmbedImageUploader() {
    const dropZone = document.getElementById("embed-image-drop-zone");
    const fileInput = document.getElementById("embed-image-file");
    const browseBtn = document.getElementById("btn-embed-image-browse");
    if (!dropZone || !fileInput) return;

    dropZone.addEventListener("click", (e) => {
      if (e.target !== browseBtn && !e.target.closest("#btn-clear-embed-image")) fileInput.click();
    });
    browseBtn?.addEventListener("click", (e) => {
      e.stopPropagation();
      fileInput.click();
    });

    fileInput.addEventListener("change", () => {
      if (fileInput.files?.[0]) this._loadEmbedImageFile(fileInput.files[0]);
    });

    dropZone.addEventListener("dragover", (e) => {
      e.preventDefault();
      dropZone.classList.add("drag-over");
    });
    dropZone.addEventListener("dragleave", () => dropZone.classList.remove("drag-over"));
    dropZone.addEventListener("drop", (e) => {
      e.preventDefault();
      dropZone.classList.remove("drag-over");
      const file = e.dataTransfer?.files?.[0];
      if (file && file.type.startsWith("image/")) this._loadEmbedImageFile(file);
    });
  }

  async _loadEmbedImageFile(file) {
    const localUrl = URL.createObjectURL(file);
    this._updateEmbedImagePreview(localUrl);

    const url = await this._images.upload(file);
    URL.revokeObjectURL(localUrl);

    this._embedImageUrl = url;
    this._updateEmbedImagePreview(url);
    if (this._embedImageInput) this._embedImageInput.value = "";
  }

  _updateEmbedImagePreview(src) {
    const preview = document.getElementById("embed-image-preview");
    const placeholder = document.getElementById("embed-image-placeholder");
    const clearBtn = document.getElementById("btn-clear-embed-image");
    if (!preview || !placeholder) return;
    if (src) {
      preview.src = src;
      preview.style.display = "block";
      placeholder.style.display = "none";
      if (clearBtn) clearBtn.style.display = "flex";
    } else {
      preview.src = "";
      preview.style.display = "none";
      placeholder.style.display = "flex";
      if (clearBtn) clearBtn.style.display = "none";
    }
  }

  // ── Helpers ─────────────────────────────────────────────────────────

  _esc(str) {
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  /** Get the currently selected channel ID (for posting). */
  get selectedChannelId() {
    return this._selectedChannelId;
  }

  /** Get the currently selected guild ID. */
  get selectedGuildId() {
    return this._selectedGuildId;
  }
}
