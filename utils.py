import customtkinter as ctk


def _make_icon(factory, name, size):
    """Return a CTkImage from an iconipy IconFactory."""
    img = factory.asPil(name)
    return ctk.CTkImage(light_image=img, dark_image=img, size=(size, size))
