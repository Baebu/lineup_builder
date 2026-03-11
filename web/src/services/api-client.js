/**
 * ApiClient — thin wrapper around the Lineup Builder REST API.
 *
 * The server base URL is read from VITE_API_URL at build time (default: same origin).
 */

const BASE_URL = import.meta.env?.VITE_API_URL ?? "";

export class ApiClient {
  constructor(baseUrl = BASE_URL) {
    this.baseUrl = baseUrl.replace(/\/$/, "");
  }

  async _request(method, path, body = null) {
    const opts = {
      method,
      headers: { "Content-Type": "application/json" },
    };
    if (body !== null) opts.body = JSON.stringify(body);
    const res = await fetch(`${this.baseUrl}${path}`, opts);
    if (!res.ok) {
      const text = await res.text().catch(() => res.statusText);
      throw new Error(`API ${method} ${path} → ${res.status}: ${text}`);
    }
    const ct = res.headers.get("Content-Type") ?? "";
    return ct.includes("application/json") ? res.json() : res.text();
  }

  get(path) {
    return this._request("GET", path);
  }

  post(path, body) {
    return this._request("POST", path, body);
  }

  put(path, body) {
    return this._request("PUT", path, body);
  }

  delete(path) {
    return this._request("DELETE", path);
  }

  // ── VRChat ────────────────────────────────────────────────────────────

  async getVrcState() {
    return this.get("/api/vrchat/state");
  }

  // ── Discord OAuth ─────────────────────────────────────────────────────

  async getDiscordLoginUrl() {
    return this.get("/api/discord/login-url");
  }

  // ── Discord Bot ───────────────────────────────────────────────────────

  async getDiscordGuilds() {
    return this.get("/guilds");
  }

  async getGuildRoles(guildId) {
    return this.get(`/guilds/${guildId}/roles`);
  }

  async getGuildChannels(guildId) {
    return this.get(`/guilds/${guildId}/channels`);
  }

  async getBotStatus() {
    return this.get("/bot/status");
  }

  async postEmbed(channelId, embedData, imageUrl = "") {
    return this.post("/post/embed", {
      channel_id: String(channelId),
      ...embedData,
      image_url: imageUrl,
    });
  }

  async postMessage(channelId, content) {
    return this.post("/post/message", {
      channel_id: String(channelId),
      content,
    });
  }

  async createScheduledPost(postAtUtc, channelId, embedData, imageUrl = "") {
    return this.post("/schedule", {
      post_at_utc: postAtUtc,
      channel_id: String(channelId),
      ...embedData,
      image_url: imageUrl,
    });
  }

  async listScheduledPosts() {
    return this.get("/schedule");
  }

  async cancelScheduledPost(postId) {
    return this.delete(`/schedule/${postId}`);
  }

  async updateScheduledPost(postId, data) {
    return this.put(`/schedule/${postId}`, data);
  }

  async getSentPosts() {
    return this.get("/sent");
  }

  async deleteSentPost(postId) {
    return this.delete(`/sent/${postId}`);
  }

  async resendPost(postId, channelId = null) {
    return this.post(`/sent/${postId}/resend`, { channel_id: channelId });
  }

  async listGroupBookings(groupName) {
    return this.get(`/bookings/group/${encodeURIComponent(groupName)}`);
  }

  // ── DJ Profiles ─────────────────────────────────────────────────────

  async djDiscordAuth(discordId, name) {
    return this.post("/dj/discord-auth", { discord_id: discordId, name });
  }

  async djGetProfile(name) {
    return this.get(`/dj/profile/${encodeURIComponent(name)}`);
  }

  async djUpdateProfile(name, links, logo, genres, availability, displayName = "") {
    return this.put("/dj/profile", { name, display_name: displayName, links, logo, genres, availability });
  }

  async djList() {
    return this.get("/dj/list");
  }

  // ── Bookings ──────────────────────────────────────────────────────────

  async createBooking(data) {
    return this.post("/booking", data);
  }

  async listDjBookings(djName) {
    return this.get(`/bookings/dj/${encodeURIComponent(djName)}`);
  }

  async respondToBooking(bookingId, status) {
    return this.put(`/booking/${bookingId}/respond`, { status });
  }

  // ── VRChat ────────────────────────────────────────────────────────────

  async verifyVrchatBio(vrchatUsername, verificationCode) {
    return this.post("/vrchat/verify-bio", {
      vrchat_username: vrchatUsername,
      verification_code: verificationCode,
    });
  }

  async verifyVrchatGroup(groupId, discordId, vrchatUserId) {
    return this.post("/vrchat/verify-group", {
      group_id: groupId,
      discord_id: discordId,
      vrchat_user_id: vrchatUserId,
    });
  }

  async getVrchatGroup(discordId) {
    return this.get(`/user/${encodeURIComponent(discordId)}/vrchat-group`);
  }

  async getVrchatUserGroups(vrchatUserId) {
    return this.get(`/vrchat/user/${encodeURIComponent(vrchatUserId)}/groups`);
  }

  // ── Club ──────────────────────────────────────────────────────────────

  async getClub(discordId) {
    return this.get(`/user/${encodeURIComponent(discordId)}/club`);
  }

  async updateClub(discordId, data) {
    return this.put(`/user/${encodeURIComponent(discordId)}/club`, data);
  }

  // ── User Data (cloud sync) ───────────────────────────────────────────

  async getUserData(discordId, key) {
    return this.get(`/user/${encodeURIComponent(discordId)}/data/${key}`);
  }

  async putUserData(discordId, key, value) {
    return this.put(`/user/${encodeURIComponent(discordId)}/data/${key}`, { value });
  }

  async getAllUserData(discordId) {
    return this.get(`/user/${encodeURIComponent(discordId)}/data`);
  }
}
