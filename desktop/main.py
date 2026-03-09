import sys

from src.frontend.app import App


def main():
    # Set Windows AppUserModelID so the taskbar shows our icon, not Python's
    if sys.platform == "win32":
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            "baebu.lineupbuilder"
        )

    app = App()
    app.run()


if __name__ == "__main__":
    main()
