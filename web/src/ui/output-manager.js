import { OutputGenerator } from "../output/output-generator.js";

/**
 * OutputManager — drives the output preview panel.
 *
 * Subscribes to model_changed, calls OutputGenerator.generate(), and updates
 * the #output-preview element. Wires format selector and copy button.
 *
 * Mirrors desktop OutputMixin.
 */
export class OutputManager {
  /**
   * @param {import('../models/event-bus.js').EventBus} bus
   * @param {import('../models/lineup-model.js').LineupModel} model
   * @param {import('../output/output-generator.js').OutputGenerator} _generator - unused, static class
   */
  constructor(bus, model, _generator) {
    this._bus = bus;
    this._model = model;
    this._preview = null;
  }

  init() {
    this._preview = document.getElementById("output-preview");

    // Format buttons (Discord/Plain) — mutually exclusive
    document.querySelectorAll(".output-format-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        document.querySelectorAll(".output-format-btn").forEach((b) => b.classList.remove("active"));
        btn.classList.add("active");
        this._model.outputFormat = btn.dataset.format;
        this._model.notify();
      });
    });

    // Stream link toggle buttons (Quest/PC) — one-or-none independent toggles
    document.querySelectorAll(".output-stream-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        const fmt = btn.dataset.stream;
        this._model.streamLinkFormat = this._model.streamLinkFormat === fmt ? "" : fmt;
        this._syncStreamBtns();
        this._model.notify();
      });
    });

    document.getElementById("btn-copy-output")?.addEventListener("click", () => this._copyOutput());
    document.getElementById("btn-refresh-output")?.addEventListener("click", () => this.update());

    this._bus.subscribe("model_changed", () => this.update());
    try { this.update(); } catch { /* deferred until model is ready */ }
  }

  update() {
    if (!this._preview) return;
    this._syncStreamBtns();
    const snap = this._model.snapshot();
    try {
      const text = OutputGenerator.generate(snap);
      this._preview.value = text;
    } catch (err) {
      this._preview.value = `[Error generating output: ${err.message}]`;
    }
  }

  _syncStreamBtns() {
    const fmt = this._model.streamLinkFormat ?? "";
    document.querySelectorAll(".output-stream-btn").forEach((btn) => {
      btn.classList.toggle("active", btn.dataset.stream === fmt);
    });
  }

  _copyOutput() {
    const text = this._preview?.value ?? "";
    if (!text) return;
    navigator.clipboard.writeText(text).then(() => {
      this._showCopied();
    }).catch(() => {
      // Fallback for non-secure contexts
      const ta = document.createElement("textarea");
      ta.value = text;
      ta.style.position = "fixed";
      ta.style.top = "-9999px";
      document.body.appendChild(ta);
      ta.select();
      document.execCommand("copy");
      ta.remove();
      this._showCopied();
    });
  }

  _showCopied() {
    const btn = document.getElementById("btn-copy-output");
    if (!btn) return;
    const icon = btn.querySelector(".material-symbols-rounded");
    if (icon) {
      const orig = icon.textContent;
      icon.textContent = "check";
      setTimeout(() => { icon.textContent = orig; }, 1500);
    }
  }
}
