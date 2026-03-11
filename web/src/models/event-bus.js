/**
 * Lightweight publish-subscribe event bus.
 *
 * Port of desktop/src/backend/models/event_bus.py
 */
export class EventBus {
  constructor() {
    /** @type {Map<string, Set<Function>>} */
    this._subs = new Map();
  }

  /**
   * Register a callback for an event. Duplicates are ignored.
   * @param {string} event
   * @param {Function} callback
   */
  subscribe(event, callback) {
    if (!this._subs.has(event)) this._subs.set(event, new Set());
    this._subs.get(event).add(callback);
  }

  /**
   * Remove a callback. No-op if not registered.
   * @param {string} event
   * @param {Function} callback
   */
  unsubscribe(event, callback) {
    this._subs.get(event)?.delete(callback);
  }

  /**
   * Notify all subscribers of an event.
   * @param {string} event
   * @param {Object} [data]
   */
  publish(event, data = {}) {
    for (const cb of this._subs.get(event) ?? []) {
      cb(data);
    }
  }

  /** Remove all subscriptions. */
  clear() {
    this._subs.clear();
  }
}
