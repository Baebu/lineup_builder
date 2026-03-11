/**
 * ImageStorageService — uploads images to the server and returns a hosted URL.
 *
 * On success: returns the full URL of the stored image (e.g. http://server/images/abc.jpg).
 * On failure: falls back to an in-memory base64 data URL so the UI still works offline.
 */

const BASE_URL = import.meta.env?.VITE_API_URL ?? "";

export class ImageStorageService {
  /** @param {string} [baseUrl] Server base URL (default: same origin) */
  constructor(baseUrl = BASE_URL) {
    this._baseUrl = baseUrl.replace(/\/$/, "");
  }

  /**
   * Upload a File and return a URL string pointing to the stored image.
   * @param {File} file
   * @returns {Promise<string>}
   */
  async upload(file) {
    try {
      const form = new FormData();
      form.append("file", file);

      const res = await fetch(`${this._baseUrl}/images/upload`, {
        method: "POST",
        body: form,
      });

      if (!res.ok) {
        const msg = await res.text().catch(() => res.statusText);
        throw new Error(`Server returned ${res.status}: ${msg}`);
      }

      const { url } = await res.json();
      // url is a server-relative path like /images/abc123.jpg
      return url.startsWith("http") ? url : this._baseUrl + url;
    } catch (err) {
      console.warn("ImageStorageService: upload failed, using base64 fallback.", err);
      return this._toDataUrl(file);
    }
  }

  /** Convert a File to a base64 data URL in-browser. */
  _toDataUrl(file) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = (e) => resolve(e.target.result);
      reader.onerror = reject;
      reader.readAsDataURL(file);
    });
  }
}
