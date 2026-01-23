"""
Integration testy pro FastAPI endpoints
"""

import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


class TestHealthEndpoint:
    """Testy pro health check"""

    def test_health_check(self):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "has_url" in data
        assert "llm_server_url" in data


class TestStaticFiles:
    """Testy pro frontend serving"""

    def test_root_endpoint(self):
        response = client.get("/")
        assert response.status_code == 200
        assert "J.A.R.V.I.S." in response.text

    def test_chat_js_accessible(self):
        response = client.get("/static/chat.js")
        assert response.status_code == 200


class TestDebugEndpoints:
    """Testy pro debug endpoints"""

    def test_debug_routing(self):
        response = client.get("/debug/routing/Refactor%20auth.py")
        assert response.status_code == 200
        data = response.json()
        assert "routing_decision" in data
        assert data["routing_decision"]["service"] == "filesystem-mcp"

    def test_debug_stats(self):
        response = client.get("/debug/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total_requests" in data

    def test_debug_logs(self):
        response = client.get("/debug/logs?lines=10")
        assert response.status_code == 200


class TestWebSocket:
    """Testy pro WebSocket komunikaci"""

    def test_websocket_connection(self):
        with client.websocket_connect("/ws") as websocket:
            # Test že spojení funguje
            websocket.send_text("Hello")
            data = websocket.receive_json()

            # Měli bychom dostat routing_info
            assert data["type"] in ["routing_info", "response", "error"]
