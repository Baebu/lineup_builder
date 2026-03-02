# Lineup Builder — Project Instructions

## Overview

A desktop GUI app for building DJ event lineups and generating formatted text output for Discord or plain text use. Built with Python and CustomTkinter.

---

## Project Structure

| File | Purpose |
|---|---|
| `lineup_builder.py` | Main application — all UI and logic |
| `date_time_picker.py` | Reusable `CTkDateTimePicker` widget |
| `lineup_data.yaml` | Seed/legacy data file (titles, DJs, genres, events) |
| `lineup_library.yaml` | Runtime library — saved titles, DJs, genres (auto-generated) |
| `lineup_events.yaml` | Runtime events store — saved lineups (auto-generated) |
| `requirements.txt` | Python dependencies |

---

## Setup

### 1. Create a virtual environment

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```powershell
pip install -r requirements.txt
```

Dependencies:
- `customtkinter` — UI framework
- `tkcalendar` — Calendar widget used in the date/time picker
- `pyyaml` — YAML read/write for data persistence

### 3. Run the app

```powershell
python lineup_builder.py
```

---

## Architecture

### Classes

#### `SlotUI` (ctk.CTkFrame)
Represents a single performer slot in the lineup. Each slot has:
- DJ name (combo box with autocomplete from saved DJs)
- Genre (text entry)
- Duration (dropdown, 15–120 min in 15-min steps)
- Up/Down reorder buttons
- Delete button
- Save DJ / Delete DJ buttons
- Info label showing saved DJ metadata (goggles, link)

#### `App` (ctk.CTk)
The main application window. Key responsibilities:
- **Left panel** — tabbed interface with:
  - *Current Event* — event config (title, vol, date/time, genres, slots, OD settings, output format)
  - *Saved Events* — load/delete previously saved lineups
  - *DJ Roster* — view and edit saved DJs with goggles and link metadata
- **Right panel** — live output preview with Copy button

### Data Flow

1. User fills in event config and slots.
2. `update_output()` rebuilds the output text on every change via variable traces and widget callbacks.
3. Output can be copied to clipboard via "COPY TEMPLATE".
4. Events can be saved (with a timestamp) and reloaded later.

### Persistence

Two separate YAML files are used at runtime:
- **`lineup_library.yaml`** — titles, DJs, genres (the "library")
- **`lineup_events.yaml`** — saved event lineups

On first run, if neither exists, the app falls back to reading `lineup_data.yaml` for initial seed data. Once runtime files exist, `lineup_data.yaml` is ignored.

---

## Output Formats

### Discord Mode
- Uses Discord markdown (`#`, `##`, `###`)
- Times are rendered as Unix timestamps: `<t:UNIX:t>` (local time display in Discord)
- DJ links are wrapped in `<>` to suppress embeds

### Plain Text (Local) Mode
- No markdown
- Times shown as `HH:MM` with the local timezone abbreviation

---

## Key Methods in `App`

| Method | Description |
|---|---|
| `load_data()` | Loads library and events from YAML on startup |
| `save_data()` | Saves both library and events |
| `_save_library()` | Writes titles, DJs, genres to `lineup_library.yaml` |
| `_save_events()` | Writes events to `lineup_events.yaml` |
| `add_slot()` | Creates a new `SlotUI` and appends it to the list |
| `refresh_slots()` | Re-packs all slots in order (used after reorder/delete) |
| `move_slot()` | Swaps two slots in `self.slots` and calls `refresh_slots()` |
| `update_output()` | Rebuilds the output text box from current state |
| `copy_template()` | Copies output to clipboard with temporary button feedback |
| `load_event_lineup()` | Loads a saved event into the current editor |
| `refresh_dj_roster_ui()` | Rebuilds the DJ Roster tab from `self.saved_djs` |

---

## Adding Features

### Adding a new field to a slot
1. Add a `ctk.StringVar` in `SlotUI.__init__`.
2. Add a widget and grid it in the appropriate column.
3. Trace the variable: `self.new_var.trace_add("write", lambda *a: self.app_ref.update_output())`.
4. Read the value in `App.update_output()` and `App.save_current_event()` / `App.load_event_lineup()`.

### Adding a new event-level field
1. Add a `ctk.StringVar` in `App.__init__`.
2. Add the widget in `setup_ui()` under the *Current Event* tab.
3. Include the value in `save_current_event()` and restore it in `load_event_lineup()`.
4. Read it in `update_output()`.

### Adding a new saved-event field
Fields are stored as plain dict keys in the events list. Add the key when saving in `save_current_event()` and read it back in `load_event_lineup()`.

---

## Style Reference

The app uses a dark blue-gray palette:

| Role | Color |
|---|---|
| App background | `#0F172A` |
| Card/frame background | `#1E293B` |
| Button/border | `#334155` |
| Hover | `#475569` |
| Muted text | `#94A3B8` |
| Body text | `#CBD5E1` |
| Accent (purple) | `#818CF8` / `#4F46E5` |
| Danger | `#EF4444` / `#7F1D1D` |
| Success | `#059669` / `#047857` |
