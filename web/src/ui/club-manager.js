/**
 * ClubManager — manages the Club tab.
 *
 * Club Discord link, VRChat group verification flow,
 * and sent booking management.
 *
 * Mirrors desktop Club tab (_build_club_tab).
 */

export class ClubManager {
  /**
   * @param {import('../models/event-bus.js').EventBus} bus
   * @param {import('../services/api-client.js').ApiClient} api
   * @param {import('./modal-manager.js').ModalManager} modal
   * @param {import('../services/storage.js').StorageManager} storage
   * @param {import('./tab-manager.js').TabManager} tabs
   */
  constructor(bus, api, modal, storage, tabs) {
    this._bus = bus;
    this._api = api;
    this._modal = modal;
    this._storage = storage;
    this._tabs = tabs;

    this._discordId = null;
    this._verifyCode = null; // persistent code derived from discord_id
    this._group = null; // linked VRChat group
  }

  init() {
    this._linkedInfo = document.getElementById("vrchat-linked-info");
    this._unlinkedState = document.getElementById("vrchat-unlinked-state");
    this._linkedState = document.getElementById("vrchat-linked-state");
    this._verifyStatus = document.getElementById("vrchat-verify-status");
    this._bookingsList = document.getElementById("club-bookings-list");
    this._clubLinkInput = document.getElementById("club-link-discord");

    // Club Discord link — load from storage first, then overwrite from server
    if (this._clubLinkInput) {
      this._clubLinkInput.value = this._storage.getSettings()?.club_discord ?? "";
      this._clubLinkInput.addEventListener("input", (e) => {
        const val = e.target.value.trim();
        // Persist locally
        const settings = this._storage.getSettings();
        settings.club_discord = val;
        this._storage.saveSettings(settings);
        // Notify other components
        this._bus.publish("club_updated", { discord: val });
        // Persist to server if signed in
        if (this._discordId) {
          this._api.updateClub(this._discordId, { discord_link: val }).catch(() => {});
        }
      });
    }

    // VRChat verify button + change group button (both open the same popup)
    document.getElementById("btn-vrchat-verify")?.addEventListener("click", () => this._openVerifyPopup());
    document.getElementById("btn-vrchat-change")?.addEventListener("click", () => this._openVerifyPopup());

    // Refresh bookings
    document.getElementById("btn-club-refresh-bookings")?.addEventListener("click", () => this._refreshBookings());

    // Restore session (if user is signed in, load linked group)
    const session = this._storage.getDjSession();
    if (session?.discord_id) {
      this._discordId = session.discord_id;
      this._verifyCode = session.verify_code ?? null;
      this._loadGroupInfo();
    }

    // Listen for auth changes (login pill + DJ tab sign-in)
    this._bus.subscribe("auth_changed", (data) => {
      if (data?.discord_id) {
        this._discordId = data.discord_id;
        this._verifyCode = data.verify_code ?? null;
        this._loadGroupInfo();
      } else {
        this._discordId = null;
        this._verifyCode = null;
        this._group = null;
        if (this._linkedInfo) this._linkedInfo.innerHTML = "";
        if (this._unlinkedState) this._unlinkedState.hidden = false;
        if (this._linkedState) this._linkedState.hidden = true;
        if (this._bookingsList) this._bookingsList.innerHTML = '<p class="muted-text">Sign in to view bookings.</p>';
      }
    });

    this._bus.subscribe("dj_signed_in", (data) => {
      if (data?.discord_id && !this._discordId) {
        this._discordId = data.discord_id;
        this._verifyCode = data.verify_code ?? null;
        this._loadGroupInfo();
      }
    });
  }

  // ── VRChat group verification ─────────────────────────────────────────

  _openVerifyPopup() {
    const code = this._verifyCode ?? "Sign in first";
    const container = this._modal.custom(`
      <h3>Verify VRChat Account</h3>
      <p class="muted-text">
        Step 1 — Add your verification code to your VRChat bio, then enter your
        VRChat username and click <strong>Verify Bio</strong>.
      </p>
      <div class="field-row" style="margin-top:12px">
        <label class="field-label" style="width:110px">Your Code</label>
        <input type="text" class="input input--sm" id="vrc-verify-code"
               style="flex:1;font-family:monospace;font-weight:600" readonly
               value="${code}" />
        <button class="btn btn--icon" id="vrc-copy-code" title="Copy code">
          <span class="material-symbols-rounded" style="font-size:16px">content_copy</span>
        </button>
      </div>
      <div class="field-row" style="margin-top:8px">
        <label class="field-label" style="width:110px">VRChat Username</label>
        <input type="text" class="input input--sm" id="vrc-verify-username" style="flex:1" placeholder="YourVRChatName" />
      </div>
      <p id="vrc-verify-error" class="error-text" style="margin-top:8px"></p>
      <div style="display:flex;gap:8px;margin-top:16px;justify-content:flex-end">
        <button class="btn btn--primary btn--sm" id="vrc-verify-submit">Verify Bio</button>
        <button class="btn btn--sm" id="vrc-verify-cancel">Cancel</button>
      </div>

      <div id="vrc-group-section" style="display:none;margin-top:20px;border-top:1px solid var(--color-border);padding-top:16px">
        <p class="muted-text" style="margin-bottom:10px">
          Step 2 — Select the VRChat group you want to link.
        </p>
        <div class="field-row">
          <label class="field-label" style="width:110px">Your Group</label>
          <select class="select select--sm" id="vrc-group-select" style="flex:1">
            <option value="">Loading groups...</option>
          </select>
        </div>
        <div style="display:flex;justify-content:flex-end;margin-top:12px">
          <button class="btn btn--primary btn--sm" id="vrc-link-group-btn">Link Group</button>
        </div>
      </div>
    `);

    const submitBtn = container.querySelector("#vrc-verify-submit");
    const cancelBtn = container.querySelector("#vrc-verify-cancel");
    const errorEl = container.querySelector("#vrc-verify-error");
    const groupSection = container.querySelector("#vrc-group-section");
    const groupSelect = container.querySelector("#vrc-group-select");
    const linkGroupBtn = container.querySelector("#vrc-link-group-btn");
    let verifiedVrcUserId = "";

    container.querySelector("#vrc-copy-code")?.addEventListener("click", () => {
      navigator.clipboard?.writeText(code);
    });

    cancelBtn?.addEventListener("click", () => this._modal.close());

    submitBtn?.addEventListener("click", async () => {
      const username = container.querySelector("#vrc-verify-username")?.value?.trim();
      if (!username) { if (errorEl) errorEl.textContent = "Enter your VRChat username."; return; }

      submitBtn.disabled = true;
      if (errorEl) errorEl.textContent = "Scanning bio...";

      try {
        const result = await this._api.verifyVrchatBio(username, code);
        verifiedVrcUserId = result.vrchat_user_id;
        if (errorEl) errorEl.textContent = `✓ Bio verified as ${result.vrchat_display_name}. Select your group below.`;

        // Fetch the user's groups and populate the dropdown
        if (groupSection) groupSection.style.display = "block";
        if (groupSelect) groupSelect.innerHTML = '<option value="">Loading groups...</option>';
        if (linkGroupBtn) linkGroupBtn.disabled = true;

        try {
          const groups = await this._api.getVrchatUserGroups(verifiedVrcUserId);
          if (!groups?.length) {
            groupSelect.innerHTML = '<option value="">No groups found</option>';
          } else {
            groupSelect.innerHTML =
              '<option value="">— Select a group —</option>' +
              groups.map(g =>
                `<option value="${this._esc(g.groupId)}">${this._esc(g.name)} (${this._esc(g.shortCode)})</option>`
              ).join("");
            linkGroupBtn.disabled = false;
          }
        } catch {
          groupSelect.innerHTML = '<option value="">Failed to load groups</option>';
        }
      } catch (err) {
        if (errorEl) errorEl.textContent = err.message || "Bio verification failed.";
        submitBtn.disabled = false;
      }
    });

    linkGroupBtn?.addEventListener("click", async () => {
      const groupId = groupSelect?.value?.trim();
      if (!groupId) { if (errorEl) errorEl.textContent = "Select a group."; return; }
      if (!verifiedVrcUserId) { if (errorEl) errorEl.textContent = "Complete bio verification first."; return; }

      linkGroupBtn.disabled = true;
      if (errorEl) errorEl.textContent = "Verifying group ownership...";

      try {
        const linked = await this._api.verifyVrchatGroup(groupId, this._discordId, verifiedVrcUserId);
        this._group = linked;
        // Save VRC group URL to settings for use in event links
        const vrcUrl = `https://vrc.group/${linked.short_code}`;
        const settings = this._storage.getSettings();
        settings.club_vrc_group_url = vrcUrl;
        this._storage.saveSettings(settings);
        this._bus.publish("club_updated", { vrc_group_url: vrcUrl });
        this._renderGroupInfo();
        this._modal.close();
        this._refreshBookings();
      } catch (err) {
        if (errorEl) errorEl.textContent = err.message || "Group verification failed.";
        linkGroupBtn.disabled = false;
      }
    });
  }

  async _loadGroupInfo() {
    if (!this._discordId) return;
    try {
      const club = await this._api.getClub(this._discordId);
      // Sync Discord link from server into input + localStorage
      if (club?.discord_link && this._clubLinkInput) {
        this._clubLinkInput.value = club.discord_link;
        const settings = this._storage.getSettings();
        settings.club_discord = club.discord_link;
        this._storage.saveSettings(settings);
      }
      // Populate VRChat group info if linked
      if (club?.vrchat_group_id) {
        this._group = {
          group_id:     club.vrchat_group_id,
          group_name:   club.vrchat_group_name,
          short_code:   club.vrchat_short_code,
          member_count: club.vrchat_member_count,
          icon_url:     club.vrchat_icon_url ?? "",
        };
        // Save VRC group URL to settings for use in event links
        const vrcUrl = `https://vrc.group/${club.vrchat_short_code}`;
        const settings = this._storage.getSettings();
        settings.club_vrc_group_url = vrcUrl;
        this._storage.saveSettings(settings);
        this._bus.publish("club_updated", { vrc_group_url: vrcUrl });
        this._renderGroupInfo();
        this._refreshBookings();
      }
    } catch {
      // No club record yet
    }
  }

  _renderGroupInfo() {
    if (!this._linkedInfo || !this._group) return;

    // Switch to linked state
    if (this._unlinkedState) this._unlinkedState.hidden = true;
    if (this._linkedState) this._linkedState.hidden = false;

    const iconHtml = this._group.icon_url
      ? `<img class="group-logo" src="${this._esc(this._group.icon_url)}" alt="" />`
      : `<div class="group-logo group-logo--placeholder"><span class="material-symbols-rounded">group</span></div>`;

    this._linkedInfo.innerHTML = `
      ${iconHtml}
      <div class="group-linked-card__info">
        <strong class="group-linked-card__name">${this._esc(this._group.group_name)}</strong>
        <span class="muted-text">${this._group.member_count ?? 0} members· ${this._esc(this._group.short_code ?? "")}</span>
      </div>`;
  }

  // ── Bookings ──────────────────────────────────────────────────────────

  async _refreshBookings() {
    if (!this._bookingsList) return;
    const groupName = this._group?.group_name;
    if (!groupName) {
      this._bookingsList.innerHTML = '<p class="muted-text">Link a VRChat group to view sent bookings.</p>';
      return;
    }

    this._bookingsList.innerHTML = '<p class="muted-text">Loading...</p>';
    try {
      const bookings = await this._api.listGroupBookings(groupName);
      this._renderBookings(Array.isArray(bookings) ? bookings : []);
    } catch {
      this._bookingsList.innerHTML = '<p class="muted-text">Could not load bookings.</p>';
    }
  }

  _renderBookings(bookings) {
    if (!this._bookingsList) return;
    this._bookingsList.innerHTML = "";

    if (!bookings.length) {
      this._bookingsList.innerHTML = '<p class="muted-text">No sent bookings.</p>';
      this._tabs?.setBadge("club", 0);
      return;
    }

    // Count responded bookings whose IDs the user hasn't seen yet
    const seenKey = "club_seen_booking_ids";
    const seenRaw = localStorage.getItem(seenKey);
    const seen = new Set(seenRaw ? JSON.parse(seenRaw) : []);

    // If the club tab is currently active, mark everything as seen immediately
    const clubTabActive = document.querySelector('.tab[data-tab="club"]')?.classList.contains("active");
    const responded = bookings.filter((b) => b.status === "accepted" || b.status === "declined");
    if (clubTabActive) {
      responded.forEach((b) => seen.add(b.id));
      localStorage.setItem(seenKey, JSON.stringify([...seen]));
    }

    const unseen = responded.filter((b) => !seen.has(b.id));
    this._tabs?.setBadge("club", unseen.length);

    // When club tab is clicked, snapshot current responded IDs as seen
    const clubTabBtn = document.querySelector('.tab[data-tab="club"]');
    if (clubTabBtn && !clubTabBtn._badgeClearBound) {
      clubTabBtn._badgeClearBound = true;
      clubTabBtn.addEventListener("click", () => {
        const all = bookings.filter((b) => b.status === "accepted" || b.status === "declined");
        const s = new Set(JSON.parse(localStorage.getItem(seenKey) || "[]"));
        all.forEach((b) => s.add(b.id));
        localStorage.setItem(seenKey, JSON.stringify([...s]));
      });
    }

    for (const b of bookings) {
      const statusClass = b.status === "accepted" ? "status--accepted" :
                          b.status === "declined" ? "status--declined" : "status--pending";
      const card = document.createElement("div");
      card.className = "booking-card";
      card.innerHTML = `
        <div class="booking-card__info">
          <strong>${this._esc(b.dj_name || "")}</strong>
          <span class="muted-text">${this._esc(b.event_title || "")} — ${this._esc(b.event_date || "")}</span>
        </div>
        <span class="booking-status ${statusClass}">${this._esc(b.status || "pending")}</span>`;
      this._bookingsList.appendChild(card);
    }
  }

  // ── Helpers ───────────────────────────────────────────────────────────

  _esc(str) {
    return String(str).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
  }
}
