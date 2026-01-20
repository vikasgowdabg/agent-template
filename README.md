# Agent Template

Minimal FastAPI-based agent template using deepagents.

## Features

- FastAPI server with `/invoke` and `/health` endpoints
- deepagents integration
- MongoDB support (optional)
- Environment-based configuration
- Poetry dependency management
- All dependencies pre-configured in `pyproject.toml`

## Quick Start

### 1. Create New Repo from Template

Go to this repository on GitHub and click **"Use this template"** → **"Create a new repository"**

**Important:** Name your repo following the pattern: `agent-<name>`
- ✅ Valid: `agent-charlie`, `agent-orchestrator`, `agent-tool-1`
- ❌ Invalid: `charlie`, `my-agent`, `Agent-charlie`

### 2. Clone and Initial Setup

```bash
git clone <your-new-repo-url>
cd agent-<name>

# Run setup - it will prompt for:
# - Project name (must start with agent-)
# - Description
# - Author (optional, uses git config by default)
bin/setup

# This script automatically:
# - Updates pyproject.toml with your project details
# - Runs poetry install (installs all dependencies)
# - Creates .env file
# - Sets up pre-commit hooks
```

### 3. Configure API Key

```bash
# Edit .env and add your OpenAI API key
nano .env  # Set OPENAI_API_KEY=sk-your-actual-key
```

**Initial setup is now complete!** You have a working agent with default configuration.

### 4. Customize Your Agent

Now iterate on your agent:

```bash
# A. Add tools in src/tools/
# Create one tool per file (e.g., src/tools/weather.py)

# B. Update system prompt
nano src/agent/system_prompt.txt
# Define your agent's role, available tools, and behavior

# C. Register tools in agent factory
nano src/agent/agent_factory.py
# Import and add your tools to the get_tools() function

# D. Test your agent
bin/run  # Start server
curl -X POST http://localhost:8000/invoke \
  -H "Content-Type: application/json" \
  -d '{"query": "Test your agent here"}'

# E. Iterate
# Test with different queries, refine system prompt and tools
# Repeat until you get accurate responses
```

## Creating an Agent

### 1. Initial Setup

Follow the **Quick Start** section above. After running `bin/setup`, you'll have:
- Poetry environment with all dependencies installed
- Project name configured in `pyproject.toml`
- `.env` file created (add your `OPENAI_API_KEY`)
- Pre-commit hooks installed

**Note:** `bin/setup` already runs `poetry install` - no need to run it separately.

### 2. Add Tools (if needed)

**Convention: One tool per file.**

Create tool in `src/tools/`:
```python
# src/tools/weather.py
def get_weather(city: str) -> str:
    """Get current weather for a city."""
    return f"Weather in {city}: Sunny, 72°F"
```

Test it:
```python
from src.tools.weather import get_weather
print(get_weather("London"))
```

### 3. Update System Prompt

Edit `src/agent/system_prompt.txt`:
```text
You are a weather assistant.

Available tools:
- get_weather(city: str) - Get current weather for any city

Provide accurate weather information.
```

### 4. Add Tools to Agent Factory

Edit `src/agent/agent_factory.py` - register your tools in the `get_tools()` function:
```python
def get_tools() -> List[Callable]:
    """Add your tools to this function."""
    from src.tools.weather import get_weather

    tools: List[Callable] = [
        get_weather,  # <-- Add your tools here
    ]

    return tools
```

### 5. Add Configuration (optional)

Edit `src/config.py`:
```python
class Settings(BaseSettings):
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    YOUR_API_KEY: str = os.getenv("YOUR_API_KEY", "")
    YOUR_SETTING: str = os.getenv("YOUR_SETTING", "default")
```

Add to `.env`:
```bash
# Custom Configuration
YOUR_API_KEY=abc123
YOUR_SETTING=custom_value
```

### 6. Add MongoDB (optional)

Add to `.env`:
```bash
MONGO_CONNECTION_STRING=mongodb://localhost:27017
```

Use in code:
```python
from src.db.mongo_client import Database
collection = Database.get_collection("users", "my_db")
collection.insert_one({"name": "John"})
```

If not using MongoDB, delete `src/db/` folder.

### 7. Add Dependencies (if needed)

```bash
# Install a new dependency
poetry add <DEPENDENCY>              # e.g., poetry add requests
poetry add <DEPENDENCY>@<VERSION>    # e.g., poetry add requests@2.31.0

# Install a dev dependency
poetry add --dev <DEPENDENCY>

# Remove a dependency
poetry remove <DEPENDENCY>
```

## Development Workflow

### Iterative Development Process

1. **Start with default agent** - After `bin/setup`, you have a working agent
2. **Define requirements** - What should your agent do? What tools does it need?
3. **Add tools** - Create tool functions in `src/tools/` (one per file)
4. **Update system prompt** - Tell the agent about its role and available tools
5. **Register tools** - Import and add tools in `src/agent/agent_factory.py`
6. **Test** - Run `bin/run` and test with various queries
7. **Iterate** - Refine system prompt and tools based on test results
8. **Repeat** - Continue testing and improving until responses are accurate

**Tip:** Test frequently with real queries to catch issues early. The system prompt is crucial - be specific about when and how to use each tool.

## Project Structure

```
.
├── main.py                      # FastAPI app
├── pyproject.toml               # Dependencies
├── .env                         # Environment variables
├── bin/
│   ├── setup                    # Setup script
│   ├── run                      # Run server
│   └── test                     # Run tests
├── src/
│   ├── agent/
│   │   ├── agent_factory.py     # Agent initialization
│   │   └── system_prompt.txt    # Agent prompt
│   ├── config.py                # Settings
│   ├── db/
│   │   └── mongo_client.py      # MongoDB (optional)
│   ├── tools/
│   │   └── example_tool.py      # Tool examples
│   └── utils/
│       └── logger.py            # Logging
└── tests/
    ├── test_api.py              # API & health tests (10 test queries)
    └── test_connections.py      # MongoDB & OpenAI API key tests
```

## Development Commands

```bash
bin/setup     # Initial setup (run once when creating new agent)
              # - Prompts for project name (agent-*), description, author
              # - Updates pyproject.toml
              # - Runs poetry install automatically
              # - Creates .env file
              # - Installs pre-commit hooks

bin/run       # Start FastAPI server on http://localhost:8000

bin/test      # Run all tests (pytest)
```

**Note:** You don't need to run `poetry install` or `poetry init` - `bin/setup` handles everything.

## Testing

Run all tests:
```bash
bin/test
```

Test execution order:
1. **Health check** - Validates API is responding
2. **10 test queries** - Tests agent with different queries
3. **Connection tests** - MongoDB connection + OpenAI API key validation (makes real API call)

**Test files:**
- `tests/test_api.py` - Health endpoint + 10 agent queries
- `tests/test_connections.py` - MongoDB connection + OpenAI API authentication test

### Adding Custom Tests

Create test files in `tests/`:
```python
# tests/test_tools.py
from src.tools.weather import get_weather

def test_weather_tool():
    result = get_weather("London")
    assert "Weather" in result
```

Customize test queries in `tests/test_api.py`:
```python
TEST_QUERIES = [
    "What is 2+2?",
    "Your custom query here",
    # Add more queries...
]
```

Run specific tests:
```bash
poetry run pytest tests/test_tools.py                     # Run specific file
poetry run pytest tests/test_api.py::TestHealthFirst      # Run health tests only
poetry run pytest --cov=src                               # With coverage
```

## Troubleshooting

- **Poetry not found**: `pip install poetry` or `brew install poetry` (macOS)
- **Project name rejected**: Must follow `agent-<name>` pattern (lowercase, hyphens/underscores only)
- **Author format invalid**: Use format `Name <email@example.com>` or just press Enter for default
- **Import errors**: Run `bin/setup` again (it runs `poetry install` automatically)
- **Agent not responding**: Check `OPENAI_API_KEY` in `.env` file
- **MongoDB errors**: Optional - leave `MONGO_CONNECTION_STRING` empty if not using
- **Tests failing**: Run `bin/test` to see which test failed
- **Pre-commit hooks failing**: Commits are automatically checked for code quality - fix the issues or run `git commit --no-verify` (not recommended)
