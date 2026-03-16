@echo off
REM Development batch script that activates server venv and runs with auto-reload

cd /d "%~dp0\src"

REM Create virtual environment if it doesn't exist
if not exist .venv (
    echo Creating virtual environment...
    python -m venv .venv
)

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Install/update dependencies
pip install -r requirements.txt

REM Run the server with auto-reload
cd /d "%~dp0"
python dev_server.py

REM Deactivate venv when done
call deactivate
