import os
import pytest
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def test_openai_api_key_configured():
    """Test that OpenAI API key is configured and valid."""
    api_key = os.getenv("OPENAI_API_KEY", "")

    # Check if configured
    assert api_key, "OPENAI_API_KEY not set in .env"
    assert api_key != "your_openai_api_key_here", "OPENAI_API_KEY is still set to default value"
    assert api_key.startswith("sk-"), "OPENAI_API_KEY should start with 'sk-'"

    # Test actual API connection
    try:
        import openai

        client = openai.OpenAI(api_key=api_key)

        # Make a minimal API call to verify the key works
        response = client.models.list()

        # If we get here, the API key is valid
        assert response is not None, "OpenAI API returned empty response"

    except openai.AuthenticationError as e:
        pytest.fail(f"OpenAI API authentication failed: {e}")
    except openai.APIError as e:
        pytest.fail(f"OpenAI API error: {e}")
    except Exception as e:
        pytest.fail(f"Unexpected error testing OpenAI API: {e}")


def test_mongodb_connection():
    """Test MongoDB connection if configured."""
    mongo_uri = os.getenv("MONGO_CONNECTION_STRING", "")

    if not mongo_uri:
        pytest.skip("MONGO_CONNECTION_STRING not set, skipping MongoDB test")

    from src.db.mongo_client import Database

    # Initialize and test connection
    Database.init_client(mongo_uri)
    result = Database.client().admin.command("ping")

    assert int(result["ok"]) == 1, "MongoDB ping failed"

    # Cleanup
    Database.close_client()
