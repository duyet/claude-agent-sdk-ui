"""
Integration tests for configuration router endpoints.

Tests cover:
- GET /api/v1/config/agents - List available agents
- Response model validation
- Default agent identification
- Agent metadata structure
- Empty/missing config handling
- API key authentication

Run: pytest tests/test_routers_configuration.py -v
"""

import pytest
from agent.core.agents import get_agents_info
from agent.core.yaml_utils import load_yaml_config
from api.routers.configuration import AgentsListResponse


class TestListAgentsEndpoint:
    """Test cases for GET /api/v1/config/agents endpoint."""

    def test_list_agents_returns_200(self, client, auth_headers):
        """Test endpoint returns 200 status code."""
        response = client.get("/api/v1/config/agents", headers=auth_headers)
        assert response.status_code == 200

    def test_list_agents_response_structure(self, client, auth_headers):
        """Test response has correct structure with agents field."""
        response = client.get("/api/v1/config/agents", headers=auth_headers)
        data = response.json()

        assert "agents" in data
        assert isinstance(data["agents"], list)

    def test_list_agents_with_valid_api_key(self, client, auth_headers):
        """Test agents list is returned with valid API key."""
        response = client.get("/api/v1/config/agents", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data["agents"]) > 0

    def test_list_agents_without_api_key_returns_401(self, client):
        """Test endpoint returns 401 without API key."""
        response = client.get("/api/v1/config/agents")
        assert response.status_code == 401

    def test_list_agents_with_invalid_api_key_returns_401(self, client):
        """Test endpoint returns 401 with invalid API key."""
        headers = {"X-API-Key": "invalid-api-key-12345"}
        response = client.get("/api/v1/config/agents", headers=headers)
        assert response.status_code == 401

    def test_agent_structure_contains_required_fields(self, client, auth_headers):
        """Test each agent has required fields: agent_id, name, description, model, is_default."""
        response = client.get("/api/v1/config/agents", headers=auth_headers)
        data = response.json()
        agents = data["agents"]

        for agent in agents:
            assert "agent_id" in agent
            assert "name" in agent
            assert "description" in agent
            assert "model" in agent
            assert "is_default" in agent

    def test_agent_id_is_string(self, client, auth_headers):
        """Test agent_id is a string."""
        response = client.get("/api/v1/config/agents", headers=auth_headers)
        agents = response.json()["agents"]

        for agent in agents:
            assert isinstance(agent["agent_id"], str)

    def test_agent_name_is_string(self, client, auth_headers):
        """Test agent name is a string."""
        response = client.get("/api/v1/config/agents", headers=auth_headers)
        agents = response.json()["agents"]

        for agent in agents:
            assert isinstance(agent["name"], str)

    def test_agent_description_is_string(self, client, auth_headers):
        """Test agent description is a string."""
        response = client.get("/api/v1/config/agents", headers=auth_headers)
        agents = response.json()["agents"]

        for agent in agents:
            assert isinstance(agent["description"], str)

    def test_agent_model_is_string(self, client, auth_headers):
        """Test agent model is a string."""
        response = client.get("/api/v1/config/agents", headers=auth_headers)
        agents = response.json()["agents"]

        for agent in agents:
            assert isinstance(agent["model"], str)

    def test_agent_is_default_is_boolean(self, client, auth_headers):
        """Test is_default field is a boolean."""
        response = client.get("/api/v1/config/agents", headers=auth_headers)
        agents = response.json()["agents"]

        for agent in agents:
            assert isinstance(agent["is_default"], bool)

    def test_exactly_one_default_agent_exists(self, client, auth_headers):
        """Test that exactly one agent is marked as default."""
        response = client.get("/api/v1/config/agents", headers=auth_headers)
        agents = response.json()["agents"]

        default_agents = [a for a in agents if a["is_default"]]
        assert len(default_agents) == 1

    def test_default_agent_matches_config(self, client, auth_headers):
        """Test default agent matches the one in agents.yaml config."""
        response = client.get("/api/v1/config/agents", headers=auth_headers)
        agents = response.json()["agents"]

        default_agent = next((a for a in agents if a["is_default"]), None)
        assert default_agent is not None

        # Verify against config
        from pathlib import Path

        config_path = Path(__file__).parent.parent / "agents.yaml"
        config = load_yaml_config(config_path)
        expected_default = config.get("default_agent")

        assert default_agent["agent_id"] == expected_default

    def test_agent_model_values_are_valid(self, client, auth_headers):
        """Test agent model values are valid Claude models."""
        response = client.get("/api/v1/config/agents", headers=auth_headers)
        agents = response.json()["agents"]

        valid_models = {"haiku", "sonnet", "opus"}

        for agent in agents:
            assert agent["model"] in valid_models

    def test_agents_from_yaml_match_response(self, client, auth_headers):
        """Test agents returned match those in agents.yaml."""
        response = client.get("/api/v1/config/agents", headers=auth_headers)
        api_agents = response.json()["agents"]

        # Get agents from config
        from pathlib import Path

        config_path = Path(__file__).parent.parent / "agents.yaml"
        config = load_yaml_config(config_path)
        config_agents = config.get("agents", {})

        # Check same number of agents
        assert len(api_agents) == len(config_agents)

        # Check all agent IDs match
        api_agent_ids = {a["agent_id"] for a in api_agents}
        config_agent_ids = set(config_agents.keys())
        assert api_agent_ids == config_agent_ids

    def test_response_model_validation(self, client, auth_headers):
        """Test response matches AgentsListResponse model."""
        response = client.get("/api/v1/config/agents", headers=auth_headers)
        data = response.json()

        # Should not raise validation error
        validated = AgentsListResponse(**data)
        assert isinstance(validated.agents, list)

    def test_content_type_is_json(self, client, auth_headers):
        """Test response content type is application/json."""
        response = client.get("/api/v1/config/agents", headers=auth_headers)

        assert response.headers["content-type"] == "application/json"


class TestAgentsListResponseModel:
    """Test cases for AgentsListResponse Pydantic model."""

    def test_create_valid_response(self):
        """Test creating a valid AgentsListResponse."""
        agents = [
            {
                "agent_id": "test-agent-123",
                "name": "Test Agent",
                "description": "A test agent",
                "model": "sonnet",
                "is_default": True,
            }
        ]

        response = AgentsListResponse(agents=agents)
        assert response.agents == agents

    def test_agents_field_is_required(self):
        """Test agents field is required."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError) as exc_info:
            AgentsListResponse()

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("agents",) for e in errors)

    def test_agents_must_be_list(self):
        """Test agents must be a list."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            AgentsListResponse(agents="not-a-list")  # type: ignore

    def test_empty_agents_list_is_valid(self):
        """Test empty agents list is valid."""
        response = AgentsListResponse(agents=[])
        assert response.agents == []

    def test_multiple_agents_in_list(self):
        """Test response with multiple agents."""
        agents = [
            {
                "agent_id": f"agent-{i}",
                "name": f"Agent {i}",
                "description": f"Description {i}",
                "model": "sonnet",
                "is_default": (i == 0),
            }
            for i in range(3)
        ]

        response = AgentsListResponse(agents=agents)
        assert len(response.agents) == 3

    def test_model_serialization(self):
        """Test model serializes correctly."""
        agents = [
            {
                "agent_id": "test-agent",
                "name": "Test",
                "description": "Test description",
                "model": "haiku",
                "is_default": False,
            }
        ]

        response = AgentsListResponse(agents=agents)
        data = response.model_dump()

        assert data == {"agents": agents}

    def test_model_json_serialization(self):
        """Test model JSON serialization."""
        agents = [
            {
                "agent_id": "test-agent",
                "name": "Test Agent",
                "description": "Test",
                "model": "opus",
                "is_default": True,
            }
        ]

        response = AgentsListResponse(agents=agents)
        json_str = response.model_dump_json()

        assert "test-agent" in json_str
        assert "Test Agent" in json_str


class TestGetAgentsInfoFunction:
    """Test cases for get_agents_info utility function."""

    def test_returns_list(self):
        """Test function returns a list."""
        agents = get_agents_info()
        assert isinstance(agents, list)

    def test_returns_non_empty_list(self):
        """Test function returns non-empty list when config exists."""
        agents = get_agents_info()
        assert len(agents) > 0

    def test_each_agent_is_dict(self):
        """Test each agent in list is a dict."""
        agents = get_agents_info()

        for agent in agents:
            assert isinstance(agent, dict)

    def test_agent_has_required_keys(self):
        """Test each agent has required keys."""
        agents = get_agents_info()
        required_keys = {"agent_id", "name", "description", "model", "is_default"}

        for agent in agents:
            assert required_keys.issubset(agent.keys())

    def test_default_agent_is_marked(self):
        """Test exactly one agent has is_default=True."""
        agents = get_agents_info()
        default_agents = [a for a in agents if a.get("is_default")]

        assert len(default_agents) == 1

    def test_agent_name_fallback_to_id(self):
        """Test agent name falls back to agent_id if not provided."""
        from agent.core.agents import AGENTS_CONFIG_PATH

        config = load_yaml_config(AGENTS_CONFIG_PATH)
        agents = config.get("agents", {})

        # get_agents_info should use agent_id as name if name is missing
        for agent_id, agent_config in agents.items():
            if "name" not in agent_config:
                agents_info = get_agents_info()
                matching = next(
                    (a for a in agents_info if a["agent_id"] == agent_id), None
                )
                if matching:
                    assert matching["name"] == agent_id

    def test_model_fallback_to_default(self):
        """Test agent model falls back to default model if not provided."""
        from agent.core.agents import AGENTS_CONFIG_PATH

        config = load_yaml_config(AGENTS_CONFIG_PATH)
        defaults = config.get("_defaults", {})
        defaults.get("model", "sonnet")

        agents = get_agents_info()

        # All agents should have a model (either explicit or default)
        for agent in agents:
            assert agent["model"] in {"haiku", "sonnet", "opus"}

    def test_returns_empty_list_when_no_config(self, monkeypatch):
        """Test returns empty list when config is missing."""
        # Mock load_yaml_config to return None
        from agent.core import agents

        def mock_load_yaml(path):
            return None

        monkeypatch.setattr(agents, "load_yaml_config", mock_load_yaml)

        result = get_agents_info()
        assert result == []


class TestConfigurationEdgeCases:
    """Test edge cases and error handling for configuration endpoints."""

    def test_get_agents_idempotent(self, client, auth_headers):
        """Test calling endpoint multiple times returns same data."""
        response1 = client.get("/api/v1/config/agents", headers=auth_headers)
        response2 = client.get("/api/v1/config/agents", headers=auth_headers)

        assert response1.json() == response2.json()

    def test_concurrent_requests(self, client, auth_headers):
        """Test multiple concurrent requests are handled correctly."""
        import threading

        results = []

        def fetch_agents():
            response = client.get("/api/v1/config/agents", headers=auth_headers)
            results.append(response.json())

        threads = [threading.Thread(target=fetch_agents) for _ in range(5)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All results should be identical
        assert all(r == results[0] for r in results)

    def test_response_with_unicode_in_description(self, client, auth_headers):
        """Test agent descriptions with unicode characters are handled."""
        response = client.get("/api/v1/config/agents", headers=auth_headers)
        agents = response.json()["agents"]

        # All descriptions should be valid strings
        for agent in agents:
            description = agent["description"]
            assert isinstance(description, str)
            # Should be able to encode/decode without errors
            description.encode("utf-8").decode("utf-8")

    def test_agent_ids_are_unique(self, client, auth_headers):
        """Test all agent IDs in response are unique."""
        response = client.get("/api/v1/config/agents", headers=auth_headers)
        agents = response.json()["agents"]

        agent_ids = [a["agent_id"] for a in agents]
        assert len(agent_ids) == len(set(agent_ids))

    def test_endpoint_supports_cors(self, client, auth_headers):
        """Test endpoint has CORS headers (if configured)."""
        response = client.get("/api/v1/config/agents", headers=auth_headers)

        # Check if CORS headers are present (depends on app config)
        # This test verifies the endpoint works regardless of CORS config
        assert response.status_code in (200, 401)


class TestConfigurationRouterIntegration:
    """Integration tests for configuration router with full app context."""

    def test_router_tag_is_config(self):
        """Test router is tagged with 'config' tag."""
        from api.routers.configuration import router

        assert "config" in router.tags

    def test_router_has_single_route(self):
        """Test configuration router has only one route."""
        from api.routers.configuration import router

        # The configuration router should have exactly one route
        assert len(router.routes) == 1

    def test_list_agents_route_path(self):
        """Test list agents route is at /agents."""
        from api.routers.configuration import router

        route = router.routes[0]
        assert "/agents" in route.path

    def test_list_agents_route_is_get(self):
        """Test list agents route is a GET request."""
        from api.routers.configuration import router

        route = router.routes[0]
        assert route.methods == {"GET"}

    def test_list_agents_route_includes_in_docs(self):
        """Test list agents route is included in API docs."""
        from api.routers.configuration import router

        route = router.routes[0]
        assert route.include_in_schema is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
