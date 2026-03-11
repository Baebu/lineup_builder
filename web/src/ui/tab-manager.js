/**
 * TabManager — handles tab switching for both left and right tab groups.
 *
 * Tab buttons carry `data-tab="<id>"` and toggle `.active` on themselves
 * and their corresponding `.tab-content#tab-<id>` element.
 */
export class TabManager {
  init() {
    this._bindGroup("left-tabs");
    this._bindGroup("right-tabs");
  }

  _bindGroup(groupId) {
    const nav = document.getElementById(groupId);
    if (!nav) return;

    nav.addEventListener("click", (e) => {
      const btn = e.target.closest(".tab");
      if (!btn) return;

      const tabId = btn.dataset.tab;
      if (!tabId) return;

      // Clear badge when the user clicks the tab
      this.clearBadge(tabId);

      // Deactivate all sibling tabs
      nav.querySelectorAll(".tab").forEach((t) => t.classList.remove("active"));
      btn.classList.add("active");

      // Deactivate all sibling tab-content panels
      const panel = nav.closest(".panel, aside");
      if (panel) {
        panel.querySelectorAll(".tab-content").forEach((c) => c.classList.remove("active"));
        const target = document.getElementById(`tab-${tabId}`);
        if (target) target.classList.add("active");
      }
    });
  }

  /** Programmatically activate a tab by its id string (e.g. "roster"). */
  activate(tabId) {
    const btn = document.querySelector(`.tab[data-tab="${tabId}"]`);
    if (btn) btn.click();
  }

  /**
   * Show a numeric badge on a tab.
   * @param {string} tabId  e.g. "dj" or "club"
   * @param {number} count
   */
  setBadge(tabId, count) {
    const badge = document.getElementById(`badge-${tabId}`);
    if (!badge) return;
    if (count > 0) {
      badge.textContent = count > 99 ? "99+" : String(count);
      badge.hidden = false;
    } else {
      badge.hidden = true;
    }
  }

  /** Hide the badge for a tab. */
  clearBadge(tabId) {
    const badge = document.getElementById(`badge-${tabId}`);
    if (badge) badge.hidden = true;
  }
}
