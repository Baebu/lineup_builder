# Lineup Builder — Desktop App

Desktop GUI application for DJs and event organizers. Streamlines scheduling sets, managing performer rosters, and generating formatted output for Discord, plain text, and VRCDN-based VR platforms (Quest/PC).

Built on **DearPyGui** with a mixin-composition architecture — the entire backend is pure Python and fully unit-testable with no GUI dependency.

---

## Screenshots

![Screenshot 1](../assets/Screenshots/Screenshot%202026-03-07%20025936.png)
![Screenshot 2](../assets/Screenshots/Screenshot%202026-03-07%20025953.png)
![Screenshot 3](../assets/Screenshots/Screenshot%202026-03-07%20030001.png)
![Screenshot 4](../assets/Screenshots/Screenshot%202026-03-07%20030012.png)

---

## Features

### Event Orchestration

- **Smart Header** — Set event titles and volume numbers. Volume auto-increments when you save a new event.
- **Integrated Date/Time Picker** — Custom-styled calendar and time selector (modal pop-up). Use **Arrow Up / Arrow Down** on the timestamp field to shift time ±15 minutes; hold **Shift** for ±24 hours.
- **Automated Import** — Paste an existing lineup from Discord or plain text. The parser extracts titles, timestamps, genres, and DJ slots automatically.
- **Genre Library** — Persistent global genre list. Toggle genres on/off per event or add new tags on the fly.

### DJ Roster & Lineup Management

- **Persistent Roster** — Store frequent performers alongside their stream links (VRCDN, Twitch, YouTube, SoundCloud, Kick, or any custom URL).
- **Exact Link Mode** — Per-DJ toggle to skip VRCDN conversion and pass the stream URL through as-is.
- **Drag-and-Drop** — Drag DJs directly from your roster into a lineup slot.
- **Slot Reordering** — Reorder slots using drag handles. Start times recalculate in real-time as durations change.
- **Open Decks** — Configurable open-deck slots with adjustable counts and durations.
- **Events History** — Save, restore, duplicate, and delete past event lineups from a persistent YAML-backed library.

### Discord Bot Integration

- **Built-in Discord Bot** — Connect a Discord bot directly from the app.
- **Rich Embed Posting** — Lineups posted as styled Discord embeds with event title, timestamps, genre tags, full lineup, and social links. Embed color matches your active theme accent.
- **Embed Image** — Attach a poster image by URL or local file.
- **Channel Picker** — Fetches your server's text channels for posting.
- **Scheduled Posting** — Schedule posts for future delivery. Posts persist across app restarts.

### Social Links

- **Configurable Social Links** — Timeline, VRCPop, X (Twitter), Instagram, Discord, and VRC Group links appear at the bottom of lineup output and Discord embeds.
- **Persistent Links** — Mark Discord and VRC Group links as persistent so they carry across all events.

### Multi-Format Output

Real-time previews for four output formats:

| Format | Style | Description |
|--------|-------|-------------|
| **Discord** | Markdown | `#` headers, `<t:UNIX:t>` timestamps, `**bold**` DJ names |
| **Local** | Plain Text | `HH:MM` times with local timezone abbreviation |
| **Quest** | HLS Links | `https://stream.vrcdn.live/live/{key}.live.ts` in a code block |
| **PC** | RTSP Links | `rtspt://stream.vrcdn.live/live/{key}` in a code block |

### Personalization & Reliability

- **Theme Engine** — 8 built-in dark presets (Slate, Midnight Blue, OLED Black, Crimson, Amber, Forest, Ocean, Violet) plus unlimited user-saved custom presets.
- **Crash Recovery** — Auto-save every 5 seconds. On next launch, the app offers to restore the previous session.
- **Window Persistence** — Remembers size, position, and panel widths across sessions.
- **Windows Title Bar Coloring** — Dynamically colors the native title bar to match the active theme (Windows 10/11).
- **Resizable Panels** — Left/right panel split is user-adjustable with a drag handle.

---

## Input Shortcuts

| Input | Action |
|-------|--------|
| **↑ / ↓** on timestamp field | Shift event time ±15 minutes |
| **Shift + ↑ / ↓** on timestamp field | Shift event time ±24 hours |
| **Mouse wheel** on combo / spinners | Cycle values up or down |

---

## Setup

### Prerequisites

- **Python 3.11+**
- **Windows 10/11** (required for native title bar coloring; runs on other platforms without it)

### Install

```bash
cd desktop
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Run

```bash
# From the project root
python main.py          # production
python dev.py           # auto-restart on code changes (watchdog)
```

On Windows you can also use `dev.bat` which activates the venv and launches `dev.py`.

### Test

```bash
pytest tests/ -v
```

The backend is fully testable without a GUI — no DearPyGui imports in `src/backend/`.

### Build Executable

```bash
pip install pyinstaller
python -m PyInstaller lineup_builder.spec --clean
```

Output: `dist/LineupBuilder.exe`

---

## Architecture

Mixin-composition pattern. A single `App` class inherits **11 functional mixins**, keeping GUI code cleanly separated from business logic.

```
desktop/src/
├── backend/              # Pure Python — zero DearPyGui imports
│   ├── api_client.py           REST client for the server API
│   ├── data_manager.py         DataMixin: YAML/JSON file I/O
│   ├── debounce.py             DebounceMixin: timer helpers + frame work queue
│   ├── discord_oauth.py        OAuth2 local callback server
│   ├── discord_service.py      DiscordService: bot lifecycle, embed posting
│   ├── event_bus.py            EventBus pub/sub hub
│   ├── lineup_model.py         LineupModel + SlotData / DJInfo dataclasses
│   ├── output_builder.py       OutputMixin: bridges UI state → OutputGenerator
│   ├── output_generator.py     Pure text generation (discord/local/quest/pc)
│   └── types.py                Shared dataclasses (EventSnapshot)
│
└── frontend/             # DearPyGui widgets — no business logic
    ├── app.py                  App class composing all 11 mixins; owns DPG lifecycle
    ├── ui_builder.py           UISetupMixin: full window/panel/widget layout
    ├── theme.py                Hex color constants + reusable style dicts
    ├── fonts.py                Icon class (Material Symbols), styled_text()
    ├── settings_manager.py     SettingsMixin: settings.json + apply_theme()
    ├── slot_ui.py              DPGVar, DPGBoolVar, SlotState, build_slot_row()
    ├── slot_manager.py         SlotMixin: add/delete/reorder slots
    ├── roster.py               RosterMixin: roster CRUD + drag payloads
    ├── genre_manager.py        GenreMixin: genre tag management
    ├── events_manager.py       EventsMixin: save/load/delete event lineups
    ├── drag_drop.py            DragDropMixin: slot reordering + DJ drop targets
    ├── date_time_picker.py     Calendar + time picker modal
    ├── import_parser.py        ImportMixin: Discord/plain-text import
    ├── widgets.py              Themed widget factory helpers
    └── utils.py                get_data_dir(), get_icon_path()
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

Cross-module communication uses `EventBus` pub/sub. `LineupModel` publishes `"model_changed"` on every setter.

### Debounce Timings

| Method | Delay | Purpose |
|--------|-------|---------|
| `_schedule_update()` | 150 ms | Refresh output preview |
| `_schedule_roster_refresh()` | 120 ms | Redraw DJ roster panel |
| `_schedule_genre_refresh()` | 120 ms | Redraw genre tags |
| `_schedule_save_library()` | 500 ms | Persist DJ/genre library to YAML |
| `_schedule_auto_save()` | 5 000 ms | Write crash-recovery state |
| `_schedule_auto_event_save()` | 1 500 ms | Write current event snapshot |

---

## Data Files

All files live in the application directory (resolved by `get_data_dir()` — the executable's directory when frozen, the project root during development):

| File | Format | Contents |
|------|--------|----------|
| `lineup_library.yaml` | YAML | DJ roster, genre library, saved titles |
| `lineup_events.yaml` | YAML | Saved event lineups |
| `settings.json` | JSON | Theme colors, UI scale, user presets |
| `window_state.json` | JSON | Window geometry and panel widths |
| `auto_save.json` | JSON | Transient lineup state for crash recovery |

---

## Theme System

Themes are defined as dictionaries of hex color tokens and applied by `SettingsMixin.apply_theme()`, which builds a global DPG theme covering 30+ color slots and rounded-corner styles.

### Built-in Presets

| Name | Description |
|------|-------------|
| **Slate** (Default) | Dark slate blue |
| **Midnight Blue** | Deep midnight blue with blue accents |
| **OLED Black** | Near-pure-black for OLED displays |
| **Crimson** | Deep red/rose tones |
| **Amber** | Warm amber/gold tones |
| **Forest** | Dark emerald green |
| **Ocean** | Deep teal/cyan |
| **Violet** | Rich purple |

### Color Tokens

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
