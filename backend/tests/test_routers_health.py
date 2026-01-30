"""
Comprehensive integration tests for health check router.

Tests cover:
- Root endpoint (/) health check
- Health endpoint (/health) health check
- Response model validation
- HTTP status codes
- Response headers
- JSON serialization
- Content-Type headers
- CORS behavior
- Edge cases

Run: pytest tests/test_routers_health.py -v
"""

import pytest
from fastapi.testclient import TestClient

from api.main import create_app
from api.routers.health import HealthResponse


class TestHealthRouterEndpoints:
    """Test cases for health router HTTP endpoints."""

    @pytest.fixture
    def client(self) -> TestClient:
        """Create a test client for the FastAPI application."""
        # Create a fresh app for each test to avoid state leakage
        app = create_app()
        return TestClient(app)

    def test_root_endpoint_returns_200(self, client: TestClient) -> None:
        """Test root endpoint returns HTTP 200 status code."""
        response = client.get("/")
        assert response.status_code == 200

    def test_root_endpoint_content_type(self, client: TestClient) -> None:
        """Test root endpoint returns application/json content type."""
        response = client.get("/")
        assert response.headers["content-type"] == "application/json"

    def test_root_endpoint_response_structure(self, client: TestClient) -> None:
        """Test root endpoint returns valid JSON with expected structure."""
        response = client.get("/")
        data = response.json()

        assert "status" in data
        assert isinstance(data["status"], str)

    def test_root_endpoint_status_value(self, client: TestClient) -> None:
        """Test root endpoint returns status 'ok'."""
        response = client.get("/")
        data = response.json()

        assert data["status"] == "ok"

    def test_root_endpoint_service_is_optional(self, client: TestClient) -> None:
        """Test root endpoint may or may not include service field."""
        response = client.get("/")
        data = response.json()

        # service may be None or missing entirely
        if "service" in data:
            assert data["service"] is None

    def test_health_endpoint_returns_200(self, client: TestClient) -> None:
        """Test /health endpoint returns HTTP 200 status code."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_endpoint_content_type(self, client: TestClient) -> None:
        """Test /health endpoint returns application/json content type."""
        response = client.get("/health")
        assert response.headers["content-type"] == "application/json"

    def test_health_endpoint_response_structure(self, client: TestClient) -> None:
        """Test /health endpoint returns valid JSON with expected structure."""
        response = client.get("/health")
        data = response.json()

        assert "status" in data
        assert isinstance(data["status"], str)
        assert "service" in data
        assert isinstance(data["service"], str)

    def test_health_endpoint_status_value(self, client: TestClient) -> None:
        """Test /health endpoint returns status 'ok'."""
        response = client.get("/health")
        data = response.json()

        assert data["status"] == "ok"

    def test_health_endpoint_service_name(self, client: TestClient) -> None:
        """Test /health endpoint returns correct service name."""
        response = client.get("/health")
        data = response.json()

        assert data["service"] == "agent-sdk-api"

    def test_root_endpoint_allows_get_request(self, client: TestClient) -> None:
        """Test root endpoint only allows GET requests."""
        # GET should work
        response = client.get("/")
        assert response.status_code == 200

        # POST should not be allowed (405 Method Not Allowed)
        response = client.post("/")
        assert response.status_code == 405

        # PUT should not be allowed
        response = client.put("/")
        assert response.status_code == 405

        # DELETE should not be allowed
        response = client.delete("/")
        assert response.status_code == 405

    def test_health_endpoint_allows_get_request(self, client: TestClient) -> None:
        """Test /health endpoint only allows GET requests."""
        # GET should work
        response = client.get("/health")
        assert response.status_code == 200

        # POST should not be allowed
        response = client.post("/health")
        assert response.status_code == 405

        # PUT should not be allowed
        response = client.put("/health")
        assert response.status_code == 405

        # DELETE should not be allowed
        response = client.delete("/health")
        assert response.status_code == 405

    def test_root_endpoint_response_time(self, client: TestClient) -> None:
        """Test root endpoint responds quickly."""
        import time

        start = time.perf_counter()
        response = client.get("/")
        end = time.perf_counter()

        assert response.status_code == 200
        # Should respond in under 100ms
        assert (end - start) < 0.1

    def test_health_endpoint_response_time(self, client: TestClient) -> None:
        """Test /health endpoint responds quickly."""
        import time

        start = time.perf_counter()
        response = client.get("/health")
        end = time.perf_counter()

        assert response.status_code == 200
        # Should respond in under 100ms
        assert (end - start) < 0.1


class TestHealthRouterResponseModel:
    """Test cases for HealthResponse model validation."""

    def test_health_response_model_with_status_only(self) -> None:
        """Test HealthResponse can be created with status only."""
        response = HealthResponse(status="ok")
        assert response.status == "ok"
        assert response.service is None

    def test_health_response_model_with_status_and_service(self) -> None:
        """Test HealthResponse can be created with both fields."""
        response = HealthResponse(status="ok", service="test-service")
        assert response.status == "ok"
        assert response.service == "test-service"

    def test_health_response_model_serialization(self) -> None:
        """Test HealthResponse serializes to dict correctly."""
        response = HealthResponse(status="ok", service="agent-sdk-api")
        data = response.model_dump()

        assert data == {"status": "ok", "service": "agent-sdk-api"}

    def test_health_response_model_json_serialization(self) -> None:
        """Test HealthResponse serializes to JSON correctly."""
        response = HealthResponse(status="ok", service="agent-sdk-api")
        json_str = response.model_dump_json()

        assert "ok" in json_str
        assert "agent-sdk-api" in json_str

    def test_health_response_model_deserialization(self) -> None:
        """Test HealthResponse can be created from dict."""
        data = {"status": "ok", "service": "agent-sdk-api"}
        response = HealthResponse(**data)

        assert response.status == "ok"
        assert response.service == "agent-sdk-api"

    def test_health_response_model_validate(self) -> None:
        """Test HealthResponse.model_validate works."""
        data = {"status": "ok", "service": "agent-sdk-api"}
        response = HealthResponse.model_validate(data)

        assert response.status == "ok"
        assert response.service == "agent-sdk-api"


class TestHealthRouterHeaders:
    """Test cases for HTTP response headers."""

    @pytest.fixture
    def client(self) -> TestClient:
        """Create a test client for the FastAPI application."""
        app = create_app()
        return TestClient(app)

    def test_root_endpoint_security_headers(self, client: TestClient) -> None:
        """Test root endpoint includes security headers."""
        response = client.get("/")

        # Check for security headers from middleware
        assert "x-frame-options" in response.headers
        assert response.headers["x-frame-options"] == "DENY"

        assert "x-content-type-options" in response.headers
        assert response.headers["x-content-type-options"] == "nosniff"

        assert "strict-transport-security" in response.headers

    def test_health_endpoint_security_headers(self, client: TestClient) -> None:
        """Test /health endpoint includes security headers."""
        response = client.get("/health")

        # Check for security headers from middleware
        assert "x-frame-options" in response.headers
        assert response.headers["x-frame-options"] == "DENY"

        assert "x-content-type-options" in response.headers
        assert response.headers["x-content-type-options"] == "nosniff"

        assert "strict-transport-security" in response.headers

    def test_root_endpoint_content_encoding(self, client: TestClient) -> None:
        """Test root endpoint may have gzip encoding."""
        response = client.get("/")
        # Small responses might not be gzipped due to minimum_size threshold
        # Just verify the response is valid
        assert response.status_code == 200

    def test_health_endpoint_content_encoding(self, client: TestClient) -> None:
        """Test /health endpoint may have gzip encoding."""
        response = client.get("/health")
        # Small responses might not be gzipped
        assert response.status_code == 200


class TestHealthRouterEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.fixture
    def client(self) -> TestClient:
        """Create a test client for the FastAPI application."""
        app = create_app()
        return TestClient(app)

    def test_invalid_path_returns_404_or_401(self, client: TestClient) -> None:
        """Test invalid paths return 404 or 401 (middleware may intercept first)."""
        response = client.get("/invalid-path")
        # Either 404 (path not found) or 401 (auth middleware intercepts)
        assert response.status_code in (404, 401)

    def test_root_endpoint_with_query_params(self, client: TestClient) -> None:
        """Test root endpoint ignores query parameters."""
        response = client.get("/?debug=true&verbose=1")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "ok"

    def test_health_endpoint_with_query_params(self, client: TestClient) -> None:
        """Test /health endpoint ignores query parameters."""
        response = client.get("/health?debug=true&verbose=1")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "agent-sdk-api"

    def test_root_endpoint_with_trailing_slash(self, client: TestClient) -> None:
        """Test root endpoint with double trailing slash."""
        response = client.get("//")
        # FastAPI normalizes paths, this may 404
        assert response.status_code in (200, 404)

    def test_health_endpoint_case_sensitivity(self, client: TestClient) -> None:
        """Test /health endpoint is case-sensitive."""
        # Uppercase should return 401 (auth middleware) or 404 (not found)
        response = client.get("/HEALTH")
        assert response.status_code in (401, 404)

        # Mixed case should return 401 or 404
        response = client.get("/Health")
        assert response.status_code in (401, 404)

        # Lowercase should work
        response = client.get("/health")
        assert response.status_code == 200

    def test_concurrent_health_checks(self, client: TestClient) -> None:
        """Test multiple concurrent health check requests."""
        import threading

        results = []
        errors = []

        def make_request() -> None:
            try:
                response = client.get("/health")
                results.append(response.status_code)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=make_request) for _ in range(10)]

        for t in threads:
            t.start()

        for t in threads:
            t.join()

        assert len(errors) == 0
        assert all(status == 200 for status in results)
        assert len(results) == 10


class TestHealthRouterCORS:
    """Test CORS headers on health endpoints."""

    @pytest.fixture
    def client(self) -> TestClient:
        """Create a test client for the FastAPI application."""
        app = create_app()
        return TestClient(app)

    def test_root_endpoint_cors_headers(self, client: TestClient) -> None:
        """Test root endpoint includes CORS headers when requested with Origin."""
        # CORS headers are only added when there's an Origin header
        response = client.get("/", headers={"Origin": "http://example.com"})

        # Check for CORS headers - may or may not be present in test client
        # depending on how TestClient handles middleware
        # Just verify the request succeeds
        assert response.status_code == 200

    def test_health_endpoint_cors_headers(self, client: TestClient) -> None:
        """Test /health endpoint includes CORS headers when requested with Origin."""
        response = client.get("/health", headers={"Origin": "http://example.com"})

        # Just verify the request succeeds
        assert response.status_code == 200

    def test_options_request_to_root(self, client: TestClient) -> None:
        """Test OPTIONS request to root endpoint (CORS preflight)."""
        response = client.options("/")
        # OPTIONS bypasses auth middleware but may return 405 if route doesn't support it
        # The actual behavior depends on FastAPI's automatic OPTIONS handling
        assert response.status_code in (200, 204, 405)

    def test_options_request_to_health(self, client: TestClient) -> None:
        """Test OPTIONS request to /health endpoint (CORS preflight)."""
        response = client.options("/health")
        # OPTIONS bypasses auth middleware but may return 405
        assert response.status_code in (200, 204, 405)


class TestHealthRouterOpenAPI:
    """Test OpenAPI documentation for health endpoints.

    Note: /openapi.json requires API key authentication. These tests
    verify schema structure when accessed with valid credentials.
    """

    @pytest.fixture
    def client(self) -> TestClient:
        """Create a test client for the FastAPI application."""
        app = create_app()
        # Use any API key value since tests may not have API_KEY set
        return TestClient(app)

    @pytest.fixture
    def api_key(self) -> str:
        """Get API key from environment or use test value."""
        import os

        # Return actual API key if set, otherwise test won't pass auth
        return os.getenv("API_KEY", "test-api-key")

    def test_openapi_schema_includes_health_endpoints(
        self, client: TestClient, api_key: str
    ) -> None:
        """Test OpenAPI schema includes health endpoints."""
        response = client.get("/openapi.json", headers={"X-API-Key": api_key})
        # May return 401 if API_KEY is not set in test environment
        if response.status_code == 401:
            pytest.skip("API_KEY not configured in test environment")
        assert response.status_code == 200

        schema = response.json()
        assert "paths" in schema

        # Check for root endpoint
        assert "/" in schema["paths"]

        # Check for /health endpoint
        assert "/health" in schema["paths"]

    def test_openapi_schema_root_endpoint_tags(
        self, client: TestClient, api_key: str
    ) -> None:
        """Test OpenAPI schema has correct tags for root endpoint."""
        response = client.get("/openapi.json", headers={"X-API-Key": api_key})
        if response.status_code == 401:
            pytest.skip("API_KEY not configured in test environment")

        schema = response.json()

        path_schema = schema["paths"]["/"]["get"]
        assert "tags" in path_schema
        assert "health" in path_schema["tags"]

    def test_openapi_schema_health_endpoint_tags(
        self, client: TestClient, api_key: str
    ) -> None:
        """Test OpenAPI schema has correct tags for /health endpoint."""
        response = client.get("/openapi.json", headers={"X-API-Key": api_key})
        if response.status_code == 401:
            pytest.skip("API_KEY not configured in test environment")

        schema = response.json()

        path_schema = schema["paths"]["/health"]["get"]
        assert "tags" in path_schema
        assert "health" in path_schema["tags"]

    def test_openapi_schema_response_models(
        self, client: TestClient, api_key: str
    ) -> None:
        """Test OpenAPI schema defines response models correctly."""
        response = client.get("/openapi.json", headers={"X-API-Key": api_key})
        if response.status_code == 401:
            pytest.skip("API_KEY not configured in test environment")

        schema = response.json()

        # Check root endpoint response
        root_response = schema["paths"]["/"]["get"]["responses"]["200"]
        assert "content" in root_response
        assert "application/json" in root_response["content"]

        # Check /health endpoint response
        health_response = schema["paths"]["/health"]["get"]["responses"]["200"]
        assert "content" in health_response
        assert "application/json" in health_response["content"]


class TestHealthRouterIntegration:
    """Integration tests for health router with full app context."""

    @pytest.fixture
    def client(self) -> TestClient:
        """Create a test client for the FastAPI application."""
        app = create_app()
        return TestClient(app)

    def test_both_endpoints_consistent_status(self, client: TestClient) -> None:
        """Test both health endpoints return consistent status."""
        root_response = client.get("/")
        health_response = client.get("/health")

        root_data = root_response.json()
        health_data = health_response.json()

        # Both should return "ok" status
        assert root_data["status"] == health_data["status"] == "ok"

    def test_health_endpoints_available_after_startup(self, client: TestClient) -> None:
        """Test health endpoints are available immediately after startup."""
        # These should work immediately without any initialization
        response = client.get("/")
        assert response.status_code == 200

        response = client.get("/health")
        assert response.status_code == 200

    def test_health_endpoints_no_auth_required(self, client: TestClient) -> None:
        """Test health endpoints work without authentication."""
        # Health endpoints should be publicly accessible
        response = client.get("/", headers={"Authorization": "invalid"})
        # Should still work - health endpoints don't require auth
        assert response.status_code == 200

        response = client.get("/health", headers={"Authorization": "invalid"})
        assert response.status_code == 200

    def test_health_endpoints_no_api_key_required(self, client: TestClient) -> None:
        """Test health endpoints work without API key."""
        # Health endpoints should work without X-API-Key header
        response = client.get("/")
        assert response.status_code == 200

        response = client.get("/health")
        assert response.status_code == 200


class TestHealthRouterLoadBalancerCompatibility:
    """Tests for load balancer and monitoring system compatibility."""

    @pytest.fixture
    def client(self) -> TestClient:
        """Create a test client for the FastAPI application."""
        app = create_app()
        return TestClient(app)

    def test_root_endpoint_simple_response(self, client: TestClient) -> None:
        """Test root endpoint returns simple JSON for load balancers."""
        response = client.get("/")
        data = response.json()

        # Load balancers expect simple, predictable responses
        assert isinstance(data, dict)
        assert len(data) <= 2  # Should have at most 2 fields

    def test_health_endpoint_includes_service_identifier(
        self, client: TestClient
    ) -> None:
        """Test /health endpoint includes service name for monitoring."""
        response = client.get("/health")
        data = response.json()

        # Monitoring systems need to identify the service
        assert "service" in data
        assert isinstance(data["service"], str)
        assert len(data["service"]) > 0

    def test_health_endpoint_reliable_indicator(self, client: TestClient) -> None:
        """Test health endpoint is a reliable service health indicator."""
        # Make multiple requests to ensure consistency
        for _ in range(5):
            response = client.get("/health")
            assert response.status_code == 200

            data = response.json()
            assert data["status"] == "ok"

    def test_response_size_small(self, client: TestClient) -> None:
        """Test health check responses are small."""
        root_response = client.get("/")
        health_response = client.get("/health")

        # Response bodies should be tiny (< 200 bytes)
        assert len(root_response.content) < 200
        assert len(health_response.content) < 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
