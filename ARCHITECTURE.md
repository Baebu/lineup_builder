# Lineup Builder — Architecture Document

> **Last updated:** 2026-03-03
> **Runtime:** Python 3.x + CustomTkinter (dark-mode desktop GUI)
> **Purpose:** Build DJ event lineups and generate formatted text output for Discord, plain text, or stream-link views.

---

## Table of Contents

1. [High-Level Overview](#1-high-level-overview)
2. [Directory & File Map](#2-directory--file-map)
3. [Dependency Graph](#3-dependency-graph)
4. [Application Bootstrap Sequence](#4-application-bootstrap-sequence)
5. [Class Architecture (Mixin Composition)](#5-class-architecture-mixin-composition)
6. [Module-by-Module Reference](#6-module-by-module-reference)
   - [main.py](#mainpy)
   - [app.py — App class](#apppy--app-class)
   - [ui_builder.py — UISetupMixin](#ui_builderpy--uisetupmixin)
   - [slot_ui.py — SlotUI](#slot_uipy--slotui)
   - [slot_manager.py — SlotMixin](#slot_managerpy--slotmixin)
   - [output_builder.py — OutputMixin](#output_builderpy--outputmixin)
   - [dj_roster.py — DJRosterMixin](#dj_rosterpy--djrostermixin)
   - [drag_drop.py — DragDropMixin](#drag_droppy--dragdropmixin)
   - [events_manager.py — EventsMixin](#events_managerpy--eventsmixin)
   - [genre_manager.py — GenreMixin](#genre_managerpy--genremixin)
   - [data_manager.py — DataMixin](#data_managerpy--datamixin)
   - [settings_manager.py — SettingsMixin](#settings_managerpy--settingsmixin)
   - [debounce.py — DebounceMixin](#debouncepy--debouncemixin)
   - [date_time_picker.py — CTkDateTimePicker](#date_time_pickerpy--ctkdatetimepicker)
   - [utils.py](#utilspy)
7. [Data Model & Persistence](#7-data-model--persistence)
8. [State Management](#8-state-management)
9. [Reactive Update Pipeline](#9-reactive-update-pipeline)
10. [UI Layout Map](#10-ui-layout-map)
11. [Drag-and-Drop System](#11-drag-and-drop-system)
12. [Theming & Color System](#12-theming--color-system)
13. [Output Rendering Engine](#13-output-rendering-engine)
14. [Keyboard Shortcuts](#14-keyboard-shortcuts)
15. [Auto-Save & Crash Recovery](#15-auto-save--crash-recovery)
16. [External Dependencies](#16-external-dependencies)

---

## 1. High-Level Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                          main.py                                │
│                     App().mainloop()                            │
└───────────────────────────┬─────────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────────┐
│                       App (ctk.CTk)                             │
│  Composed from 10 mixins via cooperative multiple inheritance   │
│                                                                 │
│  ┌────────────┐ ┌────────────┐ ┌─────────────┐ ┌────────────┐  │
│  │ UISetup    │ │ DJRoster   │ │ DragDrop    │ │ Events     │  │
│  │ Mixin      │ │ Mixin      │ │ Mixin       │ │ Mixin      │  │
│  ├────────────┤ ├────────────┤ ├─────────────┤ ├────────────┤  │
│  │ Genre      │ │ Slot       │ │ Output      │ │ Data       │  │
│  │ Mixin      │ │ Mixin      │ │ Mixin       │ │ Mixin      │  │
│  ├────────────┤ ├────────────┤                                  │
│  │ Settings   │ │ Debounce   │                                  │
│  │ Mixin      │ │ Mixin      │                                  │
│  └────────────┘ └────────────┘                                  │
│                                                                 │
│  Standalone widgets:                                            │
│    SlotUI (ctk.CTkFrame) — one per lineup performer slot        │
│    CTkDateTimePicker (ctk.CTkFrame) — date/time input widget    │
└─────────────────────────────────────────────────────────────────┘
                            │
            ┌───────────────┼───────────────┐
            ▼               ▼               ▼
   lineup_library.yaml  lineup_events.yaml  settings.json
   (DJs, titles,        (saved events)      (theme colors,
    genres)                                  font size)
```

The application is a single-window CustomTkinter desktop app structured as a **mixin-composed monolith**: one `App` class inherits from 10 specialized mixins plus `ctk.CTk`. Each mixin owns a distinct functional domain (UI layout, DJ roster, drag-and-drop, etc.) but they all operate on the same shared `self` instance — the `App`.

---

## 2. Directory & File Map

```
lineup_builder/                 ← Project root (CWD at runtime)
│
├── main.py                     ← Entry point: instantiates App, runs mainloop
├── requirements.txt            ← pip dependencies
├── lineup_builder.spec         ← PyInstaller build spec
├── settings.json               ← Runtime: user settings (theme, font size)
├── window_state.json           ← Runtime: window geometry persistence
├── auto_save.json              ← Runtime: crash-recovery session state
├── lineup_library.yaml         ← Runtime: saved titles, DJs, genres
├── lineup_events.yaml          ← Runtime: saved event lineups
├── lineup_data.yaml            ← Legacy seed data (fallback if no runtime files)
│
├── lineup_builder/             ← Python package (all app code)
│   ├── __init__.py             ← Package exports
│   ├── app.py                  ← App class definition (mixin composition + __init__)
│   ├── ui_builder.py           ← UISetupMixin — full UI layout construction
│   ├── slot_ui.py              ← SlotUI widget — single performer slot row
│   ├── slot_manager.py         ← SlotMixin — add/remove/reorder/duplicate slots
│   ├── output_builder.py       ← OutputMixin — text output generation + format switching
│   ├── dj_roster.py            ← DJRosterMixin — DJ Roster tab: CRUD cards, search
│   ├── drag_drop.py            ← DragDropMixin — slot reorder + DJ→lineup drag & drop
│   ├── events_manager.py       ← EventsMixin — save/load/delete/duplicate events
│   ├── genre_manager.py        ← GenreMixin — genre tags, genre editor popup
│   ├── data_manager.py         ← DataMixin — YAML/JSON I/O, auto-save, window state
│   ├── settings_manager.py     ← SettingsMixin — Settings tab, theme engine, presets
│   ├── debounce.py             ← DebounceMixin — coalescing timers for updates/saves
│   ├── date_time_picker.py     ← CTkDateTimePicker — reusable date/time input widget
│   └── utils.py                ← _make_icon() helper
│
├── build/                      ← PyInstaller build artifacts
└── __pycache__/
```

### File Roles

| File | Lines | Role |
|------|-------|------|
| `main.py` | 6 | Entry point only |
| `app.py` | ~111 | Central class definition + initialization |
| `ui_builder.py` | ~411 | Largest file — builds entire UI layout |
| `settings_manager.py` | ~431 | Theming engine, presets, Settings tab UI |
| `dj_roster.py` | ~260 | DJ Roster tab management |
| `genre_manager.py` | ~247 | Genre system (tags, editor popup) |
| `output_builder.py` | ~223 | Output text generation for all 4 formats |
| `events_manager.py` | ~172 | Saved Events CRUD + UI |
| `data_manager.py` | ~186 | All file I/O (YAML, JSON, auto-save, window state) |
| `slot_ui.py` | ~130 | Individual slot widget |
| `slot_manager.py` | ~70 | Slot list management |
| `drag_drop.py` | ~130 | Drag-and-drop engine |
| `debounce.py` | ~53 | Debounce timers |
| `date_time_picker.py` | ~250 | Standalone date/time picker widget |
| `utils.py` | ~8 | Icon generation utility |

---

## 3. Dependency Graph

### Internal Module Dependencies

```
main.py
  └── lineup_builder.app.App

app.py
  ├── utils._make_icon
  ├── data_manager.DataMixin
  ├── debounce.DebounceMixin
  ├── ui_builder.UISetupMixin
  │     └── date_time_picker.CTkDateTimePicker
  ├── dj_roster.DJRosterMixin
  ├── drag_drop.DragDropMixin
  ├── events_manager.EventsMixin
  ├── genre_manager.GenreMixin
  ├── slot_manager.SlotMixin
  │     └── slot_ui.SlotUI
  ├── output_builder.OutputMixin
  └── settings_manager.SettingsMixin
```

### Cross-Mixin Method Calls (shared `self`)

Every mixin freely accesses attributes and methods defined by other mixins, since they all share the same `self`. Key cross-boundary calls:

| Caller | Calls | Purpose |
|--------|-------|---------|
| `SlotUI` | `app_ref._schedule_update()` | Trigger debounced output rebuild |
| `SlotUI` | `app_ref._slot_drag_start/motion/end()` | Delegate drag events to DragDropMixin |
| `SlotUI` | `app_ref.update_output()` | Direct output refresh on combo selection |
| `DJRosterMixin` | `self._save_library()` | Persist DJ changes via DataMixin |
| `DJRosterMixin` | `self._refresh_slot_combos()` | Update slot dropdowns via DebounceMixin |
| `DJRosterMixin` | `self._on_dj_drag()` | Invoke DragDropMixin from roster cards |
| `EventsMixin` | `self.add_slot()` | Create slots via SlotMixin when loading events |
| `EventsMixin` | `self.refresh_genre_tags()` | Rebuild genre UI via GenreMixin |
| `GenreMixin` | `self._save_library()` | Persist genre changes via DataMixin |
| `DebounceMixin` | `self.update_output()` | Fire OutputMixin after debounce |
| `DebounceMixin` | `self._save_auto_state()` | Fire DataMixin auto-save after output update |
| `SettingsMixin` | `self.apply_theme()` | Walk all widgets to recolor |
| `OutputMixin` | `slot.time_lbl.configure()` | Update SlotUI time labels |

---

## 4. Application Bootstrap Sequence

```
main.py
  │
  ├─ 1. App.__init__()
  │     ├─ ctk.CTk.__init__()           # Create root Tk window
  │     ├─ self.title("Lineup Builder")
  │     ├─ self.geometry("1150x850")
  │     ├─ self._restore_window_state()  # DataMixin: load window_state.json
  │     ├─ ctk.set_appearance_mode("dark")
  │     ├─ Configure 2-column grid layout
  │     │
  │     ├─ Create 14 icon CTkImages via iconipy IconFactory
  │     │
  │     ├─ self.load_data()              # DataMixin: load YAML files
  │     │     ├─ Read lineup_library.yaml → saved_titles, saved_djs, saved_genres
  │     │     ├─ Migrate legacy DJ formats (plain strings, goggles/link fields)
  │     │     └─ Read lineup_events.yaml → saved_events (sorted by created_at DESC)
  │     │
  │     ├─ self.load_settings()          # SettingsMixin: load settings.json
  │     │     ├─ Apply DEFAULT_SETTINGS as base
  │     │     ├─ Overlay saved user settings
  │     │     └─ Initialize theme-tracking lists (_accent_labels, etc.)
  │     │
  │     ├─ Initialize all ctk.StringVar / BooleanVar state variables
  │     ├─ Initialize drag-drop state (ghost refs, drop indicator)
  │     ├─ Initialize debounce job IDs (all None)
  │     │
  │     ├─ self.setup_ui()               # UISetupMixin: build entire UI tree
  │     │     ├─ Left panel: CTkTabview ("Event", "DJ Roster", "Settings")
  │     │     │     ├─ Event tab: title, timestamp, genres, saved events
  │     │     │     ├─ DJ Roster tab: search bar, scrollable DJ card list
  │     │     │     └─ Settings tab: built via _build_settings_tab()
  │     │     ├─ Right top: Lineup panel (slots container + Open Decks row)
  │     │     ├─ Right bottom: Output preview (format buttons + textbox)
  │     │     └─ self.apply_theme()      # SettingsMixin: paint all colors
  │     │
  │     ├─ self.add_initial_slots()      # SlotMixin: create one empty slot
  │     ├─ self.update_output()          # OutputMixin: initial render
  │     ├─ self.protocol("WM_DELETE_WINDOW", self._on_close)
  │     │
  │     ├─ Bind keyboard shortcuts (Ctrl+S, Ctrl+D, Esc)
  │     └─ self.after(150, self._check_auto_save)  # Deferred crash recovery check
  │
  └─ 2. app.mainloop()                  # Enter Tk event loop
```

---

## 5. Class Architecture (Mixin Composition)

### MRO (Method Resolution Order)

```python
class App(
    UISetupMixin,       # 1st — UI construction
    DJRosterMixin,      # 2nd — DJ Roster tab
    DragDropMixin,      # 3rd — Drag-and-drop engine
    EventsMixin,        # 4th — Event save/load/delete
    GenreMixin,         # 5th — Genre tag system
    SlotMixin,          # 6th — Slot list management
    OutputMixin,        # 7th — Output text generation
    DataMixin,          # 8th — File I/O
    SettingsMixin,      # 9th — Settings & theming
    DebounceMixin,      # 10th — Debounce timers
    ctk.CTk,            # Base — CustomTkinter root window
):
```

### Why Mixins?

The app has ~2,500 lines of combined logic. Putting it all in one class would be unwieldy. The mixin pattern:
- **Separates concerns** — each file owns one domain
- **Avoids redundant `self.app` references** — all mixins share `self` (the App instance)
- **No inter-mixin import dependencies** — each mixin is a standalone class that assumes its methods will be mixed into something with the right attributes
- **Enables file-level code organization** while keeping a single runtime object

### Standalone Widget Classes

| Class | Base | Location | Purpose |
|-------|------|----------|---------|
| `SlotUI` | `ctk.CTkFrame` | `slot_ui.py` | Represents one performer slot in the lineup |
| `CTkDateTimePicker` | `ctk.CTkFrame` | `date_time_picker.py` | Reusable date/time input with calendar popup |

Both are instantiated as children of the App's widget tree but maintain a back-reference to `App` (via `app_ref` for `SlotUI`, or `variable` binding for `CTkDateTimePicker`).

---

## 6. Module-by-Module Reference

### main.py

```python
from lineup_builder.app import App
if __name__ == '__main__':
    app = App()
    app.mainloop()
```

Single entry point. No conditional logic—just instantiate and run.

---

### app.py — App class

**Role:** Central composition hub. Defines the App class through multiple inheritance, initializes all shared state, icons, data, and kicks off the UI build.

**Constants:**
| Constant | Value | Purpose |
|----------|-------|---------|
| `LIBRARY_FILE` | `"lineup_library.yaml"` | DJ/title/genre storage |
| `EVENTS_FILE` | `"lineup_events.yaml"` | Saved event lineups |
| `WINDOW_STATE_FILE` | `"window_state.json"` | Window geometry persistence |
| `AUTO_SAVE_FILE` | `"auto_save.json"` | Crash recovery state |

**State initialized in `__init__`:**

| Attribute | Type | Default | Purpose |
|-----------|------|---------|---------|
| `event_timestamp` | `StringVar` | `"YYYY-MM-DD 20:00"` | Event start datetime |
| `event_title_var` | `StringVar` | `""` | Event title |
| `event_vol_var` | `StringVar` | `""` | Volume number |
| `master_duration` | `StringVar` | `"60"` | Default slot duration |
| `active_genres` | `list[str]` | `[]` | Currently selected genres |
| `genre_entry_var` | `StringVar` | `""` | Genre input field |
| `genre_dropdown_var` | `StringVar` | `""` | Genre dropdown |
| `names_only` | `BooleanVar` | `False` | Output: names-only mode |
| `output_format` | `StringVar` | `"discord"` | Active output format |
| `include_od` | `BooleanVar` | `False` | Include Open Decks |
| `od_duration` | `StringVar` | `"30"` | Open Decks slot length |
| `od_count` | `StringVar` | `"4"` | Number of OD slots |
| `slots` | `list[SlotUI]` | `[]` | Active slot widget list |
| `_drag_ghost` | `CTkFrame\|None` | `None` | DJ roster drag ghost |
| `_slot_ghost` | `CTkFrame\|None` | `None` | Slot reorder drag ghost |
| `_drop_indicator` | `tk.Frame\|None` | `None` | Drop position indicator |
| `_update_job` | `str\|None` | `None` | Debounce: output update |
| `_roster_job` | `str\|None` | `None` | Debounce: roster refresh |
| `_save_lib_job` | `str\|None` | `None` | Debounce: library save |
| `_auto_save_job` | `str\|None` | `None` | Debounce: auto-save |
| `dj_search_var` | `StringVar` | `""` | DJ roster search query |

**Icons created (via iconipy):**
`icon_discord`, `icon_text`, `icon_trash`, `icon_quest`, `icon_pc`, `icon_arrow_up`, `icon_arrow_down`, `icon_chevron_down`, `icon_chevron_up`, `icon_chevron_right`, `icon_grip`, `icon_save`, `icon_copy`, `icon_edit`

---

### ui_builder.py — UISetupMixin

**Role:** Constructs the entire widget tree. The `setup_ui()` method is ~350 lines and builds:

**Layout Structure:**
```
App (root, 2-column grid)
├── Column 0: Left Panel
│   └── CTkTabview
│       ├── "Event" tab
│       │   └── CTkScrollableFrame (config_frame)
│       │       ├── EVENT CONFIGURATION section
│       │       │   ├── Title: CTkComboBox + Vol entry + Save/Delete buttons
│       │       │   ├── Timestamp: CTkDateTimePicker
│       │       │   └── Genres: Entry + Edit/Delete buttons + tag grid
│       │       └── SAVED EVENTS section
│       │           └── CTkScrollableFrame (saved_events_scroll)
│       ├── "DJ Roster" tab
│       │   ├── Header: label + search entry + "+ NEW DJ" button
│       │   └── CTkScrollableFrame (dj_roster_scroll)
│       └── "Settings" tab
│           └── (built by _build_settings_tab)
│
├── Column 1, Row 0: Top-Right Panel
│   └── CTkTabview
│       └── "Lineup" tab
│           ├── Header: "Default length" menu + "+ ADD DJ" + Save button
│           ├── CTkScrollableFrame (slots_scroll) ← SlotUI widgets go here
│           └── Open Decks row: checkbox + Amount menu + Slot length menu
│
└── Column 1, Row 1: Bottom-Right Panel
    └── Output Preview frame
        ├── Format buttons: Discord | Plain Text | Quest | PC
        └── CTkTextbox (output_text) + floating copy button
```

**Key methods:**
| Method | Purpose |
|--------|---------|
| `setup_ui()` | Build the entire widget tree |
| `_autohide_scrollbar(sf)` | Auto-hide scrollbar when content fits in `CTkScrollableFrame` |
| `save_title()` | Save current event title to library |
| `delete_saved_title()` | Remove a saved title from library |

**Widget references stored on `self`:** `left_tabs`, `right_tabs`, `title_combo`, `vol_entry`, `genre_entry`, `genre_tags_frame`, `saved_events_scroll`, `dj_roster_scroll`, `slots_scroll`, `output_text`, `copy_icon_btn`, `format_btn`, `plain_btn`, `quest_btn`, `pc_btn`, `master_dur_menu`, `od_toggle_btn`, `od_count_menu`, `od_count_label`, `od_dur_menu`, `od_dur_label`

---

### slot_ui.py — SlotUI

**Role:** A single performer slot row widget. Each slot is a horizontal `CTkFrame` containing:

```
┌──────────────────────────────────────────────────────────────────────┐
│ [20:00] [⋮] [DJ Name Combobox          ] [Genre Entry] [60▾] [🗑] │
│                🎙 Stream linked                                      │
└──────────────────────────────────────────────────────────────────────┘
 col 0    col 1        col 2                  col 3       col 4  col 5
```

**Column layout:**
| Column | Widget | Purpose |
|--------|--------|---------|
| 0 | `time_lbl` (CTkLabel) | Calculated start time (e.g., "20:00"), accent-colored |
| 1 | `grip` (CTkButton) | Drag handle with grip-vertical icon, cursor: fleur |
| 2 | `name_frame` → `name_entry` (CTkComboBox) + `info_label` | DJ name autocomplete + stream indicator |
| 3 | `genre_entry` (CTkEntry) | Genre text input |
| 4 | `dur_menu` (CTkOptionMenu) | Duration: 15–120 min in 15-min steps |
| 5 | `del_btn` (CTkButton) | Delete slot (danger-colored) |

**Reactive traces:**
- `name_var` → `_on_name_change()` → `_schedule_update()` + `update_dj_info()`
- `genre_var` → `_schedule_update()`
- `duration_var` → `_schedule_update()`
- `name_entry` command → `update_output()` + `update_dj_info()`

**Methods:**
| Method | Purpose |
|--------|---------|
| `_on_name_change()` | Schedule output update + refresh DJ info |
| `update_dj_info()` | Show/hide "🎙 Stream linked" indicator based on saved DJ data |
| `on_duration_change()` | Direct `update_output()` call |
| `delete_slot()` | Delegate to `app_ref.delete_slot(self)` |

---

### slot_manager.py — SlotMixin

**Role:** CRUD operations on the `self.slots` list.

| Method | Signature | Purpose |
|--------|-----------|---------|
| `add_initial_slots()` | `()` | Create one empty slot on startup |
| `apply_master_duration()` | `()` | Set all slots to the master duration value |
| `add_slot()` | `(name, genre, duration)` | Create new `SlotUI`, append, refresh, update |
| `refresh_slots()` | `()` | `pack_forget` all, then `pack` in order |
| `move_slot()` | `(slot_ui, direction)` | Swap adjacent slots and refresh |
| `_duplicate_last_slot()` | `()` | Clone last slot's name/genre/duration (Ctrl+D) |
| `delete_slot()` | `(slot_ui)` | Destroy widget, remove from list, update output |
| `toggle_od()` | `()` | Enable/disable Open Decks controls and update output |

---

### output_builder.py — OutputMixin

**Role:** Generates the formatted text output and manages format-button state.

**Output modes:**

| Format | `output_format` value | Output style |
|--------|-----------------------|--------------|
| Discord | `"discord"` | Discord markdown: `#`/`##`/`###`, `<t:UNIX:t>` timestamps, `**bold**` names |
| Plain Text | `"local"` | No markdown, `HH:MM` times with timezone abbreviation |
| Quest | `"quest"` | VRCDN stream links in HTTPS format, one per code block |
| PC | `"pc"` | VRCDN stream links in RTSPT format, one per code block |

**`update_output()` pipeline:**
1. **Always:** Recalculate and stamp `slot.time_lbl` with start times (HH:MM) for all slots
2. **Quest/PC mode:** Extract stream links from saved DJ data, apply VRCDN conversion, render in code blocks
3. **Discord/Plain mode:**
   - Build title line (with optional VOL.N)
   - Build timestamp line (Unix for Discord, formatted for plain)
   - Build genres line
   - Build "LINEUP" header
   - Iterate slots: calculate running time pointer, format each slot line
   - If Open Decks enabled: add OD section with available slots

**VRCDN link conversion logic (`_vrcdn_convert`):**
- Extracts the stream key from HTTPS or RTSPT VRCDN URLs
- Quest: returns `https://stream.vrcdn.live/live/{key}.live.ts`
- PC: returns `rtspt://stream.vrcdn.live/live/{key}`
- Non-VRCDN links pass through unchanged
- Links with `exact_link=True` skip conversion entirely

**Copy system:**
- Floating `⎘` button appears on hover over output textbox
- `copy_template()` copies to clipboard, briefly shows `✓` checkmark
- `copy_quest_links()` / `copy_pc_links()` switch format and copy

---

### dj_roster.py — DJRosterMixin

**Role:** Manages the DJ Roster tab — displays, edits, adds, and deletes DJ cards.

**`refresh_dj_roster_ui()`:**
1. Sorts `saved_djs` alphabetically (stripping non-alpha chars)
2. Filters by `dj_search_var` query
3. Destroys all children of `dj_roster_scroll`
4. Rebuilds: empty state label, no-match label, or DJ cards

**DJ Card anatomy (`_build_dj_card`):**
```
┌──────────────────────────────────────────────┐
│ [⋮] DJ Name                            [▲]  │  ← Header (clickable to toggle)
├──────────────────────────────────────────────┤
│  NAME                                        │
│  [text input                              ]  │  ← Collapsed by default
│  🎙  STREAM LINK                             │
│  [text input                              ]  │
│  ☑ Use exact link (skip conversion)          │
│  [💾] [🗑]                                   │
└──────────────────────────────────────────────┘
```

**Animated expand/collapse:**
- 8-step ease-out-quad animation (~130ms total, 16ms per frame ≈ 60fps)
- Expand: `pack` body → measure `winfo_reqheight()` → animate height from 1 to target
- Collapse: freeze current height → animate to 0 → `pack_forget()`

**DJ drag-to-lineup:** The grip button on DJ cards binds `<B1-Motion>` and `<ButtonRelease-1>` to `_on_dj_drag` / `_end_dj_drag` on DragDropMixin.

---

### drag_drop.py — DragDropMixin

**Role:** Two independent drag-and-drop systems using in-app `CTkFrame` ghosts (not OS `Toplevel` windows).

#### System 1: Slot Reorder

| Event | Method | Action |
|-------|--------|--------|
| `<ButtonPress-1>` on grip | `_slot_drag_start()` | Reset ghost to None |
| `<B1-Motion>` on grip | `_slot_drag_motion()` | Create/move ghost frame + update drop indicator |
| `<ButtonRelease-1>` on grip | `_slot_drag_end()` | Destroy ghost, compute target index, reorder `self.slots` |

- Ghost: `CTkFrame(self, fg_color="#4F46E5")` placed via `.place(x, y)` relative to app root
- Drop indicator: `tk.Frame(self.slots_scroll, bg="#818CF8", height=3)` placed between slots
- Index calculation: iterates slots comparing `y_root` to each slot's midpoint

#### System 2: DJ Roster → Lineup Drop

| Event | Method | Action |
|-------|--------|--------|
| `<B1-Motion>` on DJ grip | `_on_dj_drag()` | Create/move ghost + highlight slots panel |
| `<ButtonRelease-1>` on DJ grip | `_end_dj_drag()` | If over slots panel, call `add_slot(dj_name)` |

- `_is_over_slots_panel()` does bounds checking against `slots_scroll` geometry

---

### events_manager.py — EventsMixin

**Role:** Saved event CRUD and the Saved Events list UI.

**Event data schema:**
```python
{
    "title": str,
    "vol": str,
    "created_at": "YYYY-MM-DD HH:MM:SS",
    "timestamp": "YYYY-MM-DD HH:MM",
    "master_duration": str,
    "genres": list[str],
    "names_only": bool,
    "include_od": bool,
    "od_duration": str,
    "od_count": str,
    "slots": [
        {"name": str, "genre": str, "duration": str},
        ...
    ]
}
```

| Method | Purpose |
|--------|---------|
| `save_event_lineup()` | Serialize current state → detect duplicate by title → save to `saved_events` |
| `load_event_lineup(data)` | Restore all fields + destroy/recreate slots from event data |
| `delete_event_lineup(data)` | Confirm + remove from list + refresh UI |
| `duplicate_event_lineup(data)` | Deep copy, increment vol, new timestamp, save |
| `refresh_saved_events_ui()` | Destroy/rebuild saved event cards with Load/Copy/Delete buttons |

---

### genre_manager.py — GenreMixin

**Role:** Two-tier genre system — `saved_genres` (persistent library) and `active_genres` (selection for current event).

**Genre tag grid:** Renders as a grid of toggle buttons (4 columns). Active genres show a checkmark and use the primary accent color.

**Genre editor popup (`open_genre_editor`):**
- Modal `CTkToplevel` window (340x480)
- Add new genres, inline rename, reorder (up/down arrows), delete
- All changes apply immediately and propagate to the main UI

| Method | Purpose |
|--------|---------|
| `add_genre_from_entry()` | Parse entry field → `add_genre()` |
| `add_genre(genre)` | Add to both active and saved, persist, refresh |
| `remove_genre(genre)` | Remove from active only |
| `_toggle_genre(genre, is_active)` | Toggle genre on/off |
| `delete_saved_genre()` | Remove from both saved and active |
| `refresh_genre_tags()` | Rebuild the tag button grid |
| `open_genre_editor()` | Open the editor popup |

---

### data_manager.py — DataMixin

**Role:** All file I/O — YAML for data, JSON for settings/state.

**Loading priority chain:**
1. `lineup_library.yaml` (preferred) → fallback: `lineup_data.yaml`
2. `lineup_events.yaml` (preferred) → fallback: `lineup_data.yaml`

**DJ data migration on load:**
- Plain strings → `{"name": str, "stream": ""}`
- Old `{"name", "goggles", "link"}` → `{"name", "stream"}`
- Modern `{"name", "stream", "exact_link"}` → pass through

| Method | Purpose |
|--------|---------|
| `load_data()` | Read YAML files, populate `saved_titles`, `saved_djs`, `saved_genres`, `saved_events` |
| `get_dj_names()` | Return `[d["name"] for d in saved_djs]` |
| `save_data()` | Write both library and events |
| `_save_library()` | Write `lineup_library.yaml` |
| `_save_events()` | Write `lineup_events.yaml` |
| `_save_auto_state()` | Serialize current session to `auto_save.json` |
| `_check_auto_save()` | On startup: detect unclean exit, prompt restore |
| `_restore_window_state()` | Load `window_state.json`, apply geometry/maximized |
| `_on_close()` | Save window state + mark clean exit in `auto_save.json` + destroy |

---

### settings_manager.py — SettingsMixin

**Role:** Theme engine, color management, presets, and the Settings tab UI.

**Default color palette:**
| Key | Default | Purpose |
|-----|---------|---------|
| `accent_color` | `#818CF8` | Section headers, highlights |
| `primary_color` | `#4F46E5` | Main action buttons |
| `danger_color` | `#7F1D1D` | Delete/destructive buttons |
| `success_color` | `#059669` | Save/confirm buttons |
| `panel_bg` | `#1E293B` | Panels, tabviews, foreground cards |
| `card_bg` | `#0F172A` | Input fields, deep card backgrounds |
| `border_color` | `#334155` | Borders, secondary button backgrounds |
| `hover_color` | `#475569` | Hover state on buttons/controls |
| `scrollbar_color` | `#475569` | Scrollbar thumb |
| `output_font_size` | `14` | Output preview font size |

**Built-in presets:** Default (Indigo), Emerald, Rose, Slate (Mono)

**Theme application engine (`apply_theme()`):**
1. **Recursive widget-tree walk (`_recolor_widgets`):** For structural colors (panel_bg, card_bg, border_color, hover_color), walks the entire widget tree under `self`. For each widget, checks all color attributes (`fg_color`, `border_color`, `hover_color`, `button_color`, etc.) and replaces old color → new color.
2. **Explicit list updates:** For accent, primary, danger, success colors, iterates registered widget lists (`_accent_labels`, `_primary_buttons`, `_danger_buttons`, `_success_buttons`).
3. **Scrollbar theming:** Updates all registered `CTkScrollableFrame` scrollbar thumbs.
4. **Slot cascading:** Updates all slot delete buttons with current danger color.
5. **Snaps applied state:** Stores current settings as `_applied_settings` for next diff.

**Settings tab UI (`_build_settings_tab()`):**
- Output font size slider (10–24pt)
- Interactive colors: 4 rows with swatch, label, description, hex entry, color picker
- Structural colors: 5 rows with same layout
- "Reset to Defaults" button

---

### debounce.py — DebounceMixin

**Role:** Prevents rapid-fire callbacks from causing excessive work. Each debounce channel has a `_schedule_*` / `_run_scheduled_*` pair.

| Channel | Delay | Triggered By | Calls |
|---------|-------|--------------|-------|
| `_schedule_update` | 150ms | Any slot/event field change | `update_output()` → `_schedule_auto_save()` |
| `_schedule_roster_refresh` | 120ms | DJ search field typing | `refresh_dj_roster_ui()` |
| `_schedule_save_library` | 500ms | DJ save from slot | `_save_library()` |
| `_schedule_auto_save` | 5000ms | After every debounced output update | `_save_auto_state()` |

**Pattern:** Cancel any pending `after()` job, schedule a new one. Only the final call within the delay window actually executes.

Also provides `_refresh_slot_combos()` — updates all slot combobox dropdown values in a single pass.

---

### date_time_picker.py — CTkDateTimePicker

**Role:** Reusable date/time input widget with a calendar popup.

**Inline display:** A button showing the current datetime string + a calendar icon overlay.

**Popup (CTkToplevel):**
```
┌────────────────────────────────────────┐
│          Calendar (tkcalendar)          │
│  ┌──────────────────────────────────┐  │
│  │  S  M  T  W  T  F  S            │  │
│  │  1  2  3  4  5  6  7            │  │
│  │  ...                            │  │
│  └──────────────────────────────────┘  │
│                                        │
│  TIME  [HH ▾] : [MM ▾]               │
│                                        │
│            [Cancel] [Update Timestamp] │
└────────────────────────────────────────┘
```

- Modal (grab_set), positioned below the trigger button
- Hour: 00–23, Minute: 00–55 in 5-min steps (preserves non-5-min values from existing data)
- Output format: `"YYYY-MM-DD HH:MM"`

---

### utils.py

**Single function:**
```python
def _make_icon(factory, name, size) -> CTkImage
```
Wraps `iconipy.IconFactory.asPil(name)` into a `CTkImage` with the given display size. Used by `App.__init__` to create all 14 app icons.

---

## 7. Data Model & Persistence

### File formats

| File | Format | Written By | Read By |
|------|--------|-----------|---------|
| `lineup_library.yaml` | YAML | `_save_library()` | `load_data()` |
| `lineup_events.yaml` | YAML | `_save_events()` | `load_data()` |
| `settings.json` | JSON | `save_settings()` | `load_settings()` |
| `window_state.json` | JSON | `_on_close()` | `_restore_window_state()` |
| `auto_save.json` | JSON | `_save_auto_state()` | `_check_auto_save()` |
| `lineup_data.yaml` | YAML | Never (legacy seed) | `load_data()` (fallback) |

### lineup_library.yaml schema
```yaml
titles:
  - "Event Name A"
  - "Event Name B"
djs:
  - name: "DJ Alpha"
    stream: "https://stream.vrcdn.live/live/key123"
    exact_link: false
  - name: "DJ Beta"
    stream: "rtspt://stream.vrcdn.live/live/key456"
genres:
  - "House"
  - "Trance"
  - "Drum & Bass"
```

### lineup_events.yaml schema
```yaml
events:
  - title: "Bass Night"
    vol: "3"
    created_at: "2026-03-03 20:00:00"
    timestamp: "2026-03-10 22:00"
    master_duration: "60"
    genres: ["Bass", "Dubstep"]
    names_only: false
    include_od: true
    od_duration: "30"
    od_count: "4"
    slots:
      - name: "DJ Alpha"
        genre: "Bass"
        duration: "60"
      - name: "DJ Beta"
        genre: "Dubstep"
        duration: "45"
```

### settings.json schema
```json
{
  "output_font_size": 14,
  "accent_color": "#818CF8",
  "primary_color": "#4F46E5",
  "danger_color": "#7F1D1D",
  "success_color": "#059669",
  "panel_bg": "#1E293B",
  "card_bg": "#0F172A",
  "border_color": "#334155",
  "hover_color": "#475569",
  "scrollbar_color": "#475569",
  "user_presets": [
    {
      "name": "My Custom Theme",
      "settings": { ... }
    }
  ]
}
```

### auto_save.json schema
```json
{
  "title": "Event Name",
  "vol": "3",
  "timestamp": "2026-03-10 22:00",
  "master_duration": "60",
  "genres": ["House"],
  "names_only": false,
  "include_od": false,
  "od_duration": "30",
  "od_count": "4",
  "slots": [
    {"name": "DJ Alpha", "genre": "House", "duration": "60"}
  ]
}
```
On clean exit, replaced with: `{"clean_close": true}`

---

## 8. State Management

All application state lives directly on the `App` instance (`self`). There is no separate state store or model layer.

### State categories

| Category | Examples | Storage |
|----------|---------|---------|
| **Persistent library data** | `saved_djs`, `saved_titles`, `saved_genres` | `lineup_library.yaml` |
| **Persistent event data** | `saved_events` | `lineup_events.yaml` |
| **Current session** (volatile) | `slots`, `active_genres`, `event_title_var`, etc. | `auto_save.json` (crash recovery) |
| **UI preferences** | `settings`, `user_presets` | `settings.json` |
| **Window state** | geometry, maximized | `window_state.json` |
| **Transient UI state** | drag ghosts, debounce job IDs, search query | In-memory only |

### Reactive variable bindings

Tkinter's `StringVar` / `BooleanVar` trace system drives the reactive pipeline:
```
User types in field → StringVar.write trace fires → _schedule_update(150ms)
                                                       ↓ (after debounce)
                                                  update_output()
                                                       ↓
                                                  _schedule_auto_save(5000ms)
                                                       ↓ (after debounce)
                                                  _save_auto_state()
```

---

## 9. Reactive Update Pipeline

```
                    ┌──────────────────────────────────────┐
                    │          Input Sources                │
                    │                                      │
                    │  • SlotUI name/genre/duration vars   │
                    │  • event_title_var, event_vol_var    │
                    │  • event_timestamp                   │
                    │  • master_duration                   │
                    │  • include_od, od_duration, od_count │
                    │  • output_format                     │
                    │  • names_only                        │
                    │  • active_genres                     │
                    └───────────────┬──────────────────────┘
                                    │ trace_add("write", ...)
                                    ▼
                    ┌──────────────────────────────────────┐
                    │       _schedule_update(150ms)         │
                    │    (DebounceMixin)                    │
                    │    Cancels pending, reschedules       │
                    └───────────────┬──────────────────────┘
                                    │ after 150ms
                                    ▼
                    ┌──────────────────────────────────────┐
                    │         update_output()               │
                    │    (OutputMixin)                      │
                    │                                      │
                    │  1. Update slot time labels           │
                    │  2. Build formatted text              │
                    │  3. Write to output_text textbox      │
                    └───────────────┬──────────────────────┘
                                    │
                                    ▼
                    ┌──────────────────────────────────────┐
                    │     _schedule_auto_save(5000ms)       │
                    │    (DebounceMixin)                    │
                    └───────────────┬──────────────────────┘
                                    │ after 5s
                                    ▼
                    ┌──────────────────────────────────────┐
                    │       _save_auto_state()              │
                    │    (DataMixin)                        │
                    │    Write auto_save.json               │
                    └──────────────────────────────────────┘
```

---

## 10. UI Layout Map

```
┌──────────────────────────────────────────────────────────────────────────┐
│ App (ctk.CTk) — fg_color: #0F172A                                       │
│ Grid: col 0 | col 1                                                     │
│                                                                          │
│ ┌─────────────────────────┐ ┌──────────────────────────────────────────┐ │
│ │   Left Panel (row 0+1)  │ │   Top-Right (row 0)                     │ │
│ │   CTkTabview            │ │   CTkTabview                            │ │
│ │                         │ │   ┌──────────────────────────────────┐  │ │
│ │ ┌─[Event]──────────────┐│ │   │ "Lineup" tab                    │  │ │
│ │ │ EVENT CONFIGURATION  ││ │   │ ┌────────────────────────────┐  │  │ │
│ │ │ ┌─Title────────────┐ ││ │   │ │ Header: Default len + ADD │  │  │ │
│ │ │ │ ComboBox Vol [💾🗑]│ ││ │   │ ├────────────────────────────┤  │  │ │
│ │ │ ├─Timestamp────────┤ ││ │   │ │ ScrollableFrame            │  │  │ │
│ │ │ │ [DateTimePicker]  │ ││ │   │ │  ┌─SlotUI──────────────┐  │  │  │ │
│ │ │ ├─Genres───────────┤ ││ │   │ │  │ 20:00 ⋮ [Name] [G] │  │  │  │ │
│ │ │ │ Entry [✏️🗑]      │ ││ │   │ │  │ [60▾] [🗑]          │  │  │  │ │
│ │ │ │ [tag][tag][tag]   │ ││ │   │ │  ├─SlotUI──────────────┤  │  │  │ │
│ │ │ ├──────────────────┤ ││ │   │ │  │ 21:00 ⋮ [Name] [G] │  │  │  │ │
│ │ │ │ SAVED EVENTS     │ ││ │   │ │  │ [60▾] [🗑]          │  │  │  │ │
│ │ │ │ ┌─EventCard────┐ │ ││ │   │ │  └──────────────────────┘  │  │  │ │
│ │ │ │ │ Title [Ld][🗑]│ │ ││ │   │ ├────────────────────────────┤  │  │ │
│ │ │ │ └──────────────┘ │ ││ │   │ │ ☑ OPEN DECKS Amt: Len:    │  │  │ │
│ │ │ └──────────────────┘ ││ │   │ └────────────────────────────┘  │  │ │
│ │ └──────────────────────┘│ │   └──────────────────────────────────┘  │ │
│ │                         │ │                                          │ │
│ │ ┌─[DJ Roster]──────────┐│ ├──────────────────────────────────────────┤ │
│ │ │ DJ ROSTER [Search]   ││ │   Bottom-Right (row 1)                  │ │
│ │ │ ┌─DJCard───────────┐ ││ │   Output Preview                       │ │
│ │ │ │ ⋮ Name       [▲] │ ││ │   ┌──────────────────────────────────┐  │ │
│ │ │ │ (expandable body) │ ││ │   │ [Discord][Plain][Quest][PC]     │  │ │
│ │ │ └──────────────────┘ ││ │   ├──────────────────────────────────┤  │ │
│ │ └──────────────────────┘│ │   │ # Event Title VOL.1             │  │ │
│ │                         │ │   │ # <t:1234:F> (<t:1234:R>)      │  │ │
│ │ ┌─[Settings]───────────┐│ │   │ ## House // Trance              │  │ │
│ │ │ OUTPUT PREVIEW       ││ │   │ ### LINEUP                      │  │ │
│ │ │ INTERACTIVE COLORS   ││ │   │ <t:1234:t> | **DJ Alpha**      │  │ │
│ │ │ STRUCTURAL COLORS    ││ │   │ ...                         [⎘] │  │ │
│ │ │ [Reset to Defaults]  ││ │   └──────────────────────────────────┘  │ │
│ │ └──────────────────────┘│ └──────────────────────────────────────────┘ │
│ └─────────────────────────┘                                              │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 11. Drag-and-Drop System

### Implementation Details

Both drag systems use **in-app `CTkFrame` ghosts** placed via `.place(x, y)` rather than OS-level `Toplevel` windows. This keeps the ghost inside the app's rendering pipeline, avoiding compositor flicker.

**Ghost positioning math:**
```python
rx = event.x_root - self.winfo_rootx() + offset_x
ry = event.y_root - self.winfo_rooty() + offset_y
ghost.place(x=rx, y=ry)
```

**Slot reorder drop index calculation:**
```python
for i, slot in enumerate(self.slots):
    if y_root < slot.winfo_rooty() + slot.winfo_height() // 2:
        return i  # Insert before this slot
return len(self.slots)  # Append at end
```

**Drop indicator:** A 3px-high `tk.Frame` colored `#818CF8` that floats between slots to show the potential drop position.

---

## 12. Theming & Color System

### Architecture

The theming system has two mechanisms:

1. **Recursive widget-tree walk** (`_recolor_widgets`): For structural colors, walks every widget under the root and replaces any matching color attribute value. This handles dynamically-created widgets that weren't explicitly registered.

2. **Explicit reference lists**: For semantic colors (accent, primary, danger, success), the app maintains lists of registered widgets. This provides precise control over which widgets receive which colors.

### Color attribute scanning

The tree walk inspects these attributes on every widget:
```python
_COLOR_ATTRS = [
    "fg_color", "border_color", "hover_color",
    "button_color", "button_hover_color",
    "dropdown_fg_color", "dropdown_hover_color",
    "progress_color", "scrollbar_color",
]
```

### Change tracking

`_applied_settings` stores the last-applied color values. When `apply_theme()` runs, it diffs current settings against applied settings to know the "from" color for the tree walk. This allows chained color changes to work correctly.

---

## 13. Output Rendering Engine

### Time calculation algorithm

```python
current_pointer = event_start_datetime

for each slot:
    slot_start_time = current_pointer
    slot.time_lbl = format(current_pointer)  # UI label
    output_line = format(current_pointer, slot_name, slot_genre)
    current_pointer += timedelta(minutes=slot_duration)

# If Open Decks enabled:
for each OD slot:
    od_start_time = current_pointer
    output_line = format(current_pointer, "Slot N: [Available]")
    current_pointer += timedelta(minutes=od_duration)
```

### Discord timestamp format

Discord uses Unix timestamps with format specifiers:
- `<t:UNIX:F>` — Full date and time (e.g., "Monday, March 10, 2026 10:00 PM")
- `<t:UNIX:R>` — Relative (e.g., "in 7 days")
- `<t:UNIX:t>` — Short time (e.g., "10:00 PM")

These render in the viewer's local timezone within Discord.

---

## 14. Keyboard Shortcuts

| Shortcut | Action | Implemented In |
|----------|--------|----------------|
| `Ctrl+S` | Save current event lineup | `App.__init__` → `save_event_lineup()` |
| `Ctrl+D` | Duplicate last slot | `App.__init__` → `_duplicate_last_slot()` |
| `Esc` | Clear focus (close open dropdowns) | `App.__init__` → `self.focus()` |

---

## 15. Auto-Save & Crash Recovery

### Write trigger chain
```
Any field change → _schedule_update(150ms) → update_output() → _schedule_auto_save(5000ms) → _save_auto_state()
```

### On clean close (`_on_close`)
1. Save window geometry to `window_state.json`
2. Overwrite `auto_save.json` with `{"clean_close": true}`
3. `self.destroy()`

### On startup (`_check_auto_save`, called 150ms after init)
1. If `auto_save.json` doesn't exist → return
2. If it contains `"clean_close": true` → return
3. If content is trivially empty → return
4. Otherwise, prompt: "An unsaved lineup was found. Restore it?"
5. If yes → `load_event_lineup(state_dict)`

---

## 16. External Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `customtkinter` | latest | Modern dark-mode Tkinter widget framework |
| `tkcalendar` | latest | Calendar widget for `CTkDateTimePicker` |
| `pyyaml` | latest | YAML read/write for data persistence |
| `iconipy` | latest | Lucide icon rendering to PIL images |

All dependencies are listed in `requirements.txt`. The app can be packaged as a standalone executable via PyInstaller using `lineup_builder.spec`.
