from deepagents import create_deep_agent
from pathlib import Path
from typing import List, Callable, Any
import json
from langchain_openai import ChatOpenAI
from src import Settings


OPENAI_MODEL="gpt-4o-mini"
SYSTEM_PROMPT_FILE = Path(__file__).parent / "system_prompt.txt"


def get_tools() -> List[Callable]:
    """
    Returns the list of tools available to the agent.

    Add your custom tools here by importing them from src.tools.
    Tools are automatically included along with deepagents built-in tools:
    - write_todos: Planning and task decomposition
    - File system: ls, read_file, write_file, edit_file, glob, grep
    - task: Subagent spawning

    Returns:
        List of callable tool functions
    """
    # Import your custom tools here
    # from src.tools.example_tool import get_current_time

    # Add your custom tools to this list
    tools: List[Callable] = [
        # get_current_time,  # Uncomment when you have custom tools
    ]

    return tools


def load_system_prompt() -> str:
    """
    Loads the base system prompt from file.

    Returns:
        System prompt text

    Raises:
        FileNotFoundError: If system_prompt.txt doesn't exist
        ValueError: If system prompt is empty
    """
    if not SYSTEM_PROMPT_FILE.exists():
        raise FileNotFoundError(f"System prompt file not found: {SYSTEM_PROMPT_FILE}")

    prompt = SYSTEM_PROMPT_FILE.read_text(encoding="utf-8").strip()

    if not prompt:
        raise ValueError("System prompt cannot be empty")

    return prompt


def create_agent(user_prompt: str) -> dict[str, Any]:
    """
    Creates and invokes a deep agent, returning structured response.

    Deep agents are LangGraph graphs with built-in capabilities for:
    - Planning and task decomposition (write_todos tool)
    - File system access (ls, read_file, write_file, etc.)
    - Subagent spawning (task tool)

    Custom tools are defined in get_tools() function in this module.
    System prompt is loaded from system_prompt.txt.

    Args:
        user_prompt: User's prompt/query

    Returns:
        Dict with 'result' and 'metadata' keys containing structured response

    Raises:
        FileNotFoundError: If system_prompt.txt doesn't exist
        ValueError: If system prompt is empty
    """
    # Load configuration
    system_prompt = load_system_prompt()
    tools = get_tools()
    
    # Initialize OpenAI model
    settings = Settings()
    llm = ChatOpenAI(
        model=OPENAI_MODEL,
        api_key=settings.OPENAI_API_KEY,
        temperature=0.1,
    )

    # Create deep agent with OpenAI model - returns a LangGraph graph
    agent = create_deep_agent(system_prompt=system_prompt, tools=tools, model=llm)

    # Prepare messages in the format deepagents expects
    messages = [{"role": "user", "content": user_prompt}]

    # Invoke agent
    agent_result = agent.invoke({"messages": messages})

    # Extract messages and build response
    result_messages = agent_result.get("messages", [])
    last_message = result_messages[-1] if result_messages else None

    # Extract content from last message
    content_str = ""
    if last_message:
        content_str = (
            last_message.content if hasattr(last_message, "content") else str(last_message)
        )

    # Extract tool calls from all messages
    tools_called = []
    for msg in result_messages:
        # Check if message has tool_calls attribute (AIMessage with tool calls)
        if hasattr(msg, "tool_calls") and msg.tool_calls:
            for tool_call in msg.tool_calls:
                tools_called.append(
                    {
                        "name": tool_call.get("name", "unknown"),
                        "args": tool_call.get("args", {}),
                    }
                )
        # Check if message is a ToolMessage (tool execution result)
        elif hasattr(msg, "name") and msg.__class__.__name__ == "ToolMessage":
            # Already captured from tool_calls above
            pass

    # Parse content as JSON dict, fallback to raw string in dict if parsing fails
    content_dict: dict[str, Any]
    try:
        parsed = json.loads(content_str)
        # Ensure it's a dict
        if isinstance(parsed, dict):
            content_dict = parsed
        else:
            content_dict = {"response": parsed}
    except (json.JSONDecodeError, TypeError):
        # If not valid JSON, wrap in dict
        content_dict = {"response": content_str}

    # Build structured JSON response with result and metadata
    return {
        "result": content_dict,
        "metadata": {"tools_called": tools_called, "message_count": len(result_messages)},
    }
