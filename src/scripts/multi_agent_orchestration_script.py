from enum import Enum
from typing import List, Callable, Optional
import crewai_tools as CAITools
from langchain_openai import ChatOpenAI
import crewai
import logging
import threading
import time
import json

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)

class AgentRole(Enum):
    """Agent role types"""
    RESEARCHER = "Researcher"       # Researches and finds information
    FACT_CHECKER = "Fact Checker"     # Verifies facts and corrects errors
    SYNTHESIZER = "Synthesizer"      # Combines findings into conclusions
    PLANNER = "Planner"          # Plans next steps
    MONITOR = "Monitor"         # Monitors system health

class MultiAgentOrchestrationScript:

    def __init__(self, enable_tools: bool = True):
        self.enable_tools = enable_tools
        self.agent_threads: dict[str, threading.Thread] = {}
        self.task_status: dict[str, str] = {}
        self.workflow_history: List[dict] = []
        self.tools: Optional[List] = None
        self.models: List[str] = [
            "qwen3.5-9b-deepseek-v4-flash",
            "qwen3.5-4b",
            "qwen/qwen3.5-9b",
            "qwen2.5-coder-1.5b-instruct",
        ]
        self.agent_roles = AgentRole

        if enable_tools:
            try:
                self.tools = [
                    CAITools.SerperDevTool(),
                ]
                logging.debug(f"Initialized {len(self.tools)} tools")
            except Exception as e:
                logging.error(f"Failed to initialize tools: {e}")
                self.enable_tools = False

    def _connect_llm_lmstudio(self):
        llm_lmstudio = ChatOpenAI(
            openai_api_base="http://127.0.0.1:1234/v1",
            openai_api_key="",
            model_name=self.models[0]
        )
        return llm_lmstudio

    def _create_agent(
        self,
        role: str,
        goal: str,
        backstory: str,
        model: Optional[str] = None 
    ) -> crewai.Agent:
        agent_model = model or self.models[0]
        logging.debug(f"Agent created using model {agent_model}")

        return crewai.Agent(
            role=role,
            goal=goal,
            backstory=backstory,
            allow_delegation=False,  # Agents don't delegate to each other directly
            llm=self._get_llm(agent_model),
            tools=self.tools if self.enable_tools else None,
        )

    def _create_task(
        self, 
        description: str, 
        expected_output: str = "well-reasoned answer"
    ) -> crewai.Task:
        """Create a CrewAI task with specified parameters."""
        
        return crewai.Task(
            description=description,
            expected_output=expected_output,
        )

    def _get_llm(self, model_name: str, temperature: float = 0.3, max_tokens: int = 4096) -> crewai.LLM:
        """Get LLM instance from model name string."""
        try:
            # Map model names to CrewAI's supported formats
            model_map = {
                "gpt-4o": "gpt-4o",  # OpenAI format (CrewAI auto-detects)
                "claude-3-5-sonnet": "claude-3-5-sonnet",  # Anthropic format
                "llama-3.1-70b": "meta-llama/llama-3.1-70b-instruct",  # Groq
                "qwen3.5-9b-deepseek-v4-flash": "qwen3.5-9b-deepseek-v4-flash",
                "qwen/qwen3.5-9b": "qwen/qwen3.5-9b",
                "qwen2.5-coder-1.5b-instruct": "qwen2.5-coder-1.5b-instruct",
            }
            
            mapped_model = model_map.get(model_name, model_name)
            return crewai.LLM(
                llm=mapped_model,
                temperature=temperature,  # Moderate creativity for research tasks
                max_tokens=max_tokens
            )
        except Exception as e:
            logging.error(f"Failed to create LLM for {model_name}: {e}")
            raise

    def _create_workflow(
        self,
        initial_task: crewai.Task,
        subsequent_tasks: List[crewai.Task],
    ) -> crewai.Crew:

        all_tasks = [initial_task] + subsequent_tasks

        return crewai.Crew(
            agents=[self._create_agent(role=task.role, goal=task.goal, backstory=task.backstory, model=task.model)
                for task in all_tasks],
            tasks=all_tasks,
            verbose=True,
        )

    def get_models(self) -> List[str]:
        return self.models

    def get_agent_roles(self) -> List:
        return [role.value for role in self.agent_roles]

    def start(self) -> None:
        """Start the orchestrator (no-op - used for threading pattern)."""
        self.is_running = True
        
    def stop(self) -> None:
        """Stop the orchestrator and cleanup resources."""
        self.is_running = False
    
    @property
    def is_running(self) -> bool:
        return hasattr(self, '_running') and self._running

    @is_running.setter
    def is_running(self, value: bool):
        # Create thread-safe flag
        import threading
        
        lock = threading.Lock()
        
        with lock:
            if not hasattr(self, '_running'):
                self._running = False
                self._lock = lock
            
            self._running = value
    
    def execute_workflow(
        self, 
        initial_task_description: str, 
        subsequent_tasks: List[dict], 
        execution_mode: str = "sequential"
    ) -> dict:
        """
        Execute a multi-agent workflow.

        Args:
            initial_task_description: Description for the first task (Researcher)
            subsequent_tasks: List of dicts with 'role', 'goal', 'backstory' keys
            execution_mode: How to execute tasks ("sequential" or "parallel")

        Returns:
            Dictionary containing results from each agent and workflow history
        """
        
        # Define sequential task chain with roles
        initial_task = self._create_task(
            description=initial_task_description,
            expected_output="comprehensive research findings"
        )
        
        # Create subsequent tasks based on input
        created_tasks: List[crewai.Task] = []
        for i, task_config in enumerate(subsequent_tasks):
            role = task_config.get('role', f'Agent-{i+1}')
            goal = task_config.get('goal', '')
            backstory = task_config.get('backstory', '')
            
            task = self._create_task(
                description=f"{role} should {goal}",
                expected_output="fact-checked and corrected response" if i > 0 else "verified research findings"
            )
            created_tasks.append(task)
        
        # Build workflow with agents and tasks
        all_agents_and_tasks = [initial_task] + created_tasks
        
        # Create the Crew (orchestrator) - uses sequential execution by default
        crew_instance = self._create_workflow(
            initial_task=initial_task,
            subsequent_tasks=created_tasks
        )

        try:
            # Execute workflow and capture results
            result = crew_instance.kickoff()  # Run all tasks
            
            # Collect output from each task (agent)
            results = {}
            for i, task in enumerate(all_agents_and_tasks):
                role_name = f"{i+1}. {task.description.split()[0]}" if task.description else f"Agent-{i+1}"
                
                # Extract result from task execution (CrewAI stores output internally)
                results[role_name] = f"Task completed: {result}"  # Simplified for template

            self.workflow_history.append({
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                'execution_mode': execution_mode,
                'results': results,
            })
            
        except Exception as e:
            logging.error(f"Workflow execution failed: {e}")
            self.workflow_history.append({
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                'error': str(e),
            })

        return results


# Example usage pattern (not included in file):
# orchestrator = AgentOrchestrator(models=["gpt-4o", "claude-3-5-sonnet"])
# results = orchestrator.execute_workflow(
#     initial_task_description="Research the latest AI trends for 2024",
#     subsequent_tasks=[
#         {'role': 'Fact Checker', 'goal': 'verify research claims'},
#         {'role': 'Corrector', 'goal': 'fix any inaccuracies found'},
#     ]
# )