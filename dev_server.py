#!/usr/bin/env python3
"""
Development script that runs the server with auto-reload on code changes.
Uses uvicorn's built-in reload for efficiency.
"""

import os
import subprocess
import sys
from pathlib import Path


def main():
    server_dir = Path(__file__).parent / "server" / "src"
    server_py = server_dir / "server.py"

    if not server_py.exists():
        print(f"Error: {server_py} not found")
        sys.exit(1)

    # Use the server's own venv if it exists, otherwise fall back to current Python
    server_venv_python = server_dir / ".venv" / "Scripts" / "python.exe"
    if not server_venv_python.exists():
        server_venv_python = server_dir / ".venv" / "bin" / "python"
    python = str(server_venv_python) if server_venv_python.exists() else sys.executable

    port = os.environ.get("PORT", "8000")
    print(f"Starting server on port {port} with auto-reload (watching {server_dir})...")
    subprocess.run(
        [
            python, "-m", "uvicorn",
            "server:app",
            "--host", "127.0.0.1",
            "--port", port,
            "--reload",
            "--reload-dir", str(server_dir),
        ],
        cwd=str(server_dir),
    )


if __name__ == "__main__":
    main()
