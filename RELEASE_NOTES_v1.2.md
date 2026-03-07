# Lineup Builder v1.2 — Release Notes

## Discord Bot Integration

- **Discord Bot** — Connect a Discord bot directly from the app. Configure your bot token, client ID, and invite link via a compact settings popup.
- **Rich Embed Posting** — Lineup posts are sent as styled Discord embeds with event title, start timestamp, genre tags, full lineup with times, and social links. Embed color matches your current theme accent.
- **Embed Image** — Attach a poster image to your Discord embed by pasting a URL or browsing for a local file. Inline controls (text input + Browse + Clear) keep the workflow compact.
- **Channel Picker** — Fetches your server's text channels via the bot API so you can post to Events, Popup, or Signups channels by name.
- **Scheduled Posting** — Schedule posts for future delivery. Pick a date/time, select a channel, and the app will automatically send the embed when the time arrives. Scheduled posts persist across restarts.
- **`.env` Support** — Bot token, client ID, and client secret can be loaded from a `.env` file in the app directory for secure credential management.

## Social Links & Output

- **Social Links** — Add social media / streaming links (Twitch, SoundCloud, etc.) that appear at the bottom of your lineup output and Discord embeds.
- **GitHub Footer** — Discord embeds now include a footer linking back to the project repo.

## Themes & UI

- **8 Built-in Theme Presets** — Slate (default), Midnight Blue, OLED Black, Crimson, Amber, Forest, Ocean, Violet.
- **User Presets** — Save and manage your own custom theme presets.
- **Title Bar Theming** — The window title bar color follows your active theme.
- **Button Color Fix** — Button colors now update correctly when switching themes.

## Stability & Data

- **Autosave & Crash Recovery** — Automatic periodic saves with a restore-from-autosave modal on startup if unsaved work is detected.
- **Improved YAML/JSON Persistence** — Fixed social links parsing, autosave reliability, and modal restore flows.
- **Slot Placeholder** — Empty slots show a placeholder prompt instead of blank space.

## Internal

- Renamed `DJRosterMixin` → `RosterMixin` and `dj_roster.py` → `roster.py`.
- Added `discord_service.py` and `discord_oauth.py` backend modules (GUI-free).
- Updated PyInstaller spec with new hidden imports.

---

**Full Changelog:** [v1.1...v1.2](https://github.com/Baebu/lineup_builder/compare/v1.1...v1.2)
