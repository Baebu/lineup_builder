import sys

from src.frontend.app import App


def main():
    # Set Windows AppUserModelID so the taskbar shows our icon, not Python's
    if sys.platform == "win32":
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            "baebu.lineupbuilder"
        )
        
    import dearpygui.dearpygui as dpg
    from src.frontend.ui.widgets import add_context_menu

    # Monkeypatch dpg.add_input_text to automatically append our copy/paste right-click menu
    _original_add_input_text = dpg.add_input_text
    def _patched_add_input_text(*args, **kwargs):
        item = _original_add_input_text(*args, **kwargs)
        if item:
            add_context_menu(item)
        return item
    dpg.add_input_text = _patched_add_input_text

    app = App()
    app.run()


if __name__ == "__main__":
    main()
