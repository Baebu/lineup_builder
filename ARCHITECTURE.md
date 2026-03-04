# Lineup Builder — Architecture Document

> **Last updated:** 2026-03-04
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
7. [Data Model & State Management](#7-data-model--state-management)
8. [Event Bus & Reactive Pipeline](#8-event-bus--reactive-pipeline)
9. [UI Layout Map](#9-ui-layout-map)
10. [Drag-and-Drop System](#10-drag-and-drop-system)
11. [Theming & Color System](#11-theming--color-system)
12. [Output Rendering Engine](#12-output-rendering-engine)
13. [Keyboard Shortcuts](#13-keyboard-shortcuts)
14. [Auto-Save & Crash Recovery](#14-auto-save--crash-recovery)
15. [External Dependencies](#15-external-dependencies)

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
│  Composed from mixins via cooperative multiple inheritance      │
│                                                                 │
│  ┌────────────┐ ┌────────────┐ ┌─────────────┐ ┌────────────┐   │
│  │ UISetup    │ │ DJRoster   │ │ DragDrop    │ │ Events     │   │
│  │ Mixin      │ │ Mixin      │ │ Mixin       │ │ Mixin      │   │
│  ├────────────┤ ├────────────┤ ├─────────────┤ ├────────────┤   │
│  │ Genre      │ │ Slot       │ │ Output      │ │ Data       │   │
│  │ Mixin      │ │ Mixin      │ │ Mixin       │ │ Mixin      │   │
│  ├────────────┤ ├────────────┤ ├─────────────┤                  │
│  │ Settings   │ │ Debounce   │ │ Import      │                  │
│  │ Mixin      │ │ Mixin      │ │ Mixin       │                  │
│  └────────────┘ └────────────┘ └─────────────┘                  │
│                                                                 │
│  State & Backend Services:                                      │
│    LineupModel — Pure-Python source of truth                    │
│    EventBus — Pub/sub broker (model_changed, etc.)              │
│    OutputGenerator — UI-agnostic text rendering                 │
└─────────────────────────────────────────────────────────────────┘
                            │
            ┌───────────────┼───────────────┐
            ▼               ▼               ▼
   lineup_library.yaml  lineup_events.yaml  settings.json
```

The application is a single-window CustomTkinter desktop app structured using a **mixin-composed View layer** bound to a **pure-Python Model layer**. The `App` inherits from multiple specialized mixins (UI layout, drag-and-drop, etc.). A custom `EventBus` broadcasts state changes from the `LineupModel` to decouple logic from Tkinter.

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
│
├── src/                        ← Python package (all app code)
│   ├── backend/
│   │   ├── lineup_model.py     ← Pure-Python data model (source of truth)
│   │   ├── event_bus.py        ← Pub-sub messaging system
│   │   ├── output_generator.py ← Independent text generator (no Tkinter)
│   │   ├── data_manager.py     ← File I/O setup and data loading logic
│   │   ├── debounce.py         ← Timers for updates/saves
│   │   └── output_builder.py   ← Bridges OutputGenerator results to UI
│   │
│   └── frontend/
│       ├── app.py              ← App class definition (mixin composition + __init__)
│       ├── ui_builder.py       ← Full UI layout widget construction
│       ├── slot_ui.py          ← SlotUI widget — single performer slot row
│       ├── slot_manager.py     ← Add/remove/reorder/duplicate slots
│       ├── dj_roster.py        ← DJ Roster tab: CRUD cards, search
│       ├── drag_drop.py        ← Slot reorder + DJ→lineup drag & drop
│       ├── events_manager.py   ← Save/load/delete/duplicate events
│       ├── genre_manager.py    ← Genre tags, genre editor popup
│       ├── settings_manager.py ← Settings tab, theme engine, presets
│       ├── import_parser.py    ← Text parsing/import capabilities 
│       ├── date_time_picker.py ← CTkDateTimePicker (reusable date/time input)
│       └── utils.py            ← Helper items like _make_icon()
│
├── tests/                      ← Test suite
│   ├── test_architecture.py
│   └── test_import.py
└── build/                      ← PyInstaller build artifacts
```

---

## 3. Dependency Graph

### Internal Module Dependencies

```
main.py
  └── src.frontend.app.App

app.py
  ├── src.backend.event_bus.EventBus
  ├── src.backend.lineup_model.LineupModel
  ├── src.backend.data_manager.DataMixin
  ├── src.backend.debounce.DebounceMixin
  ├── src.backend.output_builder.OutputMixin
  ├── src.frontend.ui_builder.UISetupMixin
  ├── src.frontend.dj_roster.DJRosterMixin
  ├── src.frontend.drag_drop.DragDropMixin
  ├── src.frontend.events_manager.EventsMixin
  ├── src.frontend.genre_manager.GenreMixin
  ├── src.frontend.slot_manager.SlotMixin
  ├── src.frontend.settings_manager.SettingsMixin
  └── src.frontend.import_parser.ImportMixin
```

### Decoupled State Updates

Instead of Tkinter `trace` callbacks directly driving everything, UI components modify the `LineupModel`. The setter methods on the model automatically trigger `bus.publish("model_changed")`. The `App` main modules subscribe to this event and refresh UI / output text.

---

## 4. Application Bootstrap Sequence

```
main.py
  │
  ├─ 1. App.__init__()
  │     ├─ ctk.CTk.__init__()           # Create root Tk window
  │     ├─ Initialize EventBus and LineupModel
  │     ├─ Configure base geometry and window state
  │     │
  │     ├─ self.load_data()              # DataMixin: load YAML files
  │     ├─ self.load_settings()          # SettingsMixin: load settings.json
  │     │
  │     ├─ self.setup_ui()               # UISetupMixin: build entire UI tree
  │     │     ├─ Event tab
  │     │     ├─ DJ Roster tab
  │     │     ├─ Settings & Lineup tabs
  │     │     └─ Output Preview
  │     │
  │     ├─ self.add_initial_slots()      # SlotMixin
  │     ├─ self.update_output()          # OutputMixin: initial render
  │     │
  │     ├─ Bind Event Bus Subscriptions
  │     ├─ Bind keyboard shortcuts
  │     └─ start _check_auto_save
  │
  └─ 2. app.mainloop()                  # Enter Tk event loop
```

---

## 5. Class Architecture (Mixin Composition)

### App Class Definition

```python
class App(
    UISetupMixin,       # UI construction
    DJRosterMixin,      # DJ Roster tab
    DragDropMixin,      # Drag-and-drop engine
    EventsMixin,        # Event save/load/delete
    GenreMixin,         # Genre tag system
    SlotMixin,          # Slot list management
    OutputMixin,        # Output text generation link
    DataMixin,          # File I/O
    SettingsMixin,      # Settings & theming
    DebounceMixin,      # Debounce timers
    ImportMixin,        # Import processing
    ctk.CTk,            # Base root window
):
```

The application leverages a large `App` monolithic facade constructed dynamically from specialized Mixins.

---

## 6. Module-by-Module Reference

### `src/backend/lineup_model.py`
The pure-Python dataclass tracking all lineups. Methods manipulate attributes directly and trigger an `EventBus` publication without relying on UI StringVars.

### `src/backend/event_bus.py`
Provides lightweight PubSub decoupled communications to broadcast application-wide updates like `model_changed`.

### `src/backend/output_generator.py`
A standalone text formatting generator that extracts formatting logic away from the GUI into purely testable logic.

### UI / Form Mixins
`ui_builder.py`, `slot_ui.py`, `slot_manager.py`, `genre_manager.py`, `events_manager.py` handle all CustomTkinter logic. `slot_ui.py` wraps an individual row inside the lineup layout.

---

## 7. Data Model & State Management

All critical payload attributes are held within `LineupModel` in standard python collections. The application does not store real lineup state strictly inside `ctk.StringVar` anymore.

### Key Datastores
| File | Format | Read By |
|------|--------|---------|
| `lineup_library.yaml` | YAML | `load_data()` |
| `lineup_events.yaml` | YAML | `load_data()` |
| `auto_save.json` | JSON | Crash recovery module |

---

## 8. Event Bus & Reactive Pipeline

```
                    ┌──────────────────────────────────────┐
                    │          Input Sources                │
                    │  (e.g., SlotUI combo changed)         │
                    └───────────────┬──────────────────────┘
                                    │ model.set_slot_field("name")
                                    ▼
                    ┌──────────────────────────────────────┐
                    │             LineupModel               │
                    │   updates state -> bus.publish()      │
                    └───────────────┬──────────────────────┘
                                    │ "model_changed"
                                    ▼
                    ┌──────────────────────────────────────┐
                    │               EventBus                │
                    │      broadcasts to subscribers        │
                    └──────┬────────────────────────┬──────┘
                           │                        │
             ┌─────────────▼─────────┐    ┌─────────▼─────────────┐
             │ Debounce Update (UI)  │    │  _save_auto_state()   │
             │   update_output()     │    │  (DebounceMixin)      │
             └───────────────────────┘    └───────────────────────┘
```

---

## 9. UI Layout Map

```
┌──────────────────────────────────────────────────────────────────────────┐
│ App (ctk.CTk) — fg_color: #0F172A                                       │
│ ┌─────────────────────────┐ ┌──────────────────────────────────────────┐ │
│ │   Left Panel (row 0+1)  │ │   Top-Right (row 0)                     │ │
│ │   CTkTabview            │ │   CTkTabview                            │ │
│ │ ┌─[Event]──────────────┐│ │   ┌──────────────────────────────────┐  │ │
│ │ │ EVENT CONFIGURATION  ││ │   │ "Lineup" tab                    │  │ │
│ │ ├─[DJ Roster]──────────┤│ │   ├──────────────────────────────────┤  │ │
│ │ │ DJ ROSTER [Search]   ││ │   │ ScrollableFrame (Slot UIs)      │  │ │
│ │ ├─[Settings]───────────┤│ │   └──────────────────────────────────┘  │ │
│ │ │ OUTPUT PREVIEW / UI  ││ ├──────────────────────────────────────────┤ │
│ │ └──────────────────────┘│ │   Bottom-Right (row 1)                  │ │
│ │                         │ │   Output Preview Box                    │ │
│ │                         │ │   ┌──────────────────────────────────┐  │ │
│ │                         │ │   │ [Discord][Plain][Quest][PC]     │  │ │
│ └─────────────────────────┘ └───┴──────────────────────────────────┴──┘ │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 10. Drag-and-Drop System

Both drag systems use **in-app `CTkFrame` ghosts** placed via `.place(x, y)`. They avoid OS-level `Toplevel` windows to maintain graphical performance and prevent glitches. Tracks positioning recursively against child widgets for slot indices.

---

## 11. Theming & Color System

Maintains lists of UI component subsets.
Recursively inspects widget attributes (`fg_color`, `border_color`, etc.) and runs global text styling overrides in `apply_theme()` within `SettingsMixin`. Uses diff matching to skip unchanging elements.

---

## 12. Output Rendering Engine

The backend `OutputGenerator` extracts Discord Markdown formatting and specific Unix timestamp parsing.
It uses standard TimeDelta sequences building upon `EventSnapshot` classes representing simple native datatypes passed from the UI thread.

---

## 13. Keyboard Shortcuts

| Shortcut | Action | Implemented In |
|----------|--------|----------------|
| `Ctrl+S` | Save current event lineup | `EventsMixin` |
| `Ctrl+D` | Duplicate last slot | `SlotMixin` |
| `Esc` | Clear focus | `App` |

---

## 14. Auto-Save & Crash Recovery

Triggered debounced 5s calls execute after `model_changed`. Auto-save payload replicates existing event snapshots. Upon an ungraceful crash, startup detects missing `"clean_close": true` attributes and recovers.

---

## 15. External Dependencies

- `customtkinter`
- `tkcalendar`
- `pyyaml`
- `iconipy`
