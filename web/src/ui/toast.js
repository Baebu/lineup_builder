/**
 * Global toast notification utility.
 *
 * Shows a small card at the bottom of the viewport that auto-dismisses.
 * Supports types: "success", "error", "info" (default).
 */

let _activeToast = null;

/**
 * @param {string} message
 * @param {"success"|"error"|"info"} [type="info"]
 * @param {number} [duration=2500]
 */
export function showToast(message, type = "info", duration = 2500) {
  if (!message) return;

  // Dismiss any existing toast immediately
  if (_activeToast) {
    _activeToast.remove();
    _activeToast = null;
  }

  const toast = document.createElement("div");
  toast.className = `toast toast--${type}`;
  toast.textContent = message;
  document.body.appendChild(toast);
  _activeToast = toast;

  requestAnimationFrame(() => toast.classList.add("toast--visible"));

  setTimeout(() => {
    toast.classList.remove("toast--visible");
    setTimeout(() => {
      if (_activeToast === toast) _activeToast = null;
      toast.remove();
    }, 300);
  }, duration);
}
