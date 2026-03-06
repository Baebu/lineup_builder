import dearpygui.dearpygui as dpg

from . import theme as T
from .fonts import Icon, bind_icon_font


def add_icon_button(icon: str, is_danger: bool = False, is_primary: bool = False, **kwargs) -> int:
    """Create a standardized icon button, automatically binding the icon font and applying the proper theme."""
    if "width" not in kwargs and "width=-1" not in str(kwargs):
        kwargs["width"] = T.ICON_BTN_W
    kwargs.setdefault("height", 20)

    btn = dpg.add_button(label=icon, **kwargs)
    bind_icon_font(btn)
    
    if is_danger:
        dpg.bind_item_theme(btn, "danger_btn_theme")
    elif is_primary:
        dpg.bind_item_theme(btn, "primary_btn_theme")
        
    return btn

def add_primary_button(label: str, **kwargs) -> int:
    """Create a standard primary button with the primary theme applied."""
    kwargs.setdefault("height", 20)
    btn = dpg.add_button(label=label, **kwargs)
    dpg.bind_item_theme(btn, "primary_btn_theme")
    return btn

def add_danger_button(label: str, **kwargs) -> int:
    """Create a standard danger button with the danger theme applied."""
    kwargs.setdefault("height", 20)
    btn = dpg.add_button(label=label, **kwargs)
    dpg.bind_item_theme(btn, "danger_btn_theme")
    return btn

def add_styled_input(**kwargs) -> int:
    """Create a stylized text input widget, applying appropriate defaults."""
    if not kwargs.get("multiline"):
        kwargs.setdefault("height", 20)
    return dpg.add_input_text(**kwargs)

def add_styled_combo(**kwargs) -> int:
    """Create a dropdown combo box."""
    kwargs.setdefault("height", 20)
    return dpg.add_combo(**kwargs)
