import customtkinter as ctk
import tkinter as tk
from tkcalendar import Calendar
from datetime import datetime

class CTkDateTimePicker(ctk.CTkFrame):
    def __init__(self, master, variable=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.variable = variable
        
        # Grid layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Trigger Button showing current selection
        self.trigger_btn = ctk.CTkButton(
            self,
            textvariable=self.variable,
            fg_color="#0F172A",
            border_color="#334155",
            border_width=1,
            text_color="#CBD5E1",
            hover_color="#1E293B",
            anchor="w",
            command=self.open_picker,
            height=35
        )
        self.trigger_btn.grid(row=0, column=0, sticky="ew")
        
        # Calendar Icon overlay (right aligned)
        self.icon_label = ctk.CTkLabel(
            self.trigger_btn,
            text="📅",
            font=("Arial", 16),
            text_color="#94A3B8",
            cursor="hand2"
        )
        self.icon_label.place(relx=1.0, rely=0.5, anchor="e", x=-10)
        self.icon_label.bind("<Button-1>", lambda e: self.open_picker())

    def open_picker(self):
        # Create a top-level window for the picker
        top = ctk.CTkToplevel(self)
        top.title("Select Date & Time")
        top.geometry("340x450")
        top.resizable(False, False)
        # top.attributes("-topmost", True)
        
        # Set dark theme for the window background
        top.configure(fg_color="#1E293B")
        
        # Position near the button
        try:
            x = self.trigger_btn.winfo_rootx()
            y = self.trigger_btn.winfo_rooty() + self.trigger_btn.winfo_height() + 5
            top.geometry(f"+{x}+{y}")
        except:
            pass
            
        top.transient(self) # Keep it on top of main window
        top.grab_set()      # Modal behavior
        top.focus_set()

        # Parse current date/time to initialize
        current_dt = datetime.now()
        
        try:
            val = self.variable.get()
            # Try parsing known formats
            # Format expected: YYYY-MM-DD HH:MM
            for fmt in ["%Y-%m-%d %H:%M", "%Y-%m-%d"]:
                 try:
                     parsed = datetime.strptime(val, fmt)
                     current_dt = parsed
                     break
                 except ValueError:
                     continue
        except:
            pass
            
        # Calendar Section
        cal_frame = ctk.CTkFrame(top, fg_color="transparent")
        cal_frame.pack(fill="x", padx=10, pady=(10, 5))
        
        # Theme configuration for Calendar
        # Note: 'background' etc props work for basic tkcalendar styling
        cal = Calendar(
            cal_frame,
            selectmode='day',
            date_pattern='yyyy-mm-dd',
            year=current_dt.year,
            month=current_dt.month,
            day=current_dt.day,
            background="#0F172A",
            foreground="white",
            bordercolor="#334155",
            headersbackground="#1E293B",
            headersforeground="#94A3B8",
            selectbackground="#4F46E5",
            selectforeground="white",
            normalbackground="#1E293B",
            normalforeground="#CBD5E1",
            weekendbackground="#1E293B",
            weekendforeground="#CBD5E1",
            othermonthforeground="#475569", 
            othermonthbackground="#1E293B",
            othermonthweforeground="#475569",
            othermonthwebackground="#1E293B",
            font=("Arial", 10)
        )
        cal.pack(fill="both", expand=True)

        # Time Selection Section
        time_container = ctk.CTkFrame(top, fg_color="#0F172A", corner_radius=8, border_width=1, border_color="#334155")
        time_container.pack(fill="x", padx=10, pady=10)
        
        time_container.grid_columnconfigure(0, weight=1) # Label
        time_container.grid_columnconfigure(1, weight=0) # Hour
        time_container.grid_columnconfigure(2, weight=0) # :
        time_container.grid_columnconfigure(3, weight=0) # Min
        
        # Label
        ctk.CTkLabel(time_container, text="TIME", font=("Arial", 11, "bold"), text_color="#94A3B8").grid(row=0, column=0, padx=15, pady=10, sticky="w")
        
        # Hour
        hour_var = ctk.StringVar(value=f"{current_dt.hour:02d}")
        hours = [f"{i:02d}" for i in range(24)]
        hour_menu = ctk.CTkOptionMenu(
            time_container, 
            values=hours,
            variable=hour_var,
            width=70,
            fg_color="#1E293B", 
            button_color="#334155",
            button_hover_color="#475569",
            text_color="#CBD5E1",
            dropdown_fg_color="#1E293B",
            dropdown_text_color="#CBD5E1",
            dropdown_hover_color="#334155"
        )
        hour_menu.grid(row=0, column=1, padx=(0, 5), pady=10)
        
        # Colon
        ctk.CTkLabel(time_container, text=":", text_color="#CBD5E1", font=("Arial", 14, "bold")).grid(row=0, column=2, padx=2)
        
        # Minute
        current_minute_str = f"{current_dt.minute:02d}"
        minutes = [f"{i:02d}" for i in range(0, 60, 5)]
        if current_minute_str not in minutes:
            minutes.append(current_minute_str)
            minutes.sort()
            
        minute_var = ctk.StringVar(value=current_minute_str)
        minute_menu = ctk.CTkOptionMenu(
            time_container, 
            values=minutes,
            variable=minute_var,
            width=70,
            fg_color="#1E293B", 
            button_color="#334155",
            button_hover_color="#475569",
            text_color="#CBD5E1",
            dropdown_fg_color="#1E293B",
            dropdown_text_color="#CBD5E1",
            dropdown_hover_color="#334155"
        )
        minute_menu.grid(row=0, column=3, padx=(5, 15), pady=10)

        # Footer Actions
        btn_frame = ctk.CTkFrame(top, fg_color="transparent")
        btn_frame.pack(fill="x", padx=10, pady=(0, 10))
            
        def save():
            # Get date string from calendar (YYYY-MM-DD)
            # Calendar get_date() returns str or date based on pattern.
            date_val = cal.get_date()
            time_val = f"{hour_var.get()}:{minute_var.get()}"
            final_dt_str = f"{date_val} {time_val}"
            if self.variable:
                self.variable.set(final_dt_str)
            top.destroy()

        def close():
            top.destroy()

        save_btn = ctk.CTkButton(
            btn_frame, 
            text="Update Timestamp", 
            fg_color="#4F46E5", 
            hover_color="#4338CA", 
            width=140, 
            height=32,
            font=("Arial", 12, "bold"),
            command=save
        )
        save_btn.pack(side="right")
        
        close_btn = ctk.CTkButton(
            btn_frame, 
            text="Cancel", 
            fg_color="transparent", 
            border_width=1, 
            border_color="#334155", 
            text_color="#CBD5E1", 
            hover_color="#334155", 
            width=80, 
            height=32,
            font=("Arial", 12),
            command=close
        )
        close_btn.pack(side="right", padx=10)
