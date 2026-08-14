import customtkinter as ctk
import logging
from scripts.multi_agent_orchestration_script import MultiAgentOrchestrationScript
from typing import List, Dict
from ctk_bonus_types import ClampedIntVar

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)


class MultiAgentOrchestrationUI:
    """CustomTkinter GUI for AI agent orchestration with multiple models and sequential workflows"""

    def __init__(self, parent_frame):
        self.parent_frame = parent_frame
        self.orchestrator: MultiAgentOrchestrationScript = MultiAgentOrchestrationScript()
        self.current_agent_panels = []
        
        # UI styling
        self.default_font = ctk.CTkFont(family="Helvetica", size=16)
        self.title_font = ctk.CTkFont(
            family=self.default_font.cget("family"),
            size=self.default_font.cget("size") + 4,
            weight="bold",
        )
        
        # Default model list - can be modified by user if needed
        self.available_models: List[str] = self.orchestrator.get_models()

        self.setup_ui()

    def setup_ui(self):
        """Configure all GUI components for the Agent Orchestrator."""
        
        # Title section
        self.title_label = ctk.CTkLabel(
            self.parent_frame,
            text="AI Agent Orchestration",
            font=self.title_font,
        )
        self.title_label.pack(pady=(10,5))

        self.description_label = ctk.CTkLabel(
            self.parent_frame,
            text="Agents will run in order from top to bottom, receiving the previous agents output as input.",
            font=self.default_font
        )
        self.description_label.pack(pady=(5,10))

        # # Set default number of agents
        self.num_agents = ClampedIntVar(value=1, min_val=1, max_val=5)
        self.prev_num_agents = self.num_agents.value
        self.num_agents.trace_add("write", self._on_num_agents_changed)
        num_agents_label = ctk.CTkLabel(
            self.parent_frame,
            text="Number of Agents: ",
            font=self.default_font
        )
        num_agents_label.pack(padx=5, pady=5)

        num_agents_steps = self.num_agents.max_val - self.num_agents.min_val
        num_agents_slider = ctk.CTkSlider(
            self.parent_frame, 
            from_=self.num_agents.min_val, 
            to=self.num_agents.max_val,
            variable=self.num_agents,
            number_of_steps=num_agents_steps,
        )
        num_agents_slider.pack(padx=5, pady=5)

        num_agents_counter_label = ctk.CTkLabel(
            self.parent_frame,
            textvariable=self.num_agents,
            font=self.default_font
        )
        num_agents_counter_label.pack(padx=5, pady=5)

        # Main config frame
        self.orchestrator_frame = ctk.CTkScrollableFrame(
            master=self.parent_frame,
        )
        self.orchestrator_frame.pack(padx=5, pady=5, expand=True, fill="both")

        # Initial Task Input
        self.agent_task_label = ctk.CTkLabel(
            self.orchestrator_frame,
            text="Initial Task:",
            font=self.default_font,
        )
        self.agent_task_label.pack(padx=20, pady=5)

        self.agent_task_entry = ctk.CTkTextbox(
            self.orchestrator_frame,
            font=self.default_font,
            width=600,
        )
        self.agent_task_entry.pack(padx=20, pady=5)

        # Create agent frames
        for _ in range(self.num_agents.get()):
            self._create_agent_panel(self.orchestrator_frame)

        # Control buttons frame
        button_frame = ctk.CTkFrame(self.parent_frame)
        button_frame.pack(pady=5)

        self.execute_button_text = ctk.StringVar(value="Run Workflow")
        
        self.execute_button = ctk.CTkButton(
            button_frame,
            textvariable=self.execute_button_text,
            font=self.default_font,
            command=self.run_workflow,
        )
        self.execute_button.pack(side="left", padx=5)

    def toggle_add_agent(self):
        """Enable/disable the add agent option - shows/hides role and goal fields."""
        
        if self.add_agent_var.get():
            # Show role/goal fields (grid them back in)
            self.agent_role_optionmenu.grid(row=4, column=1, padx=5, pady=2)
            self.agent_goal_entry.grid(row=5, column=1, padx=5, pady=2)
        else:
            # Hide role/goal fields (grid_forget them)
            self.agent_role_optionmenu.grid_remove()
            self.agent_goal_entry.grid_remove()

    def run_workflow(self):
        """Execute the multi-agent workflow based on configured parameters."""
        
        if not self.orchestrator:
            # Initialize orchestrator with current model and tools settings
            try:
                self.orchestrator = MultiAgentOrchestrationScript(
                    models=[self.model_selection_var.get()],
                    enable_tools=self.tools_enabled.get(),
                )
            except Exception as e:
                logging.error(f"Failed to initialize orchestrator: {e}")
                self.status_label.configure(text="Status: Error initializing")
                return
        
        # Define initial task and subsequent tasks (only one agent in this template)
        agent_task = self.agent_task_entry.get().strip() or "Research AI trends for 2024"

        subsequent_agents_config: List[Dict] = []
        
        if self.add_agent_var.get():
            role = self.agent_role_var.get()
            goal = self.agent_goal_var.get().strip() or f"{role} should analyze findings"
            
            subsequent_agents_config.append({
                'role': role,
                'goal': goal,
                'backstory': '',  # Could add backstory if needed in future iterations
            })

        try:
            logging.debug(f"Running workflow with initial task='{agent_task}'")
            
            # Execute workflow
            results = self.orchestrator.execute_workflow(
                agent_task_description=agent_task,
                subsequent_tasks=subsequent_agents_config,
            )

            self.status_label.configure(text=f"Status: Completed - Results in logs")
            
        except Exception as e:
            logging.error(f"Workflow execution failed: {e}")
            self.status_label.configure(
                text=f"Status: Error - {str(e)}"
            )

    def cleanup(self):
        """Clean up resources on UI destruction."""
        if self.orchestrator and hasattr(self.orchestrator, 'stop'):
            try:
                self.orchestrator.stop()
            except Exception as e:
                logging.error(f"Failed to stop orchestrator during cleanup: {e}")
        
        # Clear orchestrator reference
        self.orchestrator = None

    def _create_agent_panel(self, frame):
        # Agent configuration frame
        outer_frame = ctk.CTkFrame(frame)
        outer_frame.pack(padx=5, pady=(10, 40))
        config_frame = ctk.CTkFrame(outer_frame)
        config_frame.pack()

        # Add frame to tracked agent panels
        self.current_agent_panels.append(outer_frame)

        # Model selection
        self.model_selection_var = ctk.StringVar(value=self.available_models[0])
        
        model_label = ctk.CTkLabel(
            config_frame,
            text="Select AI Model:",
            font=self.default_font,
        )
        model_label.grid(row=0, column=0, sticky="w", padx=20, pady=(20, 5))

        # Simple dropdown: just pick one primary model since CrewAI manages multiple internally
        self.model_optionmenu = ctk.CTkOptionMenu(
            config_frame,
            variable=self.model_selection_var,
            values=self.available_models,
            font=self.default_font,
        )
        self.model_optionmenu.grid(row=0, column=1, sticky="e", padx=20, pady=(20, 5))

        # Tools toggle - enable/disable search tools
        # self.tools_enabled = ctk.BooleanVar(value=True)
        # tools_switch_label = ctk.CTkLabel(
        #     config_frame,
        #     text="Enable Search Tools (Serper + DirectorySearch):",
        #     font=self.default_font,
        # )
        # tools_switch_label.grid(row=1, column=0, sticky="w", padx=5, pady=2)

        # self.tools_switch = ctk.CTkSwitch(
        #     config_frame,
        #     text="",  # Label handled by switch itself
        #     variable=self.tools_enabled,
        #     font=self.default_font,
        # )
        # self.tools_switch.grid(row=1, column=1, padx=5, pady=2)

        # Tool toggle error label (for validation if needed)
        self.tools_error_label = ctk.CTkLabel(
            config_frame,
            text="",
            font=self.default_font,
            text_color="red",
        )

        # # Initial Research Task section
        # agent_task_frame = ctk.CTkFrame(config_frame)
        # agent_task_frame.grid(row=2, columnspan=2, sticky="we", padx=5, pady=2)

        

        # Add subsequent agents section
        # self.add_agent_var = ctk.BooleanVar(value=True)
        
        # add_agent_label = ctk.CTkLabel(
        #     config_frame,
        #     text="Add Subsequent Agent:",
        #     font=self.default_font,
        # )
        # add_agent_label.grid(row=3, column=0, sticky="w", padx=5, pady=2)

        # self.add_agent_switch = ctk.CTkSwitch(
        #     config_frame,
        #     variable=self.add_agent_var,
        #     font=self.default_font,
        # )
        # self.add_agent_switch.grid(row=3, column=1, sticky="e", padx=5, pady=2)

        # Agent role configuration (appears if add agent is on)
        self.agent_role_var = ctk.StringVar(value=self.orchestrator.get_agent_roles()[0])
        self.agent_goal_var = ctk.StringVar()
        
        role_label = ctk.CTkLabel(
            config_frame,
            text="Agent Role:",
            font=self.default_font,
        )
        role_label.grid(row=4, column=0, sticky="w", padx=20, pady=5)

        self.agent_role_optionmenu = ctk.CTkOptionMenu(
            config_frame,
            variable=self.agent_role_var,
            values=self.orchestrator.get_agent_roles(),
            font=self.default_font,
        )
        self.agent_role_optionmenu.grid(row=4, column=1, sticky="e", padx=20, pady=5)

        goal_label = ctk.CTkLabel(
            config_frame,
            text="Agent Goal:",
            font=self.default_font,
        )
        goal_label.grid(row=5, column=0, sticky="w", padx=20, pady=5)

        self.agent_goal_entry = ctk.CTkEntry(
            config_frame,
            textvariable=self.agent_goal_var,
            placeholder_text="e.g., 'identify any factual errors'",
            font=self.default_font,
        )
        self.agent_goal_entry.grid(row=6, columnspan=2, sticky="we", padx=20, pady=5)

        # Status label (shows current workflow state)
        self.status_label = ctk.CTkLabel(
            config_frame,
            text="Status: Idle",
            font=self.default_font,
            wraplength=400,
        )
        self.status_label.grid(row=7, columnspan=2, padx=20, pady=(5,20))

    def _on_num_agents_changed(self, *args):
        delta = self.num_agents.get() - self.prev_num_agents

        if delta > 0:
            self._create_agent_panel(self.orchestrator_frame)
            logging.info("New agent panel created")
        elif delta < 0:
            logging.info("Removing agent panel")
            removed_panel = self.current_agent_panels.pop()
            removed_panel.grid_forget()

        self.prev_num_agents = self.num_agents.get()