"""
Pure-Python Discord bot service — no GUI imports.
Runs a discord.py client on a background thread and exposes helpers
to send messages to channels by ID.
"""

import asyncio
import threading
from typing import Callable

import discord


class DiscordService:
    """Manages a Discord bot connection on a daemon thread."""

    def __init__(self):
        self._token: str = ""
        self._client: discord.Client | None = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self._thread: threading.Thread | None = None
        self._ready = threading.Event()
        self._on_status: Callable[[str], None] | None = None  # status callback

    # ── Lifecycle ─────────────────────────────────────────────────────────

    @property
    def is_running(self) -> bool:
        return (
            self._client is not None
            and self._loop is not None
            and self._ready.is_set()
        )

    def start(self, token: str, *, on_status: Callable[[str], None] | None = None):
        """Start the bot in a background thread. No-op if already running."""
        if self.is_running:
            return
        if not token.strip():
            if on_status:
                on_status("No bot token provided.")
            return

        self._token = token.strip()
        self._on_status = on_status
        self._ready.clear()

        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        """Gracefully shut down the bot."""
        if self._client and self._loop and not self._loop.is_closed():
            asyncio.run_coroutine_threadsafe(self._client.close(), self._loop)
        self._ready.clear()
        self._client = None
        self._loop = None
        self._thread = None
        if self._on_status:
            self._on_status("Disconnected")

    # ── Send helpers ──────────────────────────────────────────────────────

    def get_text_channels(
        self,
        *,
        on_result: Callable[[list[tuple[str, str, int]]], None] | None = None,
        on_error: Callable[[str], None] | None = None,
    ):
        """Fetch all visible text channels from the bot's guilds.

        Calls *on_result* with a list of ``(guild_name, channel_name, channel_id)``
        tuples, sorted by guild then channel name.
        """
        if not self.is_running:
            if on_error:
                on_error("Bot is not connected.")
            return

        async def _fetch():
            try:
                results: list[tuple[str, str, int]] = []
                for guild in self._client.guilds:
                    for ch in guild.text_channels:
                        results.append((guild.name, ch.name, ch.id))
                results.sort(key=lambda t: (t[0].lower(), t[1].lower()))
                if on_result:
                    on_result(results)
            except Exception as exc:
                if on_error:
                    on_error(str(exc))

        asyncio.run_coroutine_threadsafe(_fetch(), self._loop)

    def send_message(
        self,
        channel_id: int,
        content: str,
        *,
        on_success: Callable[[], None] | None = None,
        on_error: Callable[[str], None] | None = None,
    ):
        """Queue a message send.  Callbacks fire on the bot's event loop."""
        if not self.is_running:
            if on_error:
                on_error("Bot is not connected.")
            return

        async def _send():
            try:
                channel = self._client.get_channel(channel_id)
                if channel is None:
                    channel = await self._client.fetch_channel(channel_id)
                # Split into 2000-char chunks for Discord's limit
                for i in range(0, len(content), 2000):
                    await channel.send(content[i : i + 2000])
                if on_success:
                    on_success()
            except Exception as exc:
                if on_error:
                    on_error(str(exc))

        asyncio.run_coroutine_threadsafe(_send(), self._loop)

    def send_embed(
        self,
        channel_id: int,
        embed: discord.Embed,
        *,
        file: discord.File | None = None,
        on_success: Callable[[], None] | None = None,
        on_error: Callable[[str], None] | None = None,
    ):
        """Queue an embed message send, optionally with a file attachment."""
        if not self.is_running:
            if on_error:
                on_error("Bot is not connected.")
            return

        async def _send():
            try:
                channel = self._client.get_channel(channel_id)
                if channel is None:
                    channel = await self._client.fetch_channel(channel_id)
                kwargs: dict = {"embed": embed}
                if file is not None:
                    kwargs["file"] = file
                await channel.send(**kwargs)
                if on_success:
                    on_success()
            except Exception as exc:
                if on_error:
                    on_error(str(exc))

        asyncio.run_coroutine_threadsafe(_send(), self._loop)

    # ── Internal ──────────────────────────────────────────────────────────

    def _run(self):
        """Entry point for the background thread."""
        intents = discord.Intents.default()
        intents.message_content = True
        self._client = discord.Client(intents=intents)

        @self._client.event
        async def on_ready():
            self._ready.set()
            if self._on_status:
                self._on_status(f"Connected as {self._client.user}")

        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        try:
            self._loop.run_until_complete(self._client.start(self._token))
        except Exception as exc:
            if self._on_status:
                self._on_status(f"Bot error: {exc}")
        finally:
            self._ready.clear()
