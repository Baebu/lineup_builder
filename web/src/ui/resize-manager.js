/**
 * ResizeManager — makes the #resize-handle draggable to resize left panel.
 *
 * The left panel width is stored in localStorage under "lineup_panel_width"
 * and restored on init.
 */
const STORAGE_KEY = "lineup_panel_width";
const MIN_WIDTH = 220;
const RIGHT_MIN = 450; // keep right panel at least this wide
const HANDLE_W = 5;
const getMaxWidth = () => window.innerWidth - RIGHT_MIN - HANDLE_W;

export class ResizeManager {
  init() {
    this._initPanelResize();
    this._initOutputResize();
  }

  _initPanelResize() {
    const handle = document.getElementById("resize-handle");
    const panelLeft = document.getElementById("panel-left");
    if (!handle || !panelLeft) return;

    // Restore saved width
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) {
      const w = parseInt(saved, 10);
      if (w >= MIN_WIDTH && w <= getMaxWidth()) {
        panelLeft.style.width = `${w}px`;
        panelLeft.style.flex = "none";
      }
    }

    let dragging = false;
    let startX = 0;
    let startW = 0;

    handle.addEventListener("mousedown", (e) => {
      e.preventDefault();
      dragging = true;
      startX = e.clientX;
      startW = panelLeft.getBoundingClientRect().width;
      document.body.style.cursor = "col-resize";
      document.body.style.userSelect = "none";
    });

    document.addEventListener("mousemove", (e) => {
      if (!dragging) return;
      const delta = e.clientX - startX;
      const newW = Math.min(getMaxWidth(), Math.max(MIN_WIDTH, startW + delta));
      panelLeft.style.width = `${newW}px`;
      panelLeft.style.flex = "none";
    });

    document.addEventListener("mouseup", () => {
      if (!dragging) return;
      dragging = false;
      document.body.style.cursor = "";
      document.body.style.userSelect = "";
      const w = Math.round(panelLeft.getBoundingClientRect().width);
      localStorage.setItem(STORAGE_KEY, String(w));
    });

    // Touch support
    handle.addEventListener("touchstart", (e) => {
      const t = e.touches[0];
      dragging = true;
      startX = t.clientX;
      startW = panelLeft.getBoundingClientRect().width;
    }, { passive: true });

    document.addEventListener("touchmove", (e) => {
      if (!dragging) return;
      const t = e.touches[0];
      const delta = t.clientX - startX;
      const newW = Math.min(getMaxWidth(), Math.max(MIN_WIDTH, startW + delta));
      panelLeft.style.width = `${newW}px`;
      panelLeft.style.flex = "none";
    }, { passive: true });

    document.addEventListener("touchend", () => {
      if (!dragging) return;
      dragging = false;
      const w = Math.round(panelLeft.getBoundingClientRect().width);
      localStorage.setItem(STORAGE_KEY, String(w));
    });
  }

  _initOutputResize() {
    const handle = document.getElementById("output-resize-handle");
    const outputSection = document.getElementById("output-section");
    const panelRight = outputSection?.closest(".panel--right");
    if (!handle || !outputSection || !panelRight) return;

    const OUTPUT_STORAGE_KEY = "lineup_output_height";
    const OUTPUT_MIN = 120;
    const getOutputMax = () => panelRight.getBoundingClientRect().height * 0.70;

    // Restore saved height
    const saved = parseInt(localStorage.getItem(OUTPUT_STORAGE_KEY) || "0", 10);
    if (saved >= OUTPUT_MIN) outputSection.style.height = `${saved}px`;

    let dragging = false;
    let startY = 0;
    let startH = 0;

    handle.addEventListener("mousedown", (e) => {
      e.preventDefault();
      dragging = true;
      startY = e.clientY;
      startH = outputSection.getBoundingClientRect().height;
      document.body.style.cursor = "row-resize";
      document.body.style.userSelect = "none";
      handle.classList.add("dragging");
    });

    document.addEventListener("mousemove", (e) => {
      if (!dragging) return;
      // Dragging up increases height, dragging down decreases
      const delta = startY - e.clientY;
      const newH = Math.min(getOutputMax(), Math.max(OUTPUT_MIN, startH + delta));
      outputSection.style.height = `${newH}px`;
    });

    document.addEventListener("mouseup", () => {
      if (!dragging) return;
      dragging = false;
      document.body.style.cursor = "";
      document.body.style.userSelect = "";
      handle.classList.remove("dragging");
      const h = Math.round(outputSection.getBoundingClientRect().height);
      localStorage.setItem(OUTPUT_STORAGE_KEY, String(h));
    });

    // Touch support
    handle.addEventListener("touchstart", (e) => {
      const t = e.touches[0];
      dragging = true;
      startY = t.clientY;
      startH = outputSection.getBoundingClientRect().height;
    }, { passive: true });

    document.addEventListener("touchmove", (e) => {
      if (!dragging) return;
      const t = e.touches[0];
      const delta = startY - t.clientY;
      const newH = Math.min(getOutputMax(), Math.max(OUTPUT_MIN, startH + delta));
      outputSection.style.height = `${newH}px`;
    }, { passive: true });

    document.addEventListener("touchend", () => {
      if (!dragging) return;
      dragging = false;
      const h = Math.round(outputSection.getBoundingClientRect().height);
      localStorage.setItem(OUTPUT_STORAGE_KEY, String(h));
    });
  }
}
