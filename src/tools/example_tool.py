"""
Example tool for the agent.

Convention: One tool per file.
Keep each tool in its own file for better organization.

Delete this file and create your own tools.
"""


def get_current_time() -> str:
    """
    Get the current time in ISO format.

    This is an example tool that the agent can call.
    The docstring is important - it tells the agent what this tool does.

    Returns:
        Current time as ISO format string
    """
    from datetime import datetime

    return datetime.now().isoformat()


# Remember to import and add this tool to the tools list in agent_factory.py
