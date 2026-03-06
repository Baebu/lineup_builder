# Lineup Builder — Copilot Instructions

## Architecture

Mixin-composition desktop app. A single `App` class (`src/frontend/app.py`) inherits **11 functional mixins**:

| # | Mixin | File | Responsibility |
|---|-------|------|----------------|
| 1 | `UISetupMixin` | `src/frontend/ui_builder.py` | DPG viewport, left/right panels, all widget construction, scroll/arrow-key handlers |
| 2 | `RosterMixin` | `src/frontend/roster.py` | DJ roster CRUD, bulk link import, drag payload creation |
| 3 | `DragDropMixin` | `src/frontend/drag_drop.py` | Slot reordering, DJ-card→slot drop targets, flash highlight |
| 4 | `EventsMixin` | `src/frontend/events_manager.py` | Save/load/delete/duplicate event lineups (YAML-backed) |
| 5 | `GenreMixin` | `src/frontend/genre_manager.py` | Genre tag add/delete/toggle, active-genre filtering |
| 6 | `SlotMixin` | `src/frontend/slot_manager.py` | Slot CRUD, reorder, apply master duration |
| 7 | `OutputMixin` | `src/backend/output_builder.py` | `_build_snapshot()` → `EventSnapshot`; `update_output()` drives preview |
| 8 | `DataMixin` | `src/backend/data_manager.py` | YAML/JSON I/O, window geometry persistence, crash-recovery auto-save |
| 9 | `SettingsMixin` | `src/frontend/settings_manager.py` | `load_settings()`, `apply_theme()`, preset management |
| 10 | `DebounceMixin` | `src/backend/debounce.py` | Timer helpers + per-frame work queue (`process_queue()`) |
| 11 | `ImportMixin` | `src/frontend/import_parser.py` | `_parse_event_text()` for Discord markdown and plain-text formats |

> **Rule:** `src/backend/` is **100% GUI-free** (no DearPyGui imports). Tests run against backend only.

| Layer | Location | Rule |
|-------|----------|------|
| Backend | `src/backend/` | Pure Python — **no DearPyGui imports** |
| Frontend | `src/frontend/` | DearPyGui widgets, themes, fonts |
| Tests | `tests/` | pytest, backend-only |

---

## State Flow

```
UI widgets
  → DPGVar / DPGBoolVar wrappers (src/frontend/slot_ui.py)
  → debounced callback (_schedule_update / _schedule_save_library)
  → OutputMixin._build_snapshot()   →   EventSnapshot (frozen dataclass)
  → OutputGenerator.generate(snap)  →   formatted string
  → dpg.set_value(preview_tag, text)
```

Cross-module events use `EventBus` pub/sub (`src/backend/event_bus.py`).  
`LineupModel` publishes `"model_changed"` on every state mutation.

---

## GUI Framework

**DearPyGui** (`import dearpygui.dearpygui as dpg`) — **NOT CustomTkinter**.

- Widgets use tag-based identity: `dpg.add_input_text(tag="event_title_input")`
- Read/write state: `dpg.get_value(tag)` / `dpg.set_value(tag, value)`
- State wrappers: `DPGVar` / `DPGBoolVar` (defined in `src/frontend/slot_ui.py`) replace `tk.StringVar` / `tk.BooleanVar`
- `SlotState` (also in `slot_ui.py`) holds `name_var`, `genre_var`, `duration_var` per slot plus `row_tag` and `_id`
- Main loop: `while dpg.is_dearpygui_running(): process_queue(); dpg.render_dearpygui_frame()`
- All popup/modal windows inherit the **global theme** — **never** override with per-window themes
- Viewport default: 1050×768, minimum 800×600

---

## Theme & Styling

- **Color tokens:** `src/frontend/theme.py` — hex string constants (`PANEL_BG`, `ACCENT`, etc.) + `hex_to_dpg()` converter + reusable style dicts (`ENTRY`, `COMBO`, `BTN_PRIMARY`, `BTN_DANGER`, `CARD`, etc.)
- **Global theme:** Built dynamically in `SettingsMixin.apply_theme()` from `self.settings` color tokens. Maps 30+ DPG color slots + rounded-corner styles. Bound globally with `dpg.bind_theme(global_theme)`.
- **Built-in presets** (8 total, in `BUILTIN_PRESETS` list in `settings_manager.py`):
  - **Slate (Default)** — Dark slate blue
  - **Midnight Blue** — Deep midnight blue with blue accents
  - **OLED Black** — Near-pure-black for OLED displays
  - **Crimson** — Deep red/rose tones
  - **Amber** — Warm amber/gold tones
  - **Forest** — Dark emerald green
  - **Ocean** — Deep teal/cyan
  - **Violet** — Rich purple
- **User presets:** Saved to `settings.json` under `"user_presets"` array; managed via `save_current_as_preset()` / `delete_preset()`
- **Fonts/icons:** `src/frontend/fonts.py` — `styled_text(label, style)` helper, `Icon` class (Material Symbols Rounded). Text styles: `HEADER`, `LABEL`, `BODY`, `MUTED`, `ERROR`, `SUCCESS`, `HINT`
- **Widget factory:** `src/frontend/widgets.py` — `add_icon_button()`, `add_primary_button()`, `add_danger_button()`, `add_styled_input()`, `add_styled_combo()` — all apply correct theme automatically

---

## Debounce Timings

All mutations must go through `DebounceMixin` helpers — **never call `update_output()` or `_save_library()` directly from a callback**.

| Method | Delay | Purpose |
|--------|-------|---------|
| `_schedule_update()` | 150 ms | Refresh output preview after input changes |
| `_schedule_roster_refresh()` | 120 ms | Redraw DJ roster panel |
| `_schedule_genre_refresh()` | 120 ms | Redraw genre tags |
| `_schedule_save_library()` | 500 ms | Persist DJ/genre library to YAML |
| `_schedule_auto_save()` | 5 000 ms | Write crash-recovery state to `auto_save.json` |
| `_schedule_auto_event_save()` | 1 500 ms | Write current event snapshot to `auto_save.json` |

`process_queue()` is called every DPG frame and drains the `self._work_queue` (SimpleQueue) for thread-safe main-thread execution.

---

## Output Generation

`OutputGenerator` (`src/backend/output_generator.py`) is **pure** — no GUI imports, no side effects.

```python
# Entry point
OutputGenerator.generate(snapshot: EventSnapshot) -> str

# Helpers
OutputGenerator.compute_slot_times(snapshot) -> list[str]   # ["20:00", "20:30", ...]
OutputGenerator.vrcdn_convert(link: str, fmt: str) -> str   # "quest" | "pc"
```

Supported `output_format` values on `EventSnapshot`: `"discord"` | `"local"` | `"quest"` | `"pc"`

`EventSnapshot` is a frozen dataclass with: `title`, `vol`, `timestamp`, `genres`, `slots` (`list[SlotData]`), `names_only`, `output_format`, `saved_djs` (`list[DJInfo]`). Computed properties: `start_datetime`, `full_title`.

---

## Conventions

- **Popup windows:** `modal=True`, `autosize=True`, `no_resize=True`, `no_scrollbar=True`. They inherit the global theme automatically. Examples: `save_warn_win`, `overwrite_confirm_win`, `dj_edit_win_{idx}`, `dt_picker_modal`, `import_dialog_win`.
- **File I/O:** YAML for events/library (`lineup_events.yaml`, `lineup_library.yaml`), JSON for settings/state (`settings.json`, `window_state.json`, `auto_save.json`). All paths via `get_data_dir()` from `src/frontend/utils.py`.
- **Thread safety:** Long-running work goes through `self._work_queue` (SimpleQueue), drained each frame by `process_queue()`.
- **Output generation is pure:** `OutputGenerator.generate(snapshot)` takes an immutable `EventSnapshot` and returns a string. No side effects.
- **Tag naming:** Widget tags use snake_case strings, e.g. `"event_title_input"`, `"slot_row_{id}"`, `"dj_card_{idx}"`.
- **`get_data_dir()`:** Returns `sys.executable`'s directory when frozen by PyInstaller, project root otherwise.

---

## Build & Test

```bash
# Setup
python -m venv .venv && .venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Run
python main.py          # production
python dev.py           # auto-restart on src/ file changes (watchdog)

# Test
pytest tests/ -v

# Build exe
pip install pyinstaller
python -m PyInstaller lineup_builder.spec --clean
```

---

## Code Style

- Linter: **Ruff** (E, F, W, I rules; `line-length = 100`; E501 ignored)
- Python 3.11+ (type unions with `|`, f-strings, `match` statements allowed)
- No type annotations required on existing code unless adding new public APIs
- `pyproject.toml` is the single source for tool config (Ruff, pytest)