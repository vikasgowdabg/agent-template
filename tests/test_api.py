import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

# Mock the agent before importing main
with patch("src.agent.agent_factory.create_agent") as mock_create_agent:
    mock_agent = MagicMock()
    mock_agent.run.return_value = "Test response"
    mock_create_agent.return_value = mock_agent

    from main import app

client = TestClient(app)


# Test queries list
TEST_QUERIES = [
    "What is 2+2?",
    "Hello, how are you?",
    "What is the capital of France?",
    "Explain quantum computing in simple terms",
    "What is the weather like today?",
    "Tell me a joke",
    "What is Python?",
    "How do I learn programming?",
    "What is artificial intelligence?",
    "Summarize the benefits of exercise",
]


class TestHealthFirst:
    """Run health check first before other tests."""

    def test_01_health_endpoint(self):
        """Test the health check endpoint - runs first."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_02_health_returns_json(self):
        """Test that health endpoint returns valid JSON."""
        response = client.get("/health")
        assert response.headers["content-type"] == "application/json"
        data = response.json()
        assert isinstance(data, dict)
        assert "status" in data


class TestAgentQueries:
    """Test agent with multiple queries - runs after health check."""

    @patch("main.agent_instance")
    @pytest.mark.parametrize("query", TEST_QUERIES)
    def test_agent_with_queries(self, mock_agent, query):
        """Test agent invocation with different queries."""
        # Mock agent response
        mock_agent.run.return_value = f"Response to: {query}"

        # Make request
        response = client.post("/invoke", json={"query": query})

        # Assertions
        assert response.status_code == 200
        assert "answer" in response.json()
        mock_agent.run.assert_called_with(query)

    @patch("main.agent_instance")
    def test_agent_with_empty_query(self, mock_agent):
        """Test agent with empty query."""
        mock_agent.run.return_value = "I need more information."

        response = client.post("/invoke", json={"query": ""})

        assert response.status_code == 200
        assert "answer" in response.json()

    def test_agent_missing_query_field(self):
        """Test agent endpoint with missing query field."""
        response = client.post("/invoke", json={})

        # Should return validation error
        assert response.status_code == 422
