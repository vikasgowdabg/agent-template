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

```bash
# 1. Clone and setup
git clone <repo-url> my-agent
cd my-agent
bin/setup "my-agent" "My agent description" "Your Name <you@example.com>"

# 2. Add your OpenAI API key
nano .env  # Set OPENAI_API_KEY=sk-your-actual-key

# 3. Customize system prompt
nano src/agent/system_prompt.txt

# 4. Run
bin/run

# 5. Test
curl -X POST http://localhost:8000/invoke \
  -H "Content-Type: application/json" \
  -d '{"query": "Hello!"}'
```

## Creating an Agent

### 1. Setup Project

```bash
# This installs all dependencies from pyproject.toml automatically
bin/setup "project-name" "Description" "Author Name"
nano .env  # Add OPENAI_API_KEY
```

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

Edit `src/agent/agent_factory.py`:
```python
from deepagents import Agent
from pathlib import Path
from src.tools.weather import get_weather

SYSTEM_PROMPT_FILE = Path(__file__).parent / "system_prompt.txt"

def create_agent() -> Agent:
    system_prompt = SYSTEM_PROMPT_FILE.read_text(encoding="utf-8")
    tools = [get_weather]  # Add your tools here
    agent = Agent(system_prompt=system_prompt, tools=tools)
    return agent

agent_instance = create_agent()
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
bin/run       # Start server
bin/test      # Run all tests
```

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

- **Poetry not found**: `pip install poetry`
- **Import errors**: `poetry install`
- **Agent not responding**: Check `OPENAI_API_KEY` in `.env`
- **MongoDB errors**: Optional - leave empty if not using
- **Tests failing**: Run `bin/test` to see which test failed
