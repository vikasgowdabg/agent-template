from deepagents import Agent
from pathlib import Path

# Path to system prompt file
SYSTEM_PROMPT_FILE = Path(__file__).parent / "system_prompt.txt"


def create_agent() -> Agent:
    """
    Creates a deepagents Agent instance.
    
    The agent is configured with:
    - system_prompt: loaded from system_prompt.txt
    - tools: empty list (add your custom tools here)
    
    Returns:
        Configured Agent instance
    """
    # Load system prompt from file
    system_prompt = SYSTEM_PROMPT_FILE.read_text(encoding="utf-8")
    
    # Define tools (empty for now - add your custom tools here)
    tools = []
    
    # Create and return agent
    agent = Agent(
        system_prompt=system_prompt,
        tools=tools
    )
    
    return agent


# Singleton agent instance - created once at import
agent_instance = create_agent()
