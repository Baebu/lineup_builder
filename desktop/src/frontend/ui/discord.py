import os as _os
from datetime import datetime
import dearpygui.dearpygui as dpg

from ..styling.fonts import styled_text, LABEL, MUTED, Icon, bind_icon_font
from .widgets import add_primary_button, popup_pos
from .confirm_dialog import confirm
from .toast import show_toast

class DiscordBuilderMixin:
    def _save_discord_credentials(self):
        """Persist client ID from the input field."""
        if dpg.does_item_exist("discord_client_id"):
            self.discord_client_id = dpg.get_value("discord_client_id").strip()
        self.save_settings()

    def _save_discord_ping_roles(self):
        if dpg.does_item_exist("discord_ping_roles"):
            display = dpg.get_value("discord_ping_roles")
            role_map = getattr(self, "_discord_role_map", {})
            self.discord_ping_roles = str(role_map.get(display, ""))
        self.save_settings()

    def _invite_discord_bot(self):
        """Open the bot invite URL in the browser."""
        client_id = getattr(self, "discord_client_id", "")
        if dpg.does_item_exist("discord_client_id"):
            client_id = dpg.get_value("discord_client_id").strip()
        if not client_id:
            self._set_discord_status("No Client ID provided.")
            return
        invite_url = (
            f"https://discord.com/oauth2/authorize"
            f"?client_id={client_id}&permissions=67584&scope=bot"
        )
        import webbrowser
        webbrowser.open(invite_url)

    def _clear_embed_image(self):
        """Clear the embed image."""
        self.discord_embed_image = ""
        if dpg.does_item_exist("embed_image_browse_btn"):
            dpg.set_item_label("embed_image_browse_btn", "Select Image...")
        
        # Clear the displayed image
        tex_tag = "embed_image_tex"
        if dpg.does_item_exist(tex_tag):
            dpg.delete_item(tex_tag)
        if dpg.does_item_exist("embed_image_display"):
            dpg.delete_item("embed_image_display")
            
        if hasattr(self, "_auto_event_save"):
            self._auto_event_save()

    def _browse_embed_image(self):
        """Open the native Windows file explorer to pick a local image."""
        import tkinter as _tk
        from tkinter import filedialog as _fd
        root = _tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        path = _fd.askopenfilename(
            parent=root,
            title="Select Embed Image",
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg *.gif *.webp"),
                ("All files", "*.*"),
            ],
        )
        root.destroy()
        if path:
            self.discord_embed_image = path
            if dpg.does_item_exist("embed_image_browse_btn"):
                label = _os.path.basename(path)
                if len(label) > 32:
                    label = label[:29] + "..."
                dpg.set_item_label("embed_image_browse_btn", label)
            
            # Clear existing image display so it gets refreshed
            tex_tag = "embed_image_tex"
            if dpg.does_item_exist(tex_tag):
                dpg.delete_item(tex_tag)
            if dpg.does_item_exist("embed_image_display"):
                dpg.delete_item("embed_image_display")
                
            if hasattr(self, "_auto_event_save"):
                self._auto_event_save()

    def _build_discord_settings_drawer(self):
        """Populate the Discord settings drawer with bot config fields."""
        styled_text("  Client ID", LABEL)
        dpg.add_input_text(
            tag="discord_client_id",
            default_value=getattr(self, "discord_client_id", ""),
            hint="Application Client ID...",
            width=-1,
            callback=lambda s, a, u=None: self._save_discord_credentials(),
        )
        dpg.add_spacer(height=2)
        styled_text("  Bot Token", LABEL)
        dpg.add_input_text(
            tag="discord_bot_token",
            default_value=getattr(self, "discord_bot_token", ""),
            hint="Paste bot token here...",
            password=True,
            width=-1,
            callback=lambda s, a, u=None: self._save_bot_token(),
        )
        dpg.add_spacer(height=4)
        add_primary_button(
            "Invite Bot to Server", width=-1,
            callback=lambda: self._invite_discord_bot(),
        )

    def _toggle_discord_settings_drawer(self):
        """Toggle the inline Discord settings drawer open/closed."""
        tag = "discord_settings_drawer"
        if not dpg.does_item_exist(tag):
            return
        currently_shown = dpg.is_item_shown(tag)
        dpg.configure_item(tag, show=not currently_shown)

    def _on_server_selected(self):
        """When server combo changes, save and fetch channels + roles."""
        if dpg.does_item_exist("discord_ping_server"):
            display = dpg.get_value("discord_ping_server")
            guild_map = getattr(self, "_discord_guild_map", {})
            guild_id = str(guild_map.get(display, ""))
            self.discord_ping_server = guild_id
            self.save_settings()
            if guild_id:
                self._fetch_discord_roles(guild_id)
                self._fetch_discord_channels_for_guild(guild_id)
            else:
                dpg.configure_item("discord_ping_roles", items=["None"])
                dpg.set_value("discord_ping_roles", "None")
                self.discord_ping_roles = ""
                dpg.configure_item("discord_channel", items=[])
                dpg.set_value("discord_channel", "")
                self.save_settings()

    def _save_discord_channel(self):
        """Read Discord channel combo selection and persist channel ID."""
        channel_map = getattr(self, "_discord_channel_map", {})
        tag = "discord_channel"
        if dpg.does_item_exist(tag):
            display = dpg.get_value(tag).strip()
            self.discord_channel_id = str(channel_map.get(display, ""))
        self.save_settings()

    def _channel_display(self, channel_id_str: str) -> str:
        """Return the display string for a saved channel ID, or empty."""
        channel_map = getattr(self, "_discord_channel_map", {})
        for display, cid in channel_map.items():
            if str(cid) == channel_id_str:
                return display
        return ""

    def _fetch_discord_channels_for_guild(self, guild_id_str: str):
        """Ask the bot to list text channels for a specific guild."""
        if not self._discord_service.is_running:
            self._set_discord_status("Connect bot first.")
            return
        self._discord_service.get_text_channels(
            on_result=lambda channels: self._queue_on_main(
                lambda: self._on_channels_fetched(channels, guild_id_str)),
            on_error=lambda e: self._set_discord_status(f"Error: {e}"),
        )

    def _on_channels_fetched(self, channels: list[tuple[str, str, int]], guild_id_str: str = ""):
        """Populate the single channel combo with fetched data."""
        items =[]
        channel_map: dict[str, int] = {}
        for guild_name, ch_name, ch_id in channels:
            # If we know the guild, filter to only that guild's channels
            if guild_id_str:
                guild_map = getattr(self, "_discord_guild_map", {})
                matched = False
                for g_display, g_id in guild_map.items():
                    if str(g_id) == guild_id_str and g_display == guild_name:
                        matched = True
                        break
                if not matched:
                    continue
            display = f"#{ch_name}"
            items.append(display)
            channel_map[display] = ch_id

        self._discord_channel_map = channel_map

        tag = "discord_channel"
        if dpg.does_item_exist(tag):
            dpg.configure_item(tag, items=items)
            saved_id = getattr(self, "discord_channel_id", "")
            current = ""
            for display, cid in channel_map.items():
                if str(cid) == saved_id:
                    current = display
                    break
            dpg.set_value(tag, current)

    def _fetch_discord_guilds(self):
        """Ask the bot to list all visible guilds."""
        if not self._discord_service.is_running:
            return
        self._discord_service.get_guilds(
            on_result=lambda guilds: self._queue_on_main(
                lambda: self._on_guilds_fetched(guilds)),
            on_error=lambda e: self._set_discord_status(f"Error: {e}"),
        )

    def _on_guilds_fetched(self, guilds: list[tuple[str, int]]):
        items =[]
        guild_map = {}
        for g_name, g_id in guilds:
            items.append(g_name)
            guild_map[g_name] = g_id
        
        self._discord_guild_map = guild_map
        if dpg.does_item_exist("discord_ping_server"):
            dpg.configure_item("discord_ping_server", items=items)
            
            saved_id = getattr(self, "discord_ping_server", "")
            current = ""
            for display, gid in guild_map.items():
                if str(gid) == saved_id:
                    current = display
                    break
            dpg.set_value("discord_ping_server", current)
            if current:
                self._fetch_discord_roles(str(guild_map[current]))
                self._fetch_discord_channels_for_guild(str(guild_map[current]))

    def _fetch_discord_roles(self, guild_id_str: str):
        if not guild_id_str or not guild_id_str.isdigit():
            return
        if not self._discord_service.is_running:
            return
        guild_id = int(guild_id_str)
        self._discord_service.get_roles(
            guild_id=guild_id,
            on_result=lambda roles: self._queue_on_main(
                lambda: self._on_roles_fetched(roles)),
            on_error=lambda e: self._set_discord_status(f"Error fetching roles: {e}")
        )

    def _on_roles_fetched(self, roles: list[tuple[str, int]]):
        items = ["None"]
        role_map = {"None": ""}
        for r_name, r_id in roles:
            display = f"@{r_name}"
            items.append(display)
            role_map[display] = r_id
            
        self._discord_role_map = role_map
        if dpg.does_item_exist("discord_ping_roles"):
            dpg.configure_item("discord_ping_roles", items=items)
            
            saved_id = getattr(self, "discord_ping_roles", "")
            current = "None"
            for display, rid in role_map.items():
                if str(rid) == saved_id:
                    current = display
                    break
            dpg.set_value("discord_ping_roles", current)

    def _save_bot_token(self):
        """Persist the bot token from the input field."""
        if dpg.does_item_exist("discord_bot_token"):
            self.discord_bot_token = dpg.get_value("discord_bot_token").strip()
            self.save_settings()

    def _set_discord_status(self, text: str):
        """Update the Discord status label (thread-safe via work queue)."""
        def _update():
            if dpg.does_item_exist("discord_status_text"):
                dpg.set_value("discord_status_text", f"  {text}")
            # Auto-fetch guilds when connected
            if "connected" in text.lower() or "ready" in text.lower():
                self._fetch_discord_guilds()
                show_toast(text, severity="success", duration=3.0)
            elif "error" in text.lower() or "failed" in text.lower():
                show_toast(text, severity="error", duration=5.0)
            elif "posted" in text.lower():
                show_toast(text, severity="success", duration=4.0)
            elif "disconnect" in text.lower():
                show_toast(text, severity="warning", duration=3.0)
        self._queue_on_main(_update)

    def _connect_discord_bot(self):
        """Start the Discord bot with the saved token."""
        token = getattr(self, "discord_bot_token", "")
        if dpg.does_item_exist("discord_bot_token"):
            token = dpg.get_value("discord_bot_token").strip()
            self.discord_bot_token = token
            self.save_settings()
        if not token:
            self._set_discord_status("No bot token provided.")
            return
        self._set_discord_status("Connecting...")
        self._discord_service.start(token, on_status=self._set_discord_status)

    def _disconnect_discord_bot(self):
        """Stop the Discord bot."""
        self._discord_service.stop()
        self._set_discord_status("Disconnected")

    def _confirm_post_to_discord(self):
        """Show confirmation before posting."""
        ch_display = ""
        if dpg.does_item_exist("discord_channel"):
            ch_display = dpg.get_value("discord_channel") or "selected channel"
        confirm(
            f"Post lineup to {ch_display}?",
            on_confirm=self._post_to_discord,
            title="Post to Discord",
            confirm_label="Post",
        )

    def _post_to_discord(self):
        """Post the current lineup as a Discord embed to the selected channel."""
        import datetime as _dt
        import discord

        if not self._discord_service.is_running:
            self._set_discord_status("Bot is not connected.")
            return

        channel_id_str = getattr(self, "discord_channel_id", "").strip()
        if not channel_id_str:
            self._set_discord_status("No channel selected.")
            return
        try:
            channel_id = int(channel_id_str)
        except ValueError:
            self._set_discord_status("Invalid channel ID.")
            return

        snap = self._build_snapshot()
        if not snap.slots:
            self._set_discord_status("Lineup is empty — nothing to post.")
            return

        body_text = dpg.get_value("output_text") if dpg.does_item_exist("output_text") else ""
        if not body_text.strip():
            self._set_discord_status("Output is empty.")
            return

        image_path = getattr(self, "discord_embed_image", "").strip()
        attach_file = None

        ping_roles = getattr(self, "discord_ping_roles", "").strip()
        ping_content = " ".join([f"<@&{r.strip()}>" for r in ping_roles.split(",") if r.strip()]) if ping_roles else ""

        embed_desc = body_text
        if ping_content:
            embed_desc = f"{body_text}\n\n{ping_content}".strip()

        embed = discord.Embed(
            description=embed_desc,
            color=0x4F46E5,
        )

        if image_path:
            if image_path.startswith(("http://", "https://")):
                embed.set_image(url=image_path)
            elif _os.path.isfile(image_path):
                ext = _os.path.splitext(image_path)[1]
                safe_name = f"image{ext}"
                attach_file = discord.File(image_path, filename=safe_name)
                embed.set_image(url=f"attachment://{safe_name}")

        ch_display = ""
        if dpg.does_item_exist("discord_channel"):
            ch_display = dpg.get_value("discord_channel") or "channel"

        self._set_discord_status(f"Posting to {ch_display}...")
        self._discord_service.send_embed(
            channel_id,
            embed=embed,
            content=None,
            file=attach_file,
            on_success=lambda: self._set_discord_status(
                f"Posted to {ch_display}."),
            on_error=lambda e: self._set_discord_status(f"Error: {e}"),
        )

    def _open_schedule_picker(self):
        """Open the calendar picker for the schedule datetime field."""
        from .date_time_picker import open_datetime_picker
        from ..types import DPGVar
        var = DPGVar(tag="discord_schedule_datetime")
        open_datetime_picker(var, callback=None)

    def _schedule_discord_post(self):
        """Add a scheduled post entry from the UI inputs."""
        raw_dt = ""
        if dpg.does_item_exist("discord_schedule_datetime"):
            raw_dt = dpg.get_value("discord_schedule_datetime").strip()
        if not raw_dt:
            self._set_discord_status("Enter a date/time to schedule.")
            return
        try:
            post_dt = datetime.strptime(raw_dt, "%Y-%m-%d %H:%M")
        except ValueError:
            self._set_discord_status("Invalid format. Use YYYY-MM-DD HH:MM")
            return
        if post_dt <= datetime.now():
            self._set_discord_status("Schedule time must be in the future.")
            return

        channel_key = "events"
        if dpg.does_item_exist("discord_schedule_channel"):
            channel_key = dpg.get_value("discord_schedule_channel")

        snap = self._build_snapshot()
        if not snap.slots:
            self._set_discord_status("Lineup is empty — nothing to schedule.")
            return

        if not hasattr(self, "_discord_scheduled_posts"):
            self._discord_scheduled_posts =[]

        body_text = dpg.get_value("output_text") if dpg.does_item_exist("output_text") else ""
        ping_roles = getattr(self, "discord_ping_roles", "").strip()
        ping_str = " ".join(f"<@&{r.strip()}>" for r in ping_roles.split(",") if r.strip())
        content_text = body_text

        entry = {
            "datetime": raw_dt,
            "channel": channel_key,
            "content": content_text,
            "ping": ping_str,
            "snapshot": snap,
            "image": getattr(self, "discord_embed_image", ""),
        }
        self._discord_scheduled_posts.append(entry)
        self._save_scheduled_posts()
        self._refresh_schedule_list_ui()
        self._set_discord_status(f"Scheduled for {raw_dt} → {channel_key}")

        if dpg.does_item_exist("discord_schedule_datetime"):
            dpg.set_value("discord_schedule_datetime", "")

    def _cancel_scheduled_post(self, idx: int):
        """Remove a scheduled post by index."""
        posts = getattr(self, "_discord_scheduled_posts",[])
        if 0 <= idx < len(posts):
            posts.pop(idx)
            self._save_scheduled_posts()
            self._refresh_schedule_list_ui()

    def _open_pending_popup(self):
        """Open a popup window showing pending scheduled posts."""
        tag = "pending_posts_win"
        if dpg.does_item_exist(tag):
            dpg.delete_item(tag)
        with dpg.window(
            tag=tag, label="Pending Scheduled Posts",
            modal=True, autosize=True, no_resize=True,
            no_scrollbar=True, min_size=(320, 100),
            pos=popup_pos("discord_pending_btn", width=320, height=200),
        ):
            dpg.add_group(tag="discord_scheduled_list")
            self._refresh_schedule_list_ui()
            dpg.add_spacer(height=4)
            dpg.add_button(label="Close", width=-1,
                           callback=lambda: dpg.delete_item(tag))

    def _refresh_schedule_list_ui(self):
        """Rebuild the pending-posts list in the popup."""
        tag = "discord_scheduled_list"
        if not dpg.does_item_exist(tag):
            return
        dpg.delete_item(tag, children_only=True)

        posts = getattr(self, "_discord_scheduled_posts",[])
        if not posts:
            styled_text("  No scheduled posts", MUTED, parent=tag)
            return

        for i, entry in enumerate(posts):
            dt_str = entry.get("datetime", "?")
            ch = entry.get("channel", "?")
            with dpg.group(horizontal=True, parent=tag):
                styled_text(f"  {dt_str} → {ch}", LABEL)
                idx = i  # capture for closure
                dpg.add_button(
                    label=Icon.CLOSE, width=22, height=18,
                    callback=lambda s, a, u=idx: self._cancel_scheduled_post(u),
                )
                bind_icon_font(dpg.last_item())

    def check_scheduled_posts(self):
        """Called every frame via process_queue to fire due posts."""
        now = datetime.now()
        last = getattr(self, "_last_schedule_check", None)
        if last and (now - last).total_seconds() < 1.0:
            return
        self._last_schedule_check = now

        posts = getattr(self, "_discord_scheduled_posts",[])
        if not posts:
            return

        fired =[]
        for i, entry in enumerate(posts):
            try:
                post_dt = datetime.strptime(entry["datetime"], "%Y-%m-%d %H:%M")
            except (ValueError, KeyError):
                fired.append(i)
                continue
            if now >= post_dt:
                self._fire_scheduled_post(entry)
                fired.append(i)

        if fired:
            for idx in reversed(fired):
                posts.pop(idx)
            self._save_scheduled_posts()
            self._refresh_schedule_list_ui()

    def _fire_scheduled_post(self, entry: dict):
        """Execute a scheduled post using its stored snapshot."""
        import datetime as _dt
        import discord

        channel_key = entry.get("channel", "events")
        if not self._discord_service.is_running:
            self._set_discord_status(f"Missed schedule ({channel_key}): bot not connected.")
            return

        channel_id_str = self.discord_channels.get(channel_key, "").strip()
        if not channel_id_str:
            self._set_discord_status(f"Missed schedule: no channel for '{channel_key}'.")
            return
        try:
            channel_id = int(channel_id_str)
        except ValueError:
            self._set_discord_status(f"Missed schedule: invalid channel for '{channel_key}'.")
            return

        snap = entry.get("snapshot")
        if snap is None or not snap.slots:
            return

        start = snap.start_datetime
        unix = int(start.timestamp())

        embed = discord.Embed(
            title=snap.full_title or "Lineup",
            description=f"<t:{unix}:F> (<t:{unix}:R>)",
            color=0x5865F2,
            timestamp=_dt.datetime.fromtimestamp(unix, tz=_dt.timezone.utc),
        )

        if snap.genres:
            embed.add_field(name="Genres", value=" // ".join(snap.genres), inline=False)

        ptr = start
        lineup_lines: list[str] =[]
        for slot in snap.slots:
            name = slot.name or "TBA"
            if snap.names_only:
                lineup_lines.append(f"**{name}**")
            else:
                ts = int(ptr.timestamp())
                genre_str = f"  •  {slot.genre}" if slot.genre else ""
                lineup_lines.append(f"<t:{ts}:t>  **{name}**{genre_str}")
            ptr += _dt.timedelta(minutes=slot.duration)

        lineup_text = "\n".join(lineup_lines)
        chunks = [lineup_text[i : i + 1024] for i in range(0, len(lineup_text), 1024)]
        for i, chunk in enumerate(chunks):
            embed.add_field(
                name="Lineup" if i == 0 else "\u200b",
                value=chunk, inline=False,
            )

        link_order =["TIMELINE", "VRCPOP", "X", "IG", "DISCORD", "VRC GROUP"]
        if snap.social_links:
            parts = [
                f"[{label}]({snap.social_links[label]})"
                for label in link_order
                if snap.social_links.get(label, "").strip()
            ]
            if parts:
                embed.add_field(name="Links", value=" | ".join(parts), inline=False)

        image_path = entry.get("image", "").strip()
        attach_file = None
        if image_path:
            if image_path.startswith(("http://", "https://")):
                embed.set_image(url=image_path)
            elif _os.path.isfile(image_path):
                ext = _os.path.splitext(image_path)[1]
                safe_name = f"image{ext}"
                attach_file = discord.File(image_path, filename=safe_name)
                embed.set_image(url=f"attachment://{safe_name}")

        embed.set_footer(text="GitHub | Baebu/lineup_builder")

        ping_content = entry.get("ping", "")
        if ping_content:
             embed.description = f"{embed.description}\n\n{ping_content}"

        self._set_discord_status(f"Sending scheduled post to {channel_key}...")
        self._discord_service.send_embed(
            channel_id, embed,
            content=entry.get("content", ""),
            file=attach_file,
            on_success=lambda: self._set_discord_status(
                f"Scheduled post sent to {channel_key}."),
            on_error=lambda e: self._set_discord_status(f"Schedule error: {e}"),
        )

    def _save_scheduled_posts(self):
        """Persist scheduled posts to settings.json."""
        from ..types import DPGVar  # noqa: F401
        posts = getattr(self, "_discord_scheduled_posts", [])
        serializable =[]
        for entry in posts:
            serializable.append({
                "datetime": entry.get("datetime", ""),
                "channel": entry.get("channel", ""),
                "content": entry.get("content", ""),
                "ping": entry.get("ping", ""),
                "image": entry.get("image", ""),
                "snapshot": self._snapshot_to_dict(entry.get("snapshot"))
                            if entry.get("snapshot") else None,
            })
        self.discord_scheduled_posts = serializable
        self.save_settings()

    @staticmethod
    def _snapshot_to_dict(snap) -> dict:
        """Serialize an EventSnapshot to a plain dict."""
        if snap is None:
            return {}
        return {
            "title": snap.title,
            "vol": snap.vol,
            "timestamp": snap.timestamp,
            "genres": list(snap.genres),
            "slots":[{"name": s.name, "genre": s.genre, "duration": s.duration}
                      for s in snap.slots],
            "names_only": snap.names_only,
            "output_format": snap.output_format,
            "saved_djs":[{"name": d.name, "stream": d.stream, "exact_link": d.exact_link}
                          for d in snap.saved_djs],
            "social_links": dict(snap.social_links),
        }

    @staticmethod
    def _dict_to_snapshot(d: dict):
        """Deserialize a plain dict back into an EventSnapshot."""
        from ...backend.models.types import DJInfo, EventSnapshot, SlotData
        if not d:
            return None
        return EventSnapshot(
            title=d.get("title", ""),
            vol=d.get("vol", ""),
            timestamp=d.get("timestamp", ""),
            genres=d.get("genres", []),
            slots=[SlotData(s.get("name", ""), s.get("genre", ""), s.get("duration", 60))
                   for s in d.get("slots", [])],
            names_only=d.get("names_only", False),
            output_format=d.get("output_format", "discord"),
            saved_djs=[DJInfo(dj.get("name", ""), dj.get("stream", ""), dj.get("exact_link", False))
                       for dj in d.get("saved_djs", [])],
            social_links=d.get("social_links", {}),
        )

    def _load_scheduled_posts(self):
        """Restore scheduled posts from settings (called at startup)."""
        self._discord_scheduled_posts =[]
        raw = getattr(self, "discord_scheduled_posts",[])
        now = datetime.now()
        for entry in raw:
            try:
                post_dt = datetime.strptime(entry["datetime"], "%Y-%m-%d %H:%M")
            except (ValueError, KeyError):
                continue
            if post_dt > now:
                snap = self._dict_to_snapshot(entry.get("snapshot"))
                self._discord_scheduled_posts.append({
                    "datetime": entry["datetime"],
                    "channel": entry.get("channel", "events"),
                    "content": entry.get("content", ""),
                    "snapshot": snap,
                })