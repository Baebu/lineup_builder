# Lineup Builder

**Lineup Builder** is a desktop GUI application for DJs and event organizers. It streamlines scheduling sets, managing performer rosters, and generating perfectly formatted output for Discord, plain text, and VRCDN-based VR platforms (Quest/PC).

Built on **DearPyGui** with a mixin-composition architecture — the entire backend is pure Python and fully unit-testable with no GUI dependency.

---

## Screenshots

![Lineup Builder screenshot 1](assets/Screenshots/Screenshot%202026-03-07%20025936.png)
![Lineup Builder screenshot 2](assets/Screenshots/Screenshot%202026-03-07%20025953.png)
![Lineup Builder screenshot 3](assets/Screenshots/Screenshot%202026-03-07%20030001.png)
![Lineup Builder screenshot 4](assets/Screenshots/Screenshot%202026-03-07%20030012.png)

---

## Features

### Event Orchestration

- **Smart Header** — Set event titles and volume numbers. Volume auto-increments when you save a new event.
- **Integrated Date/Time Picker** — A custom-styled calendar and time selector (modal pop-up) for precise start times. Use **Arrow Up / Arrow Down** on the timestamp field to shift the time by ±15 minutes; hold **Shift** for ±24 hours.
- **Automated Import** — Paste an existing lineup from Discord or plain text. The parser extracts titles, timestamps, genres, and DJ slots, populating the editor in seconds.
- **Genre Library** — Persistent global genre list. Toggle genres on/off per event or add new tags on the fly.

### DJ Roster & Lineup Management

- **Persistent Roster** — Store frequent performers alongside their stream links. Supports **VRCDN**, **Twitch**, **YouTube**, **SoundCloud**, **Kick**, or any custom URL.
- **Exact Link Mode** — Per-DJ toggle to skip VRCDN conversion and pass the stream URL through as-is (for Twitch, YouTube, etc.).
- **Drag-and-Drop** — Drag DJs directly from your roster into a lineup slot.
- **Slot Reordering** — Reorder slots using drag handles. Start times recalculate in real-time as durations change.
- **Open Decks** — A dedicated configurable section for open-deck slots with adjustable counts and durations.
- **Events History** — Save, restore, duplicate, and delete past event lineups from a persistent YAML-backed library.

### Discord Bot Integration

- **Built-in Discord Bot** — Connect a Discord bot directly from the app. Configure your bot token and client ID via a compact settings popup.
- **Rich Embed Posting** — Lineups are posted as styled Discord embeds with event title, timestamps, genre tags, full lineup, and social links. Embed color matches your active theme accent.
- **Embed Image** — Attach a poster image to embeds by pasting a URL or browsing for a local file.
- **Channel Picker** — Fetches your server's text channels so you can post to Events, Popup, or Signups channels by name.
- **Scheduled Posting** — Schedule posts for future delivery with a date/time picker. Posts persist across app restarts.
- **`.env` Support** — Load bot credentials from a `.env` file for secure credential management.

### Social Links

- **Configurable Social Links** — Add links for Timeline, VRCPop, X (Twitter), Instagram, Discord, and VRC Group that appear at the bottom of lineup output and Discord embeds.
- **Persistent Links** — Mark Discord and VRC Group links as persistent so they carry across all events automatically.

### Multi-Format Output

Real-time previews for four output formats:

| Format | Style | Description |
| :---- | :---- | :---- |
| **Discord** | Markdown | `#` headers, `<t:UNIX:t>` timestamps, `**bold**` DJ names |
| **Local** | Plain Text | `HH:MM` times with local timezone abbreviation (PST, GMT, etc.) |
| **Quest** | HLS Links | `https://stream.vrcdn.live/live/{key}.live.ts` in a code block |
| **PC** | RTSP Links | `rtspt://stream.vrcdn.live/live/{key}` in a code block |

### Personalization & Reliability

- **Theme Engine** — 8 built-in dark presets (**Slate**, **Midnight Blue**, **OLED Black**, **Crimson**, **Amber**, **Forest**, **Ocean**, **Violet**) plus unlimited user-saved custom presets. All color/dimension tokens are defined in `theme.py`.
- **Crash Recovery** — Auto-save every 5 seconds to `auto_save.json`. On next launch, the app offers to restore the previous session.
- **Window Persistence** — Remembers size, position, and panel widths across sessions via `window_state.json`.
- **Windows Title Bar Coloring** — Dynamically colors the native title bar to match the active theme accent (Windows 10/11).
- **Resizable Panels** — The left/right panel split is user-adjustable with a drag handle persisted to `window_state.json`.

---

## Input Shortcuts

| Input | Action |
| :---- | :---- |
| **↑ / ↓** on timestamp field | Shift event time ±15 minutes |
| **Shift + ↑ / ↓** on timestamp field | Shift event time ±24 hours |
| **Mouse wheel** on combo / spinners | Cycle values up or down |

---

## Installation & Development

### Prerequisites

- **Python 3.11+**
- **Windows 10/11** (required for native title bar coloring; app runs on other platforms without it)

### Setup

```bash
git clone https://github.com/Baebu/lineup_builder.git
cd lineup_builder
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Run

```bash
python main.py      # production
python dev.py       # auto-restart on src/ file changes (uses watchdog)
```

On Windows you can also use `dev.bat` which activates the venv and launches `dev.py`.

### Test

```bash
pytest tests/ -v
```

The backend (models, output generator, event bus) is fully testable without a GUI — no DearPyGui imports in `src/backend/`.

### Build Executable

```bash
pip install pyinstaller
python -m PyInstaller lineup_builder.spec --clean
```

Output: `dist/LineupBuilder.exe`

---

## Architecture

Mixin-composition pattern built on **DearPyGui**. A single `App` class inherits **11 functional mixins**, keeping GUI code cleanly separated from business logic.

```
src/
├── backend/          # Pure Python — zero DearPyGui imports
│   ├── event_bus.py        EventBus pub/sub hub
│   ├── lineup_model.py     LineupModel + SlotData / DJInfo dataclasses
│   ├── output_generator.py Pure text generation (discord/local/quest/pc)
│   ├── output_builder.py   OutputMixin: bridges UI state → OutputGenerator
│   ├── data_manager.py     DataMixin: YAML/JSON file I/O
│   ├── debounce.py         DebounceMixin: timer helpers + frame work queue
│   ├── discord_service.py  DiscordService: bot lifecycle, channel fetch, embed posting
│   ├── discord_oauth.py    OAuth2 helpers (unused — bot-token auth preferred)
│   └── types.py            Shared dataclasses (EventSnapshot)
│
└── frontend/         # DearPyGui widgets — no business logic
    ├── app.py              App class composing all 11 mixins
    ├── ui_builder.py       UISetupMixin: full window/panel/widget layout
    ├── theme.py            Hex color constants + reusable style dicts
    ├── fonts.py            Icon class (Material Symbols), styled_text()
    ├── settings_manager.py SettingsMixin: settings.json + apply_theme()
    ├── slot_ui.py          DPGVar, DPGBoolVar, SlotState, build_slot_row()
    ├── slot_manager.py     SlotMixin: add/delete/reorder slots
    ├── roster.py           RosterMixin: roster CRUD + drag payloads
    ├── genre_manager.py    GenreMixin: genre tag management
    ├── events_manager.py   EventsMixin: save/load/delete event lineups
    ├── drag_drop.py        DragDropMixin: slot reordering + DJ drop targets
    ├── date_time_picker.py Calendar + time picker modal
    ├── import_parser.py    ImportMixin: Discord/plain-text import
    ├── widgets.py          Themed widget factory helpers
    └── utils.py            get_data_dir(), get_icon_path()
```

### State Flow

```
UI widgets
  → DPGVar / DPGBoolVar wrappers
  → debounced callback (_schedule_update / _schedule_save_library)
  → OutputMixin._build_snapshot()  →  EventSnapshot (immutable)
  → OutputGenerator.generate(snap) →  formatted string
  → dpg.set_value(preview_tag, text)
```

Cross-module communication uses `EventBus` pub/sub. `LineupModel` publishes `"model_changed"` on every setter; subscribers (output, roster, etc.) react accordingly.

### Backend Modules

| Module | Key Class / Function | Purpose |
| :---- | :---- | :---- |
| `event_bus.py` | `EventBus` | Lightweight pub/sub: `subscribe`, `publish`, `unsubscribe`, `clear` |
| `lineup_model.py` | `LineupModel`, `SlotData`, `DJInfo` | Mutable runtime state; every mutating setter fires `"model_changed"` |
| `output_generator.py` | `OutputGenerator` | `generate(snap)` → discord/local/quest/pc text; `compute_slot_times(snap)` |
| `output_builder.py` | `OutputMixin` | `_build_snapshot()` harvests widget state; `update_output()` drives preview |
| `data_manager.py` | `DataMixin` | Load/save YAML + JSON; crash-recovery auto-save; window state persistence |
| `debounce.py` | `DebounceMixin` | `_schedule_update()` (150 ms), `_schedule_save_library()` (500 ms), `_schedule_auto_save()` (5 s) |
| `discord_service.py` | `DiscordService` | Bot start/stop, `get_text_channels()`, `send_message()`, `send_embed()` |
| `types.py` | `EventSnapshot` | Frozen dataclass snapshot consumed by `OutputGenerator` |

### Frontend Modules

| Module | Key Class | Purpose |
| :---- | :---- | :---- |
| `app.py` | `App` | MRO root composing all 11 mixins; owns DPG lifecycle |
| `ui_builder.py` | `UISetupMixin` | Viewport, left/right panels, tabs, all widget construction |
| `theme.py` | — | `PANEL_BG`, `ACCENT`, `ENTRY`, `BTN_PRIMARY`, etc. + `hex_to_dpg()` |
| `fonts.py` | `Icon` | Material Symbols Rounded constants; `styled_text(label, style)` |
| `settings_manager.py` | `SettingsMixin` | `load_settings()`, `apply_theme()`, `apply_preset()`, `save_current_as_preset()` |
| `slot_ui.py` | `DPGVar`, `DPGBoolVar`, `SlotState` | Per-slot widget state; `build_slot_row()` creates the slot UI row |
| `slot_manager.py` | `SlotMixin` | `add_slot()`, `delete_slot()`, `move_slot()`, apply master duration |
| `roster.py` | `RosterMixin` | Roster display + CRUD; bulk link import; drag payload creation |
| `genre_manager.py` | `GenreMixin` | Genre tag add/delete/toggle; filtered genre lists |
| `events_manager.py` | `EventsMixin` | YAML-backed event save/load/delete/duplicate + confirmation dialogs |
| `drag_drop.py` | `DragDropMixin` | Slot reorder drag handles; DJ-card drop targets; "flash" highlight |
| `date_time_picker.py` | — | `open_datetime_picker()` modal: calendar grid + hour/minute spinners |
| `import_parser.py` | `ImportMixin` | `_parse_event_text()` for Discord markdown and plain-text formats |
| `widgets.py` | — | `add_icon_button()`, `add_primary_button()`, `add_danger_button()`, `add_styled_input()`, `add_styled_combo()` |
| `utils.py` | — | `get_data_dir()` (handles frozen exe), `get_icon_path()` (PNG→ICO) |

---

## Data Files

All files live in the application directory (resolved by `get_data_dir()` — the executable's directory when frozen, the project root during development):

| File | Format | Contents |
| :---- | :---- | :---- |
| `lineup_library.yaml` | YAML | DJ roster (`name`, `stream`, `exact_link`), genre library, saved titles |
| `lineup_events.yaml` | YAML | Saved event lineups (`title`, `vol`, `timestamp`, `slots`, `genres`, `created_at`) |
| `settings.json` | JSON | Theme colors, `ui_scale`, `user_presets` array |
| `window_state.json` | JSON | Window geometry (x, y, width, height) and panel widths |
| `auto_save.json` | JSON | Transient lineup state for crash recovery |
| `.env` | Env | Optional bot credentials (`DISCORD_BOT_TOKEN`, `DISCORD_CLIENT_ID`, `DISCORD_CLIENT_SECRET`) |

---

## Theme System

Themes are defined as dictionaries of hex color tokens in `settings_manager.py` and applied by `SettingsMixin.apply_theme()`, which builds a global DPG theme object covering 30+ color slots and rounded-corner styles.

### Built-in Presets

| Name | Description |
| :---- | :---- |
| **Slate (Default)** | Dark slate blue — the default palette |
| **Midnight Blue** | Deep midnight blue with blue accents |
| **OLED Black** | Near-pure-black backgrounds for OLED displays |
| **Crimson** | Deep red/rose tones |
| **Amber** | Warm amber/gold tones |
| **Forest** | Dark emerald green |
| **Ocean** | Deep teal/cyan |
| **Violet** | Rich purple |

User-defined custom presets can be saved at any time from the Settings tab and are stored in `settings.json` under `"user_presets"`.

### Color Tokens

The `DEFAULT_SETTINGS` dict defines these token keys (all hex strings):

`primary_color`, `primary_hover`, `secondary_color`, `secondary_hover`, `success_color`, `success_hover`, `danger_color`, `danger_hover`, `accent_color`, `panel_bg`, `card_bg`, `border_color`, `hover_color`, `scrollbar_color`, `text_primary`, `text_secondary`

---

## Output Formats

`OutputGenerator.generate(snapshot)` is a pure static method — no GUI, no side effects.

### Discord
```
# Event Title VOL.3
# <t:1234567890:F> (<t:1234567890:R>)
## House // Techno
### LINEUP
<t:1234567890:t> | **DJ Alpha** (House)
<t:1234567950:t> | **DJ Beta** (Techno)
```

### Local (Plain Text)
```
Event Title VOL.3
2025-06-01 @ 20:00 (PST)
House // Techno
LINEUP
20:00 | DJ Alpha (House)
20:30 | DJ Beta (Techno)
```

### Quest / PC (Stream Links)
```
https://stream.vrcdn.live/live/{key}.live.ts   ← Quest (HLS)
rtspt://stream.vrcdn.live/live/{key}           ← PC (RTSP)
```

VRCDN stream keys are automatically extracted and reformatted for the target platform. Non-VRCDN links (Twitch, YouTube, Kick, etc.) are passed through unchanged when **"Use exact link"** is enabled on the DJ’s roster entry.

### Supported Stream Platforms

| Platform | Example Link | Notes |
| :---- | :---- | :---- |
| **VRCDN** | `https://stream.vrcdn.live/live/{key}` | Auto-converted between Quest (HLS) and PC (RTSP) formats |
| **Twitch** | `https://twitch.tv/username` | Use "exact link" mode — passed through as-is |
| **YouTube** | `https://youtube.com/watch?v=...` | Use "exact link" mode |
| **Kick** | `https://kick.com/username` | Use "exact link" mode |

---

## License

This project is licensed under the MIT License.