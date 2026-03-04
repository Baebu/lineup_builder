import os
import sys

import customtkinter as ctk


def get_data_dir() -> str:
    """Return the directory where runtime data files live.

    - Frozen (PyInstaller exe): the folder that contains the .exe.
    - Development: the project root (three levels above this file).
    """
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    # src/frontend/utils.py  →  ../../..  =  project root
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _make_icon(factory, name, size):
    """Return a CTkImage from an iconipy IconFactory."""
    img = factory.asPil(name)
    return ctk.CTkImage(light_image=img, dark_image=img, size=(size, size))
