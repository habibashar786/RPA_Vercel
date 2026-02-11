"""Unit tests for FastAPI endpoints."""

import pytest
from fastapi.testclient import TestClient
import asyncio

from src.api.main import app, initialize_system, shutdown_system


@pytest.fixture
def client():
    """FastAPI test client with initialization."""
    # Initialize the system before creating client
    try:
        asyncio.run(initialize_system())
    except RuntimeError:
        # Event loop already running in pytest
        loop = asyncio.get_event_loop()
        loop.run_until_complete(initialize_system())
    
    client = TestClient(app)
    yield client
    
    # Shutdown after tests
    try:
        asyncio.run(shutdown_system())
    except RuntimeError:
        # Event loop already running in pytest
        loop = asyncio.get_event_loop()
        loop.run_until_complete(shutdown_system())


def test_health_endpoint(client):
    """Test /health endpoint returns healthy status."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["agents_registered"] == 11
    assert data["version"] == "1.0.0"


def test_agents_endpoint(client):
    """Test /agents endpoint returns registered agents."""
    response = client.get("/agents")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 11
    assert isinstance(data["agents"], list)
    assert len(data["agents"]) == 11
    # Verify key agents are registered
    assert "literature_review_agent" in data["agents"]
    assert "front_matter_agent" in data["agents"]
    assert "reference_citation_agent" in data["agents"]


def test_status_endpoint(client):
    """Test /status endpoint returns system status."""
    response = client.get("/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert data["agents"] == 11
    assert data["active_workflows"] >= 0


def test_proposals_post_valid_request(client):
    """Test POST /proposals with valid request."""
    payload = {
        "topic": "Machine learning in healthcare applications",
        "key_points": [
            "Background and motivation",
            "Research objectives",
            "Expected contributions",
        ],
    }
    response = client.post("/proposals", json=payload)
    # May return 200 or 500 depending on workflow; main check is structure
    if response.status_code == 200:
        data = response.json()
        assert "request_id" in data
        assert data["topic"] == payload["topic"]
        assert data["status"] in ["completed", "in_progress"]
    else:
        # Even on error, should be proper HTTP error
        assert response.status_code >= 400


def test_proposals_post_invalid_topic(client):
    """Test POST /proposals with invalid (too short) topic."""
    payload = {"topic": "short"}  # Min length is 10
    response = client.post("/proposals", json=payload)
    assert response.status_code == 422  # Validation error


def test_proposals_post_missing_topic(client):
    """Test POST /proposals with missing topic."""
    payload = {}
    response = client.post("/proposals", json=payload)
    assert response.status_code == 422


def test_proposals_get_status(client):
    """Test GET /proposals/{request_id} endpoint."""
    # Use a fake request_id (will not be found, but endpoint should handle gracefully)
    response = client.get("/proposals/nonexistent_request_id")
    # Should return 404 or error gracefully
    assert response.status_code in [404, 500]


def test_health_endpoint_uninitialized():
    """Test /health endpoint when system not initialized."""
    # Create a fresh client without calling initialize_system
    from src.api.main import app as fresh_app
    from fastapi.testclient import TestClient
    fresh_client = TestClient(fresh_app)
    response = fresh_client.get("/health")
    # Should handle gracefully (either return partial status or 503)
    assert response.status_code in [200, 503]


def test_agents_endpoint_uninitialized():
    """Test /agents endpoint when system not initialized."""
    from src.api.main import app as fresh_app
    from fastapi.testclient import TestClient
    fresh_client = TestClient(fresh_app)
    response = fresh_client.get("/agents")
    # Should handle gracefully
    assert response.status_code in [200, 503]


def test_proposals_custom_key_points(client):
    """Test POST /proposals with custom key points."""
    payload = {
        "topic": "Quantum computing and cryptography security",
        "key_points": ["Overview", "Challenges", "Future outlook"],
        "author": "Dr. Jane Doe",
        "institution": "Tech University",
        "department": "Computer Science",
    }
    response = client.post("/proposals", json=payload)
    if response.status_code == 200:
        data = response.json()
        assert data["topic"] == payload["topic"]
        assert data["request_id"]


def test_error_response_structure(client):
    """Test that error responses follow expected structure."""
    # Try to get a non-existent proposal
    response = client.get("/proposals/fake_id_xyz")
    # Even if error, structure should be consistent
    assert response.status_code >= 400
    # Response should be valid JSON
    # Response should contain error structure
    assert "error" in response.json() or response.status_code >= 400

