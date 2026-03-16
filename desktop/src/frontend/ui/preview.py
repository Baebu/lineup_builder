import os as _os
import re
from datetime import datetime
import dearpygui.dearpygui as dpg

from ..styling import fonts
from ..styling.fonts import styled_text, HEADER, BODY, MUTED, HINT

class PreviewBuilderMixin:
    def _build_visual_preview(self):
        """Build a DPG mockup of a Discord embed."""
        if not dpg.does_item_exist("discord_preview_theme"):
            with dpg.theme(tag="discord_preview_theme"):
                with dpg.theme_component(dpg.mvChildWindow):
                    dpg.add_theme_color(dpg.mvThemeCol_ChildBg, (43, 45, 49, 255))
                    dpg.add_theme_color(dpg.mvThemeCol_Border, (30, 31, 34, 255))
                    dpg.add_theme_style(dpg.mvStyleVar_ChildRounding, 4)
                    dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, 12, 12)

        with dpg.child_window(tag="discord_embed_mockup", width=-1, autosize_y=True, border=True):
            dpg.bind_item_theme(dpg.last_item(), "discord_preview_theme")
            with dpg.group(tag="preview_content_group"):
                pass

        dpg.add_spacer(height=10)
        styled_text("  * Preview reflects current Discord format text & image.", MUTED)

    def _on_output_tab_changed(self, s, a):
        if a == "output_tab_visual":
            self._update_visual_preview()

    def _update_visual_preview(self):
        """Refresh the items in the visual preview mockup."""
        if not dpg.does_item_exist("preview_content_group"):
            return
            
        dpg.delete_item("preview_content_group", children_only=True)
        
        desc = dpg.get_value("output_text") if dpg.does_item_exist("output_text") else ""
        
        def relative_time(dt):
            now = datetime.now()
            diff = dt - now
            seconds = diff.total_seconds()
            past = seconds < 0
            seconds = abs(seconds)
            if seconds < 60: res = "a few seconds"
            elif seconds < 3600: 
                m = int(seconds//60)
                res = f"{m} minute{'s' if m != 1 else ''}"
            elif seconds < 86400: 
                h = int(seconds//3600)
                res = f"{h} hour{'s' if h != 1 else ''}"
            else: 
                d = int(seconds//86400)
                res = f"{d} day{'s' if d != 1 else ''}"
            return f"{res} ago" if past else f"in {res}"

        def format_timestamp(match):
            unix = int(match.group(1))
            style = match.group(2)
            try:
                dt = datetime.fromtimestamp(unix)
            except Exception:
                return match.group(0)
                
            if style == 't': return dt.strftime("%I:%M %p").lstrip('0')
            if style == 'T': return dt.strftime("%I:%M:%S %p").lstrip('0')
            if style == 'd': return dt.strftime("%m/%d/%Y")
            if style == 'D': return dt.strftime("%B %d, %Y")
            if style == 'f': return dt.strftime("%B %d, %Y %I:%M %p").replace(' 0', ' ')
            if style == 'F': return dt.strftime("%A, %B %d, %Y %I:%M %p").replace(' 0', ' ')
            if style == 'R': return relative_time(dt)
            return dt.strftime("%Y-%m-%d %H:%M")

        dpg.push_container_stack("preview_content_group")
        
        # Embed Title
        t_title = styled_text("Lineup Builder", {"color": (255, 255, 255, 255)})
        if fonts.h2_font:
            dpg.bind_item_font(t_title, fonts.h2_font)
        dpg.add_spacer(height=4)
        
        if not dpg.does_item_exist("discord_code_theme"):
            with dpg.theme(tag="discord_code_theme"):
                with dpg.theme_component(dpg.mvChildWindow):
                    dpg.add_theme_color(dpg.mvThemeCol_ChildBg, (30, 31, 34, 255))
                    dpg.add_theme_style(dpg.mvStyleVar_ChildRounding, 4)
                    dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, 8, 8)
        
        lines = desc.split('\n')
        in_code_block = False
        code_block_text =[]
        
        for line in lines:
            if line.startswith("```"):
                if in_code_block:
                    in_code_block = False
                    cb_height = max(20, len(code_block_text) * 18 + 16)
                    with dpg.child_window(width=-1, height=cb_height, border=False):
                        dpg.bind_item_theme(dpg.last_item(), "discord_code_theme")
                        dpg.add_text("\n".join(code_block_text), color=(200, 200, 200, 255))
                    code_block_text =[]
                else:
                    in_code_block = True
                continue
                
            if in_code_block:
                code_block_text.append(line)
                continue
                
            if not line.strip():
                dpg.add_spacer(height=4)
                continue
                
            # Process timestamps
            line = re.sub(r'<t:(\d+):([tTdDfFR])>', format_timestamp, line)
            
            # Process bold
            line = re.sub(r'\*\*(.*?)\*\*', r'\1', line)
            
            # Process links [Text](url)
            line = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', line)
            
            # Process headers (bind dynamically loaded bold fonts)
            if line.startswith("### "):
                t = styled_text(line[4:], {"color": (255, 255, 255, 255)}, wrap=0)
                if fonts.h3_font:
                    dpg.bind_item_font(t, fonts.h3_font)
            elif line.startswith("## "):
                t = styled_text(line[3:], {"color": (255, 255, 255, 255)}, wrap=0)
                if fonts.h2_font:
                    dpg.bind_item_font(t, fonts.h2_font)
            elif line.startswith("# "):
                t = styled_text(line[2:], {"color": (255, 255, 255, 255)}, wrap=0)
                if fonts.h1_font:
                    dpg.bind_item_font(t, fonts.h1_font)
            else:
                styled_text(line, BODY, wrap=0)
                
        # Catch any unclosed code blocks
        if in_code_block and code_block_text:
            cb_height = max(20, len(code_block_text) * 18 + 16)
            with dpg.child_window(width=-1, height=cb_height, border=False):
                dpg.bind_item_theme(dpg.last_item(), "discord_code_theme")
                dpg.add_text("\n".join(code_block_text), color=(200, 200, 200, 255))
                
        # Image
        img_path = getattr(self, "discord_embed_image", "").strip()
        if img_path and _os.path.exists(img_path):
            dpg.add_spacer(height=8)
            with dpg.child_window(width=-1, height=150, border=True):
                styled_text("      IMAGE ATTACHMENT", MUTED)
                styled_text(f"   {_os.path.basename(img_path)}", HINT)
                
        dpg.pop_container_stack()