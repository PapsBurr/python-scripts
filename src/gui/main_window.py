import logging
import customtkinter as ctk
import sys
import os
from gui.hold_key_ui import HoldKeyUI
from gui.weather_ui import WeatherUI
from gui.recipe_ui import RecipeUI
from gui.multi_agent_orchestration_ui import MultiAgentOrchestrationUI


class MainWindow:
    def __init__(self, root):
        self.root = root
        self.WINDOW_SIZE = "400x500"
        self.root.title("Nathan's Python Scripts")
        self.root.geometry(self.WINDOW_SIZE)

        self.default_font = ctk.CTkFont(family="Helvetica", size=16)
        self.title_font = ctk.CTkFont(
            family=self.default_font.cget("family"),
            size=self.default_font.cget("size") + 4,
            weight="bold",
        )

        if getattr(sys, "frozen", False):
            icon_path = os.path.join(sys._MEIPASS, "assets", "favicon.ico")
        else:
            icon_path = "src/assets/favicon.ico"
        self.root.iconbitmap(icon_path)

        self.current_ui = None
        self.scripts_list = ["None", "Hold Key", "Weather", "Recipe Finder", "Multi-Agent Orchestration"]
        logging.info("Main window initializing...")
        self.setup_ui()

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def setup_ui(self):
        # Main frame
        main_frame = ctk.CTkFrame(self.root)
        main_frame.pack(pady=10, padx=10, expand=True, fill="both")

        # Header frame
        header_frame = ctk.CTkFrame(main_frame)
        header_frame.pack(fill="x", padx=10, pady=10)
        header_label = ctk.CTkLabel(
            header_frame,
            text="Nathan's Python Scripts",
            font=self.title_font,
            height=50,
        )
        header_label.pack()

        # Script selector
        selection_frame = ctk.CTkFrame(main_frame)
        selection_frame.pack(fill="x", padx=10, pady=10)

        selection_label = ctk.CTkLabel(
            selection_frame, text="Select a script:", font=self.default_font
        )
        selection_label.pack(pady=5)

        self.script_type = ctk.StringVar()
        self.combobox = ctk.CTkOptionMenu(
            selection_frame,
            variable=self.script_type,
            values=self.scripts_list,
            font=self.default_font,
            command=self.on_selection,
        )
        self.combobox.set("None")
        self.combobox.pack(pady=(0, 10))

        # Dynamic content
        self.dynamic_content_frame = ctk.CTkFrame(main_frame)
        self.dynamic_content_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.setup_default_ui()

    def on_selection(self, event):
        """Called when a new script is selected."""
        selection = self.script_type.get()
        logging.info(f"Script selected: {selection}")

        self.clear_dynamic_content()

        match selection:
            case "Hold Key":
                self.setup_hold_key_ui()
            case "Weather":
                self.setup_weather_ui()
            case "Recipe Finder":
                self.setup_recipe_ui()
            case "Multi-Agent Orchestration":
                self.setup_multi_agent_orchestration()
            case _:
                self.setup_default_ui()

    def clear_dynamic_content(self):
        """Clears the dynamic content frame."""
        if self.current_ui and hasattr(self.current_ui, "cleanup"):
            self.current_ui.cleanup()

        for widget in self.dynamic_content_frame.winfo_children():
            widget.destroy()

        self.current_ui = None

    def setup_hold_key_ui(self):
        """Sets up the UI for the Hold Key script."""
        self.current_ui = HoldKeyUI(self.dynamic_content_frame)
        width, height = self.WINDOW_SIZE.split("x")
        if self.root.winfo_width() < int(width) and self.root.winfo_height() < int(
            height
        ):
            self.root.geometry(self.WINDOW_SIZE)
            logging.info(f"Upscaled window to default size: {self.WINDOW_SIZE}")

    def setup_weather_ui(self):
        """Sets up the UI for the Weather script."""
        self.current_ui = WeatherUI(self.dynamic_content_frame)
        width, height = 1000, 600
        if self.root.winfo_width() < width and self.root.winfo_height() < height:
            self.root.geometry(f"{width}x{height}")
            logging.info(f"Upscaled window to size: {width}x{height}")

    def setup_recipe_ui(self):
        """Sets up the UI for the Recipe Finder script."""
        self.current_ui = RecipeUI(self.dynamic_content_frame)
        width, height = 1000, 600
        if self.root.winfo_width() < width and self.root.winfo_height() < height:
            self.root.geometry(f"{width}x{height}")
            logging.info(f"Upscaled window to size: {width}x{height}")

    def setup_multi_agent_orchestration(self):
        """Sets up the UI for the Agent Orchestrator"""
        self.current_ui = MultiAgentOrchestrationUI(self.dynamic_content_frame)
        width, height = 1000, 600
        if self.root.winfo_width() < width and self.root.winfo_height() < height:
            self.root.geometry(f"{width}x{height}")
            logging.info(f"Upscaled window to size: {width}x{height}")

    def setup_default_ui(self):
        """Sets up the default UI when no script is selected."""
        self.default_ui_label = ctk.CTkLabel(
            self.dynamic_content_frame,
            text="Please select a script from the dropdown above.",
            font=self.default_font,
        )
        self.default_ui_label.pack(pady=20)

    def on_close(self):
        """Handles cleanup on window close."""
        if self.current_ui and hasattr(self.current_ui, "cleanup"):
            logging.info("Closing application and cleaning up resources...")
            self.current_ui.cleanup()
            logging.info("Cleanup complete.")
        self.root.destroy()
