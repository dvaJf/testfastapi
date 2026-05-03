"""
Tests for basic API endpoints and pages.

Covers:
- Root endpoint
- Health check
- CORS headers
"""

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.integration


class TestBasicEndpoints:
    """Tests for basic endpoints."""

    async def test_root_endpoint(self, client: AsyncClient):
        """Test root endpoint returns HTML page."""
        response = await client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    async def test_health_check(self, client: AsyncClient):
        """Test health check endpoint."""
        response = await client.get("/api/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    async def test_cors_headers(self, client: AsyncClient):
        """Test CORS headers are present."""
        response = await client.get(
            "/api/races/",
            headers={"Origin": "http://localhost"},
        )
        assert "access-control-allow-origin" in response.headers

    async def test_404_handler(self, client: AsyncClient):
        """Test 404 for non-existent endpoint."""
        response = await client.get("/api/nonexistent")
        assert response.status_code == 404

    async def test_method_not_allowed(self, client: AsyncClient):
        """Test method not allowed."""
        response = await client.put("/api/races/")
        # Should return 405 or be handled gracefully
        assert response.status_code in [405, 422]
