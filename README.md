# Lineup Builder

A desktop app for building DJ event lineups and generating formatted output for Discord or plain text use.

![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey)
![License](https://img.shields.io/badge/license-MIT-green)

---

## Features

**Event Builder**
- Set event title, volume number, and start date/time
- Add and tag reusable genres
- Build a lineup of performer slots — DJ name, genre, and set duration
- Drag and drop slots to reorder the lineup
- Optional Open Decks section with configurable slot count and duration

**DJ Roster**
- Persistent roster with DJ name and VRCDN stream link
- Drag a DJ from the roster directly into the lineup
- Live search/filter, inline edit, save, and delete per card

**Output Formats**
| Mode | Description |
|---|---|
| **Discord** | Unix timestamps `<t:...:t>`, markdown headers, embed-suppressed links |
| **Plain Text** | `HH:MM` times with local timezone abbreviation, no markdown |
| **Quest** | VRCDN HTTPS stream URLs (`stream.vrcdn.live/live/...`) in a code block |
| **PC** | VRCDN `rtspt://` stream URLs in a code block |

**Persistence**
- Saves lineups, DJ roster, genres, and event titles to local YAML files
- Reload and edit past events; duplicate with auto-incremented volume number
- Window size and position restored between sessions

---

## Download

Grab the latest **`LineupBuilder.exe`** from the [Releases](https://github.com/Baebu/lineup_builder/releases) page — standalone Windows executable, no installation required.

---

## Running from Source

### 1. Clone the repo

```powershell
git clone https://github.com/Baebu/lineup_builder.git
cd lineup_builder
```

### 2. Create a virtual environment

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
pip install -r requirements.txt
```

### 4. Run

```powershell
python main.py
```

---

## Building the EXE

Requires [PyInstaller](https://pyinstaller.org):

```powershell
pip install pyinstaller
python -m PyInstaller lineup_builder.spec --clean
```

Output: `dist\LineupBuilder.exe`

---

## Project Structure

```
lineup_builder/           ← repo root
├── main.py               # Entry point
├── lineup_builder.spec   # PyInstaller build spec
├── requirements.txt
└── lineup_builder/       # Source package
    ├── __init__.py
    ├── app.py            # App class (assembles all mixins)
    ├── ui_builder.py     # Full UI layout
    ├── slot_ui.py        # Per-slot row widget
    ├── slot_manager.py   # Add / remove / reorder slots
    ├── drag_drop.py      # Drag-and-drop for slots and DJ roster
    ├── dj_roster.py      # DJ Roster tab
    ├── events_manager.py # Save / load / delete / duplicate events
    ├── genre_manager.py  # Genre tags and saved-genres panel
    ├── output_builder.py # Output text generation for all formats
    ├── data_manager.py   # YAML/JSON persistence and window state
    ├── debounce.py       # Debounced UI callbacks
    ├── date_time_picker.py  # Reusable CTkDateTimePicker widget
    └── utils.py          # Icon helper
```

---

## Data Files

The following files are created automatically at runtime and are excluded from version control:

| File | Contents |
|---|---|
| `lineup_library.yaml` | Saved titles, DJs, genres |
| `lineup_events.yaml` | Saved event lineups |
| `window_state.json` | Window geometry and maximized state |
