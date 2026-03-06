# Lineup Builder

**Lineup Builder** is a desktop GUI application for DJs and event organizers. It streamlines scheduling sets, managing performer rosters, and generating perfectly formatted output for Discord, plain text, and VRCDN-based VR platforms (Quest/PC).

Built on **DearPyGui** with a mixin-composition architecture — the entire backend is pure Python and fully unit-testable with no GUI dependency.

---

## Features

### Event Orchestration

- **Smart Header** — Set event titles and volume numbers. Volume auto-increments when you save a new event.
- **Integrated Date/Time Picker** — A custom-styled calendar and time selector (modal pop-up) for precise start times. Use **Arrow Up / Arrow Down** on the timestamp field to shift the time by ±15 minutes; hold **Shift** for ±24 hours.
- **Automated Import** — Paste an existing lineup from Discord or plain text. The parser extracts titles, timestamps, genres, and DJ slots, populating the editor in seconds.
- **Genre Library** — Persistent global genre list. Toggle genres on/off per event or add new tags on the fly.

### DJ Roster & Lineup Management

- **Persistent Roster** — Store frequent performers alongside their VRCDN stream links.
- **Drag-and-Drop** — Drag DJs directly from your roster into a lineup slot.
- **Slot Reordering** — Reorder slots using drag handles. Start times recalculate in real-time as durations change.
- **Open Decks** — A dedicated configurable section for open-deck slots with adjustable counts and durations.
- **Events History** — Save, restore, duplicate, and delete past event lineups from a persistent YAML-backed library.

### Multi-Format Output

Real-time previews for four output formats:

| Format | Style | Description |
| :---- | :---- | :---- |
| **Discord** | Markdown | `#` headers, `<t:UNIX:t>` timestamps, `**bold**` DJ names |
| **Local** | Plain Text | `HH:MM` times with local timezone abbreviation (PST, GMT, etc.) |
| **Quest** | HLS Links | `https://stream.vrcdn.live/live/{key}.live.ts` in a code block |
| **PC** | RTSP Links | `rtspt://stream.vrcdn.live/live/{key}` in a code block |

### Personalization & Reliability

- **Theme Engine** — 3 built-in dark presets (**Slate**, **Midnight**, **OLED Black**) plus unlimited user-saved custom presets. All color/dimension tokens are defined in `theme.py`.
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
    ├── dj_roster.py        DJRosterMixin: roster CRUD + drag payloads
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
| `dj_roster.py` | `DJRosterMixin` | Roster display + CRUD; bulk link import; drag payload creation |
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

---

## Theme System

Themes are defined as dictionaries of hex color tokens in `settings_manager.py` and applied by `SettingsMixin.apply_theme()`, which builds a global DPG theme object covering 30+ color slots and rounded-corner styles.

### Built-in Presets

| Name | Description |
| :---- | :---- |
| **Slate (Default)** | Dark slate blue — the default palette |
| **Midnight** | Deep midnight blue, deeper contrast than Slate |
| **OLED Black** | Near-pure-black backgrounds for OLED displays |

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

---

## License

This project is licensed under the MIT License.