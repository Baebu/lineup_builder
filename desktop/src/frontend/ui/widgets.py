from contextlib import contextmanager

import dearpygui.dearpygui as dpg

from ..styling import theme as T
from ..styling.fonts import bind_icon_font


def popup_pos(trigger_tag: str | int | None = None, width: int = 300, height: int = 200):
    """Return (x, y) near *trigger_tag* (below-right of its rect), clamped to viewport.

    Falls back to the current mouse position when *trigger_tag* is None or
    the item doesn't exist yet.
    """
    vp_w = dpg.get_viewport_width()
    vp_h = dpg.get_viewport_height()

    if trigger_tag and dpg.does_item_exist(trigger_tag):
        try:
            mn = dpg.get_item_rect_min(trigger_tag)
            mx = dpg.get_item_rect_max(trigger_tag)
            x = int(mn[0])
            y = int(mx[1]) + 4  # just below the trigger
        except Exception:
            x, y = dpg.get_mouse_pos(local=False)
    else:
        x, y = dpg.get_mouse_pos(local=False)

    # Clamp so the popup stays inside the viewport
    x = max(0, min(x, vp_w - width))
    y = max(0, min(y, vp_h - height))
    return [x, y]


def add_icon_button(icon: str, is_danger: bool = False, is_primary: bool = False, **kwargs) -> int:
    """Create a standardized icon button, automatically binding the icon font and applying the proper theme."""
    if "width" not in kwargs and "width=-1" not in str(kwargs):
        kwargs["width"] = T.ICON_BTN_W

    btn = dpg.add_button(label=icon, **kwargs)
    bind_icon_font(btn)
    
    if is_danger:
        dpg.bind_item_theme(btn, "danger_btn_theme")
    elif is_primary:
        dpg.bind_item_theme(btn, "primary_btn_theme")
        
    return btn

def add_primary_button(label: str, **kwargs) -> int:
    """Create a standard primary button with the primary theme applied."""
    btn = dpg.add_button(label=label, **kwargs)
    dpg.bind_item_theme(btn, "primary_btn_theme")
    return btn

def add_danger_button(label: str, **kwargs) -> int:
    """Create a standard danger button with the danger theme applied."""
    btn = dpg.add_button(label=label, **kwargs)
    dpg.bind_item_theme(btn, "danger_btn_theme")
    return btn

def add_context_menu(item_tag: int | str):
    """Adds a standard Copy/Paste right click menu to a text input."""
    with dpg.popup(item_tag, mousebutton=dpg.mvMouseButton_Right):
        def _copy(s, a, u):
            val = dpg.get_value(item_tag)
            if val:
                dpg.set_clipboard_text(str(val))
        def _paste(s, a, u):
            clip = dpg.get_clipboard_text()
            if clip:
                dpg.set_value(item_tag, clip)
        dpg.add_menu_item(label="Copy", callback=_copy)
        dpg.add_menu_item(label="Paste", callback=_paste)

def add_styled_input(**kwargs) -> int:
    """Create a stylized text input widget, applying appropriate defaults and context menu."""
    item = dpg.add_input_text(**kwargs)
    add_context_menu(item)
    return item

def add_styled_combo(**kwargs) -> int:
    """Create a dropdown combo box."""
    return dpg.add_combo(**kwargs)


@contextmanager
def section(app, section_id: str, label: str, default_open: bool = True):
    """Collapsible section. Use as a context manager.

    Creates a wrapper group + toggle button header.
    All widgets created inside the ``with`` block go into the content group.
    """
    wrapper_tag = f"sect_{section_id}"
    content_tag = f"sect_c_{section_id}"

    dpg.add_group(tag=wrapper_tag)
    dpg.push_container_stack(dpg.last_item())

    # Header toggle button
    collapsed = app._section_collapsed.get(section_id, not default_open)
    icon = "\u25ba" if collapsed else "\u25bc"
    btn = dpg.add_button(
        label=f" {icon}  {label}",
        tag=f"sect_btn_{section_id}",
        callback=lambda: app._toggle_section(section_id),
        width=-1,
    )
    dpg.bind_item_theme(btn, "section_btn_theme")

    # Register the label for later reference
    app._section_labels[section_id] = label

    # Content container
    dpg.add_group(tag=content_tag, show=not collapsed)
    dpg.push_container_stack(dpg.last_item())

    try:
        yield content_tag
    finally:
        dpg.pop_container_stack()  # content
        dpg.pop_container_stack()  # wrapper