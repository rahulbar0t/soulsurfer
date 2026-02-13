import io
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


class TestHealthEndpoint:
    def test_health_returns_ok(self, client):
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "version" in data


class TestSessionEndpoints:
    def test_create_session_rejects_invalid_format(self, client):
        video = io.BytesIO(b"fake data")
        response = client.post(
            "/api/v1/sessions/",
            files={"video": ("test.txt", video, "text/plain")},
        )
        assert response.status_code == 400
        assert "Unsupported video format" in response.json()["detail"]

    def test_create_session_rejects_invalid_skill_level(self, client):
        video = io.BytesIO(b"fake video data")
        response = client.post(
            "/api/v1/sessions/",
            files={"video": ("test.mp4", video, "video/mp4")},
            data={"skill_level": "expert"},
        )
        assert response.status_code == 400
        assert "Invalid skill_level" in response.json()["detail"]

    def test_get_nonexistent_session_returns_404(self, client):
        response = client.get("/api/v1/sessions/nonexistent-id")
        assert response.status_code == 404

    @patch("app.api.endpoints.sessions._run_pipeline")
    def test_create_session_returns_202(self, mock_pipeline, client):
        video = io.BytesIO(b"fake video data")
        response = client.post(
            "/api/v1/sessions/",
            files={"video": ("test.mp4", video, "video/mp4")},
            data={"surfer_name": "TestSurfer", "skill_level": "beginner"},
        )
        assert response.status_code == 202
        data = response.json()
        assert "session_id" in data
        assert data["status"] == "pending"
        assert data["surfer_name"] == "TestSurfer"
        assert data["skill_level"] == "beginner"

    @patch("app.api.endpoints.sessions._run_pipeline")
    def test_get_pending_session(self, mock_pipeline, client):
        # Create a session
        video = io.BytesIO(b"fake video data")
        create_resp = client.post(
            "/api/v1/sessions/",
            files={"video": ("test.mp4", video, "video/mp4")},
        )
        session_id = create_resp.json()["session_id"]

        # Get session status
        get_resp = client.get(f"/api/v1/sessions/{session_id}")
        assert get_resp.status_code == 200
        assert get_resp.json()["status"] == "pending"
