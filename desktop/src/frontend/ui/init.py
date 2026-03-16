from .layout import LayoutBuilderMixin
from .auth import AuthBuilderMixin
from .tabs import TabsBuilderMixin
from .discord import DiscordBuilderMixin
from .preview import PreviewBuilderMixin
from .interactions import InteractionsBuilderMixin

class UISetupMixin(
    LayoutBuilderMixin,
    AuthBuilderMixin,
    TabsBuilderMixin,
    DiscordBuilderMixin,
    PreviewBuilderMixin,
    InteractionsBuilderMixin
):
    """Combined mixin for building the application UI layout."""
    pass