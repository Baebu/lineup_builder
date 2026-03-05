# **🎧 Lineup Builder**

**Lineup Builder** is a high-performance desktop GUI application designed for DJs and event organizers. It streamlines the tedious process of scheduling sets, managing performer rosters, and generating perfectly formatted output for Discord, plain text, and VRCDN-based VR platforms (Quest/PC).

## **🚀 Key Features**

### **📅 Event Orchestration**

* **Smart Header:** Quickly set event titles and auto-incrementing volume numbers.  
* **Integrated Date Picker:** A custom-styled calendar and time selector to ensure precise start times.  
* **Automated Import:** Paste an existing lineup from Discord or plain text. The intelligent parser automatically detects titles, timestamps, genres, and DJs, populating the editor in seconds.  
* **Genre Library:** Maintain a persistent, global library of genres. Toggle tags on/off or add new ones on the fly.

### **🎧 DJ Roster & Lineup Management**

* **Persistent Database:** Store your frequent performers along with their specific VRCDN stream links.  
* **Drag-and-Drop Workflow:** Drag DJs directly from your roster into the lineup.  
* **Interactive Lineup:** Reorder slots using intuitive drag handles. Start times for every slot are recalculated in real-time as durations change.  
* **Open Decks:** A dedicated, configurable section for "Open Deck" slots with customizable counts and durations.

### **📤 Professional Multi-Format Output**

The app generates real-time previews for four distinct use cases:

| Format | Output Style | Key Features |
| :---- | :---- | :---- |
| **Discord** | Markdown | Headers (\#), Unix Timestamps (\<t:12345:t\>), and bold names. |
| **Plain Text** | Human Readable | Clean HH:MM formatting with local timezone abbreviations (PST, GMT, etc). |
| **Quest** | HLS Links | Extracts VRCDN keys into https://... links in a copyable code block. |
| **PC** | RTSP Links | Generates rtspt://... low-latency links for PC-based VR clients. |

### **🎨 Personalization & Reliability**

* **Theme Engine:** Switch between multiple high-contrast presets like *Indigo*, *Emerald*, *Rose*, and *Ocean*.  
* **Crash Recovery:** Never lose your work. The app automatically saves session state, allowing you to restore your lineup if the application is closed unexpectedly.  
* **Window Persistence:** Remembers your window size, position, and maximized state across sessions.

## **⌨️ Keyboard Shortcuts**

| Shortcut | Action |
| :---- | :---- |
| Ctrl \+ S | Save current event lineup |
| Ctrl \+ D | Duplicate the last slot in the lineup |
| Ctrl \+ I | Open the Import Event dialog |
| Esc | Clear focus from input fields |

## **🛠 Installation & Development**

### **Prerequisites**

* **Python 3.11** or higher.  
* **Windows 10/11** (Optimized for Windows title bar coloring).

### **Setup**

1. **Clone the repository:**  
   git clone \[https://github.com/Baebu/lineup\_builder.git\](https://github.com/Baebu/lineup\_builder.git)  
   cd lineup\_builder

2. **Create and activate a virtual environment:**  
   python \-m venv .venv  
   .venv\\Scripts\\Activate.ps1

3. **Install dependencies:**  
   pip install \-r requirements.txt

4. **Run the application:**  
   python main.py

## **🏗 Architecture**

The project follows a **Modular Mixin Architecture**, ensuring that the GUI code remains decoupled from the business logic.

### **Backend (Pure Python)**

* lineup\_model.py: The single source of truth using dataclasses and an internal state model.  
* output\_generator.py: A "pure-function" engine. It takes a data snapshot and returns formatted strings, making it 100% unit-testable without a GUI.  
* data\_manager.py: Handles all YAML/JSON I/O and window state persistence.  
* event\_bus.py: A lightweight pub-sub hub for decoupled communication between modules.

### **Frontend (CustomTkinter)**

* The App class assembles various functional mixins (GenreMixin, DJRosterMixin, DragDropMixin) to build the interface dynamically.  
* theme.py: Centralized source for all colors, dimensions, and widget styles.

## **📦 Building the Executable**

To package the application into a standalone .exe:

1. Install PyInstaller:  
   pip install pyinstaller

2. Run the build command:  
   python \-m PyInstaller lineup\_builder.spec \--clean

The resulting LineupBuilder.exe will be located in the dist/ directory.

## **📂 Data Files**

The application stores data in the following files (created in the app directory):

* lineup\_library.yaml: Your global DJ roster, genre library, and saved titles.  
* lineup\_events.yaml: History of all saved event lineups.  
* settings.json: User preferences (theme, font size).  
* window\_state.json: Saved window geometry.  
* auto\_save.json: Recovery data for interrupted sessions.

## **📄 License**

This project is licensed under the MIT License \- see the [LICENSE](https://www.google.com/search?q=LICENSE) file for details.