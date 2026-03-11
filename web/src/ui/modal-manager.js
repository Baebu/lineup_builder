/**
 * ModalManager — renders confirm / prompt / custom modals into the shared
 * #modal-overlay / #modal-container elements defined in index.html.
 */
export class ModalManager {
  constructor() {
    this._overlay = null;
    this._container = null;
  }

  init() {
    this._overlay = document.getElementById("modal-overlay");
    this._container = document.getElementById("modal-container");

    // Close on overlay backdrop click
    this._overlay?.addEventListener("click", (e) => {
      if (e.target === this._overlay) this.close();
    });

    // Close on Escape
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && !this._overlay?.hidden) this.close();
    });
  }

  /** Show a yes/no confirm dialog. */
  confirm(message, confirmLabel = "Confirm", cancelLabel = "Cancel", onConfirm = null, onCancel = null) {
    const html = `
      <div class="modal__body">
        <p class="modal__message">${this._esc(message)}</p>
        <div class="modal__actions">
          <button class="btn btn--secondary" id="modal-cancel">${this._esc(cancelLabel)}</button>
          <button class="btn btn--primary" id="modal-confirm">${this._esc(confirmLabel)}</button>
        </div>
      </div>`;
    this._show(html);

    this._container.querySelector("#modal-confirm")?.addEventListener("click", () => {
      this.close();
      onConfirm?.();
    });
    this._container.querySelector("#modal-cancel")?.addEventListener("click", () => {
      this.close();
      onCancel?.();
    });
  }

  /** Show a text-input prompt dialog. Returns value via onSubmit(value). */
  prompt(message, defaultValue = "", placeholder = "", submitLabel = "OK", onSubmit = null) {
    const html = `
      <div class="modal__body">
        <p class="modal__message">${this._esc(message)}</p>
        <input class="input" id="modal-input" type="text"
               value="${this._esc(defaultValue)}"
               placeholder="${this._esc(placeholder)}" />
        <div class="modal__actions">
          <button class="btn btn--secondary" id="modal-cancel">Cancel</button>
          <button class="btn btn--primary" id="modal-submit">${this._esc(submitLabel)}</button>
        </div>
      </div>`;
    this._show(html);

    const input = this._container.querySelector("#modal-input");
    // Focus and select existing text
    requestAnimationFrame(() => { input?.select(); });

    const submit = () => {
      const val = input?.value ?? "";
      this.close();
      onSubmit?.(val);
    };

    this._container.querySelector("#modal-submit")?.addEventListener("click", submit);
    this._container.querySelector("#modal-cancel")?.addEventListener("click", () => this.close());
    input?.addEventListener("keydown", (e) => { if (e.key === "Enter") submit(); });
  }

  /** Show arbitrary HTML in the modal. Returns the container element for further manipulation. */
  custom(html, onClose = null) {
    this._show(html);
    this._onClose = onClose;
    return this._container;
  }

  close() {
    if (this._overlay) this._overlay.hidden = true;
    if (this._container) this._container.innerHTML = "";
    const cb = this._onClose;
    this._onClose = null;
    cb?.();
  }

  _show(html) {
    if (!this._overlay || !this._container) return;
    this._container.innerHTML = html;
    this._overlay.hidden = false;
  }

  _esc(str) {
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }
}
