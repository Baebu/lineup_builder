/**
 * AuthManager — login pill + Discord OAuth modal.
 *
 * Manages the top-right login pill that opens a Discord sign-in modal.
 * Persists session to localStorage via StorageManager.
 */
export class AuthManager {
  /**
   * @param {import('../services/api-client.js').ApiClient} api
   * @param {import('./modal-manager.js').ModalManager} modal
   * @param {import('../services/storage.js').StorageManager} storage
   * @param {import('../models/event-bus.js').EventBus} bus
   */
  constructor(api, modal, storage, bus) {
    this._api = api;
    this._modal = modal;
    this._storage = storage;
    this._bus = bus;

    this._pill = null;
    this._session = null; // { name, discord_id, avatar }
  }

  init() {
    this._pill = document.getElementById("btn-login");
    this._pill?.addEventListener("click", () => this._onPillClick());

    // Restore saved session
    this._restoreSession();
  }

  // ── Pill state ─────────────────────────────────────────────────────────

  _updatePill() {
    if (!this._pill) return;
    if (this._session) {
      this._pill.classList.add("login-pill--active");
      this._pill.title = `Signed in as ${this._session.name}`;

      if (this._session.avatar) {
        this._pill.innerHTML =
          `<img class="login-pill__avatar" src="${this._avatarUrl()}" alt="" />` +
          `<span class="login-pill__label">${this._esc(this._session.name)}</span>`;
      } else {
        this._pill.innerHTML =
          `<span class="material-symbols-rounded login-pill__icon">person</span>` +
          `<span class="login-pill__label">${this._esc(this._session.name)}</span>`;
      }
    } else {
      this._pill.classList.remove("login-pill--active");
      this._pill.title = "Sign in with Discord";
      this._pill.innerHTML =
        `<span class="material-symbols-rounded login-pill__icon">person</span>` +
        `<span class="login-pill__label">Sign In</span>`;
    }
  }

  _onPillClick() {
    if (this._session) {
      this._showProfileModal();
    } else {
      this._showLoginModal();
    }
  }

  // ── Login modal ────────────────────────────────────────────────────────

  _showLoginModal() {
    this._modal.custom(`
      <div class="modal__body" style="align-items:center; text-align:center;">
        <span class="material-symbols-rounded" style="font-size:48px; color:var(--color-primary);">person</span>
        <h3 style="margin:0; color:var(--color-text-primary);">Sign In</h3>
        <p style="margin:0; color:var(--color-text-secondary); font-size:var(--text-sm);">
          Connect your Discord account to sync your DJ profile, bookings, and preferences.
        </p>
        <button class="btn btn--primary btn--full-inner" id="modal-discord-signin"
                style="margin-top:var(--space-2); gap:var(--space-2);">
          <svg width="20" height="15" viewBox="0 0 71 55" fill="currentColor">
            <path d="M60.1 4.9A58.5 58.5 0 0 0 45.4.2a.2.2 0 0 0-.2.1 40.8 40.8 0 0 0-1.8 3.7 54 54 0 0 0-16.2 0A37 37 0 0 0 25.4.3a.2.2 0 0 0-.2-.1A58.4 58.4 0 0 0 10.5 5a.2.2 0 0 0-.1 0C1.5 17.2-.9 29 .3 40.7a.2.2 0 0 0 .1.2 58.7 58.7 0 0 0 17.7 9 .2.2 0 0 0 .3-.1 42 42 0 0 0 3.6-5.9.2.2 0 0 0-.1-.3 38.6 38.6 0 0 1-5.5-2.6.2.2 0 0 1 0-.4l1.1-.9a.2.2 0 0 1 .2 0 41.9 41.9 0 0 0 35.6 0 .2.2 0 0 1 .2 0l1.1.9a.2.2 0 0 1 0 .3 36.3 36.3 0 0 1-5.5 2.6.2.2 0 0 0-.1.4 47.2 47.2 0 0 0 3.6 5.8.2.2 0 0 0 .3.1 58.5 58.5 0 0 0 17.7-9 .2.2 0 0 0 .1-.1c1.4-14.5-2.3-27.1-9.9-38.3a.2.2 0 0 0-.1-.1zM23.7 33.4c-3.3 0-6-3-6-6.7s2.7-6.7 6-6.7c3.4 0 6.1 3 6 6.7 0 3.7-2.7 6.7-6 6.7zm22.2 0c-3.3 0-6-3-6-6.7s2.6-6.7 6-6.7c3.4 0 6 3 6 6.7 0 3.7-2.6 6.7-6 6.7z"/>
          </svg>
          Sign in with Discord
        </button>
        <p id="modal-login-error" style="color:var(--color-danger); font-size:var(--text-sm); margin:0; display:none;"></p>
      </div>
    `);

    document.getElementById("modal-discord-signin")?.addEventListener("click", () => {
      this._startOAuth();
    });
  }

  // ── Profile modal (signed in) ──────────────────────────────────────────

  _showProfileModal() {
    const s = this._session;
    const avatarHtml = s.avatar
      ? `<img class="login-pill__avatar" src="${this._avatarUrl()}" alt=""
              style="width:48px; height:48px;" />`
      : `<span class="material-symbols-rounded"
              style="font-size:48px; color:var(--color-primary);">person</span>`;

    this._modal.custom(`
      <div class="modal__body" style="align-items:center; text-align:center;">
        ${avatarHtml}
        <h3 style="margin:0; color:var(--color-text-primary);">${this._esc(s.name)}</h3>
        <p style="margin:0; color:var(--color-text-secondary); font-size:var(--text-sm);">
          Signed in via Discord
        </p>
        <div class="modal__actions" style="justify-content:center; margin-top:var(--space-2);">
          <button class="btn btn--danger btn--sm" id="modal-signout">Sign Out</button>
        </div>
      </div>
    `);

    document.getElementById("modal-signout")?.addEventListener("click", () => {
      this._signOut();
      this._modal.close();
    });
  }

  // ── OAuth flow ─────────────────────────────────────────────────────────

  async _startOAuth() {
    const errEl = document.getElementById("modal-login-error");
    const showErr = (msg) => {
      if (errEl) { errEl.textContent = msg; errEl.style.display = "block"; }
    };

    try {
      const urlResp = await this._api.getDiscordLoginUrl();
      const loginUrl = typeof urlResp === "string" ? urlResp : urlResp?.url;
      if (!loginUrl) { showErr("Could not get login URL."); return; }

      const popup = window.open(loginUrl, "discord_auth", "width=500,height=700");
      if (!popup) { showErr("Popup blocked — allow popups and try again."); return; }

      // Listen for postMessage from OAuth redirect
      const result = await new Promise((resolve) => {
        const handler = (event) => {
          if (event.data?.type === "discord_auth") {
            window.removeEventListener("message", handler);
            resolve(event.data);
          }
        };
        window.addEventListener("message", handler);
        setTimeout(() => {
          window.removeEventListener("message", handler);
          resolve(null);
        }, 120_000);
      });

      if (!result?.discord_id || !result?.username) {
        showErr("Discord sign-in was cancelled or failed.");
        return;
      }

      // Register / sign in via server
      const resp = await this._api.djDiscordAuth(result.discord_id, result.username);
      const name = resp?.name ?? result.username;
      const verify_code = this._generateVerifyCode(result.discord_id);

      this._session = {
        name,
        discord_id: result.discord_id,
        avatar: result.avatar ?? null,
        verify_code,
      };

      // Persist session
      this._storage.setDjSession({
        name,
        discord_id: result.discord_id,
        avatar: result.avatar ?? null,
        verify_code,
      });

      this._updatePill();
      this._bus.publish("auth_changed", this._session);
      this._modal.close();
    } catch (err) {
      showErr(err.message || "Sign-in failed.");
    }
  }

  // ── Session persistence ────────────────────────────────────────────────

  _restoreSession() {
    const saved = this._storage.getDjSession();
    if (!saved?.name) { this._updatePill(); return; }

    // Ensure legacy sessions without a code get one generated
    const verify_code = saved.verify_code ?? this._generateVerifyCode(saved.discord_id);
    if (!saved.verify_code) {
      this._storage.setDjSession({ ...saved, verify_code });
    }

    this._session = {
      name: saved.name,
      discord_id: saved.discord_id,
      avatar: saved.avatar ?? null,
      verify_code,
    };
    this._updatePill();
    this._bus.publish("auth_changed", this._session);
  }

  _signOut() {
    this._session = null;
    this._storage.clearDjSession();
    this._updatePill();
    this._bus.publish("auth_changed", null);
  }

  // ── Helpers ────────────────────────────────────────────────────────────

  _avatarUrl() {
    if (!this._session?.discord_id || !this._session?.avatar) return "";
    return `https://cdn.discordapp.com/avatars/${this._session.discord_id}/${this._session.avatar}.png?size=64`;
  }

  /** Deterministic verification code derived from discord_id — same every sign-in. */
  _generateVerifyCode(discordId) {
    let hash = 0;
    for (let i = 0; i < discordId.length; i++) {
      hash = Math.imul(31, hash) + discordId.charCodeAt(i) | 0;
    }
    const hex = Math.abs(hash).toString(16).toUpperCase().padStart(8, "0").slice(0, 8);
    return `LB-${hex}`;
  }

  _esc(str) {
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }
}
