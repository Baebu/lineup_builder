/**
 * DJManager — manages the DJ Profile tab.
 *
 * Sign-in via Discord OAuth, profile editing (links, logo, genres,
 * availability), and booking management (accept/decline).
 *
 * Mirrors desktop DJ Profile tab (_build_dj_profile_tab).
 */

const DJ_LINK_FIELDS = [
  { key: "Twitch", hint: "https://twitch.tv/" },
  { key: "SoundCloud", hint: "https://soundcloud.com/" },
  { key: "X", hint: "https://x.com/" },
  { key: "Instagram", hint: "https://instagram.com/" },
  { key: "YouTube", hint: "https://youtube.com/@" },
  { key: "Website", hint: "https://..." },
];

export class DJManager {
  /**
   * @param {import('../models/event-bus.js').EventBus} bus
   * @param {import('../services/api-client.js').ApiClient} api
   * @param {import('./modal-manager.js').ModalManager} modal
   * @param {import('../services/storage.js').StorageManager} storage
   * @param {import('../services/image-storage.js').ImageStorageService} images
   * @param {import('./tab-manager.js').TabManager} tabs
   */
  constructor(bus, api, modal, storage, images, tabs) {
    this._bus = bus;
    this._api = api;
    this._modal = modal;
    this._storage = storage;
    this._images = images;
    this._tabs = tabs;

    this._profile = null; // { name, discord_id, links, logo, genres, availability }
    this._syncTimer = null;
  }

  init() {
    this._signinView = document.getElementById("dj-signin-view");
    this._profileView = document.getElementById("dj-profile-view");
    this._signinError = document.getElementById("dj-signin-error");
    this._signedInLabel = document.getElementById("dj-signed-in-label");
    this._linksContainer = document.getElementById("dj-links-container");
    this._genreTags = document.getElementById("dj-genre-tags");
    this._availList = document.getElementById("dj-avail-list");
    this._bookingsList = document.getElementById("dj-bookings-list");

    document.getElementById("dj-profile-logo")?.addEventListener("input", (e) => {
      this._updateProfileField("logo", e.target.value.trim());
      this._updateLogoPreview(e.target.value.trim());
    });

    document.getElementById("dj-display-name")?.addEventListener("input", (e) => {
      this._updateProfileField("display_name", e.target.value);
    });

    // Logo file picker + drag-and-drop
    this._initLogoUploader();

    document.getElementById("btn-dj-add-genre")?.addEventListener("click", () => this._addGenre());
    document.getElementById("dj-genre-input")?.addEventListener("keydown", (e) => {
      if (e.key === "Enter") { e.preventDefault(); this._addGenre(); }
    });

    document.getElementById("btn-dj-add-avail")?.addEventListener("click", () => this._addAvailability());
    document.getElementById("btn-dj-refresh-bookings")?.addEventListener("click", () => this._refreshBookings());

    // Auto-update when user signs in/out via the topbar Discord button
    this._bus.subscribe("auth_changed", (session) => {
      if (session?.name) {
        this._restoreSession();
      } else {
        this._profile = null;
        if (this._signinView) this._signinView.hidden = false;
        if (this._profileView) this._profileView.hidden = true;
      }
    });

    // Try restoring session from storage
    this._restoreSession();
  }

  // ── Sign-in ───────────────────────────────────────────────────────────

  async _signIn() {
    this._setError("");
    try {
      const urlResp = await this._api.getDiscordLoginUrl();
      const loginUrl = typeof urlResp === "string" ? urlResp : urlResp?.url;
      if (!loginUrl) { this._setError("Could not get login URL."); return; }

      // Open popup for Discord OAuth
      const popup = window.open(loginUrl, "discord_auth", "width=500,height=700");
      if (!popup) { this._setError("Popup blocked — allow popups and try again."); return; }

      // Listen for message from OAuth redirect page
      const result = await new Promise((resolve) => {
        const handler = (event) => {
          if (event.data?.type === "discord_auth") {
            window.removeEventListener("message", handler);
            resolve(event.data);
          }
        };
        window.addEventListener("message", handler);
        // Fallback timeout
        setTimeout(() => {
          window.removeEventListener("message", handler);
          resolve(null);
        }, 120_000);
      });

      if (!result?.discord_id || !result?.username) {
        this._setError("Discord sign-in was cancelled or failed.");
        return;
      }

      const resp = await this._api.djDiscordAuth(result.discord_id, result.username);
      const djName = resp?.name ?? result.username;

      // Fetch full profile
      this._profile = await this._api.djGetProfile(djName);
      this._profile.discord_id = result.discord_id;

      // Persist session
      this._storage.setDjSession({ name: djName, discord_id: result.discord_id });

      this._showProfile();
    } catch (err) {
      this._setError(err.message || "Sign-in failed.");
    }
  }

  _restoreSession() {
    const session = this._storage.getDjSession();
    if (!session?.name) return;

    // Show basic info from session immediately while the API call is in flight
    if (!this._profile) {
      this._profile = { name: session.name, discord_id: session.discord_id };
      this._showProfile();
    }

    // Try loading full profile from server
    this._api.djGetProfile(session.name).then((profile) => {
      this._profile = profile;
      this._profile.discord_id = session.discord_id;
      this._showProfile();
    }).catch(() => {
      // Server unavailable — basic session view already shown above
    });
  }

  // ── Profile display ───────────────────────────────────────────────────

  _showProfile() {
    if (!this._profile) return;

    if (this._signinView) this._signinView.hidden = true;
    if (this._profileView) this._profileView.hidden = false;
    if (this._signedInLabel) this._signedInLabel.textContent = `Signed in as ${this._profile.name}`;

    this._buildLinks();
    this._refreshGenres();
    this._refreshAvailability();
    this._refreshBookings();

    // Populate logo
    const logoInput = document.getElementById("dj-profile-logo");
    if (logoInput) logoInput.value = this._profile.logo ?? "";
    this._updateLogoPreview(this._profile.logo ?? "");

    // Populate display name
    const displayInput = document.getElementById("dj-display-name");
    if (displayInput) displayInput.value = this._profile.display_name ?? "";
  }

  // ── Links ─────────────────────────────────────────────────────────────

  // ── Logo uploader ─────────────────────────────────────────────────────

  _initLogoUploader() {
    const dropZone = document.getElementById("dj-logo-drop-zone");
    const fileInput = document.getElementById("dj-logo-file");
    const browseBtn = document.getElementById("btn-dj-logo-browse");
    if (!dropZone || !fileInput) return;

    // Click anywhere on drop zone (except the browse button) opens picker
    dropZone.addEventListener("click", (e) => {
      if (e.target !== browseBtn) fileInput.click();
    });
    browseBtn?.addEventListener("click", (e) => {
      e.stopPropagation();
      fileInput.click();
    });

    fileInput.addEventListener("change", () => {
      if (fileInput.files?.[0]) this._loadImageFile(fileInput.files[0]);
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
      if (file && file.type.startsWith("image/")) this._loadImageFile(file);
    });
  }

  async _loadImageFile(file) {
    // Show a quick local preview immediately while the upload is in flight
    const localUrl = URL.createObjectURL(file);
    this._updateLogoPreview(localUrl);

    const url = await this._images.upload(file);
    URL.revokeObjectURL(localUrl);

    this._updateLogoPreview(url);
    this._updateProfileField("logo", url);
    const logoInput = document.getElementById("dj-profile-logo");
    if (logoInput) logoInput.value = ""; // clear URL field, file takes precedence
  }

  _updateLogoPreview(src) {
    const preview = document.getElementById("dj-logo-preview");
    const placeholder = document.getElementById("dj-logo-placeholder");
    if (!preview || !placeholder) return;
    if (src) {
      preview.src = src;
      preview.style.display = "block";
      placeholder.style.display = "none";
    } else {
      preview.src = "";
      preview.style.display = "none";
      placeholder.style.display = "flex";
    }
  }

  _buildLinks() {
    if (!this._linksContainer) return;
    this._linksContainer.innerHTML = "";
    const links = this._profile?.links ?? {};

    for (const { key, hint } of DJ_LINK_FIELDS) {
      const row = document.createElement("div");
      row.className = "field-row";
      row.innerHTML = `
        <label class="field-label" style="width:90px">${key.toUpperCase()}</label>
        <input type="text" class="input input--sm" data-dj-link="${key}"
               value="${this._esc(links[key] ?? "")}"
               placeholder="${hint}" style="flex:1" />`;
      this._linksContainer.appendChild(row);

      row.querySelector("input")?.addEventListener("input", (e) => {
        if (!this._profile.links) this._profile.links = {};
        this._profile.links[key] = e.target.value.trim();
        this._scheduleSync();
      });
    }
  }

  // ── Genres ────────────────────────────────────────────────────────────

  _addGenre() {
    const input = document.getElementById("dj-genre-input");
    const val = input?.value?.trim();
    if (!val || !this._profile) return;

    if (!this._profile.genres) this._profile.genres = [];
    if (this._profile.genres.includes(val)) { input.value = ""; return; }

    this._profile.genres.push(val);
    input.value = "";
    this._refreshGenres();
    this._scheduleSync();
  }

  _removeGenre(genre) {
    if (!this._profile?.genres) return;
    this._profile.genres = this._profile.genres.filter((g) => g !== genre);
    this._refreshGenres();
    this._scheduleSync();
  }

  _refreshGenres() {
    if (!this._genreTags || !this._profile) return;
    this._genreTags.innerHTML = "";

    for (const g of this._profile.genres ?? []) {
      const tag = document.createElement("span");
      tag.className = "genre-tag";
      tag.innerHTML = `${this._esc(g)} <button class="genre-tag__remove">&times;</button>`;
      tag.querySelector("button")?.addEventListener("click", () => this._removeGenre(g));
      this._genreTags.appendChild(tag);
    }

    if (!this._profile.genres?.length) {
      const empty = document.createElement("p");
      empty.className = "muted-text";
      empty.textContent = "No genres added.";
      this._genreTags.appendChild(empty);
    }
  }

  // ── Availability ──────────────────────────────────────────────────────

  _addAvailability() {
    if (!this._profile) return;
    if (!this._profile.availability) this._profile.availability = [];
    this._profile.availability.push({ date: "", start: "8:00 PM", end: "11:00 PM" });
    this._refreshAvailability();
    this._scheduleSync();
  }

  _removeAvailability(idx) {
    if (!this._profile?.availability) return;
    this._profile.availability.splice(idx, 1);
    this._refreshAvailability();
    this._scheduleSync();
  }

  _refreshAvailability() {
    if (!this._availList || !this._profile) return;
    this._availList.innerHTML = "";

    const avail = this._profile.availability ?? [];
    if (!avail.length) {
      const empty = document.createElement("p");
      empty.className = "muted-text";
      empty.textContent = "No availability set.";
      this._availList.appendChild(empty);
      return;
    }

    avail.forEach((entry, idx) => {
      const row = document.createElement("div");
      row.className = "avail-row";
      row.innerHTML = `
        <input type="date" class="input input--sm avail-date" value="${entry.date ?? ""}" />
        <input type="text" class="input input--sm avail-time" value="${this._esc(entry.start ?? "8:00 PM")}" placeholder="Start" />
        <span class="avail-sep">–</span>
        <input type="text" class="input input--sm avail-time" value="${this._esc(entry.end ?? "11:00 PM")}" placeholder="End" />
        <button class="btn btn--icon btn--danger avail-remove" title="Remove">
          <span class="material-symbols-rounded">close</span>
        </button>`;

      const inputs = row.querySelectorAll("input");
      inputs[0]?.addEventListener("change", (e) => { entry.date = e.target.value; this._scheduleSync(); });
      inputs[1]?.addEventListener("input", (e) => { entry.start = e.target.value.trim(); this._scheduleSync(); });
      inputs[2]?.addEventListener("input", (e) => { entry.end = e.target.value.trim(); this._scheduleSync(); });
      row.querySelector(".avail-remove")?.addEventListener("click", () => this._removeAvailability(idx));

      this._availList.appendChild(row);
    });
  }

  // ── Bookings ──────────────────────────────────────────────────────────

  async _refreshBookings() {
    if (!this._bookingsList || !this._profile?.name) return;
    this._bookingsList.innerHTML = '<p class="muted-text">Loading...</p>';

    try {
      const bookings = await this._api.listDjBookings(this._profile.name);
      this._renderBookings(Array.isArray(bookings) ? bookings : []);
    } catch {
      this._bookingsList.innerHTML = '<p class="muted-text">Could not load bookings.</p>';
    }
  }

  _renderBookings(bookings) {
    if (!this._bookingsList) return;
    this._bookingsList.innerHTML = "";

    const pending = bookings.filter((b) => b.status === "pending");

    // Update DJ tab badge with pending count
    this._tabs?.setBadge("dj", pending.length);

    if (!pending.length) {
      this._bookingsList.innerHTML = '<p class="muted-text">No pending bookings.</p>';
      return;
    }

    for (const b of pending) {
      const card = document.createElement("div");
      card.className = "booking-card";
      card.innerHTML = `
        <div class="booking-card__info">
          <strong>${this._esc(b.group_name || b.event_title || "Booking")}</strong>
          <span class="muted-text">${this._esc(b.event_date || "")} ${this._esc(b.start_time || "")}</span>
          ${b.message ? `<span class="muted-text">${this._esc(b.message)}</span>` : ""}
        </div>
        <div class="booking-card__actions">
          <button class="btn btn--primary btn--sm booking-accept">Accept</button>
          <button class="btn btn--danger btn--sm booking-decline">Decline</button>
        </div>`;

      card.querySelector(".booking-accept")?.addEventListener("click", () => this._respondBooking(b.id, "accepted"));
      card.querySelector(".booking-decline")?.addEventListener("click", () => this._respondBooking(b.id, "declined"));
      this._bookingsList.appendChild(card);
    }
  }

  async _respondBooking(bookingId, status) {
    try {
      await this._api.respondToBooking(bookingId, status);
      this._refreshBookings();
    } catch (err) {
      this._modal.confirm(`Failed to respond: ${err.message}`, "OK");
    }
  }

  // ── Server sync ───────────────────────────────────────────────────────

  _scheduleSync() {
    clearTimeout(this._syncTimer);
    this._syncTimer = setTimeout(() => this._syncToServer(), 800);
  }

  async _syncToServer() {
    if (!this._profile?.name) return;
    try {
      await this._api.djUpdateProfile(
        this._profile.name,
        this._profile.links ?? {},
        this._profile.logo ?? "",
        this._profile.genres ?? [],
        this._profile.availability ?? [],
        this._profile.display_name ?? "",
      );
    } catch {
      // Silent failure — will retry on next edit
    }
  }

  _updateProfileField(key, value) {
    if (!this._profile) return;
    this._profile[key] = value;
    this._scheduleSync();
  }

  // ── Helpers ───────────────────────────────────────────────────────────

  _setError(msg) {
    if (this._signinError) this._signinError.textContent = msg;
  }

  _esc(str) {
    return String(str).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
  }
}
