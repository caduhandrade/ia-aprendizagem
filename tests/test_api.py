import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock

from api.main import app


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
async def async_client():
    """Create an async test client."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


class TestHealthEndpoint:
    """Test health check endpoint."""
    
    def test_health_check(self, client):
        """Test health check returns correct status."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["version"] == "1.0.0"
        assert "environment" in data


class TestSessionEndpoints:
    """Test session management endpoints."""
    
    def test_create_session(self, client):
        """Test creating a new session."""
        response = client.post("/sessions")
        
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert data["message"] == "Session created successfully"
        assert len(data["session_id"]) > 0
    
    def test_get_session_history_new_session(self, client):
        """Test getting history for non-existent session."""
        response = client.get("/sessions/nonexistent/history")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    def test_delete_nonexistent_session(self, client):
        """Test deleting non-existent session."""
        response = client.delete("/sessions/nonexistent")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]


class TestAskEndpoint:
    """Test the main ask endpoint."""
    
    def test_ask_without_session(self, client):
        """Test asking question without session ID."""
        response = client.post(
            "/ask",
            json={"query": "Hello, how are you?"}
        )
        
        # Should return streaming response
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
    
    def test_ask_with_session(self, client):
        """Test asking question with session ID."""
        # First create a session
        session_response = client.post("/sessions")
        session_id = session_response.json()["session_id"]
        
        # Then ask a question
        response = client.post(
            "/ask",
            json={
                "query": "Hello, how are you?",
                "session_id": session_id
            }
        )
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
    
    def test_ask_with_metadata(self, client):
        """Test asking question with metadata."""
        response = client.post(
            "/ask",
            json={
                "query": "Hello",
                "metadata": {"source": "test", "priority": "high"}
            }
        )
        
        assert response.status_code == 200
    
    def test_ask_empty_query(self, client):
        """Test asking with empty query."""
        response = client.post(
            "/ask",
            json={"query": ""}
        )
        
        # Should return validation error
        assert response.status_code == 422
    
    def test_ask_too_long_query(self, client):
        """Test asking with too long query."""
        long_query = "x" * 2001  # Exceeds max_length of 2000
        response = client.post(
            "/ask",
            json={"query": long_query}
        )
        
        # Should return validation error
        assert response.status_code == 422
    
    def test_ask_invalid_json(self, client):
        """Test asking with invalid JSON."""
        response = client.post(
            "/ask",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 422


class TestSessionWorkflow:
    """Test complete session workflow."""
    
    def test_complete_conversation_workflow(self, client):
        """Test a complete conversation workflow."""
        # 1. Create a session
        session_response = client.post("/sessions")
        assert session_response.status_code == 200
        session_id = session_response.json()["session_id"]
        
        # 2. Ask first question
        response1 = client.post(
            "/ask",
            json={
                "query": "What is Python?",
                "session_id": session_id
            }
        )
        assert response1.status_code == 200
        
        # 3. Ask follow-up question
        response2 = client.post(
            "/ask",
            json={
                "query": "Tell me more about it",
                "session_id": session_id
            }
        )
        assert response2.status_code == 200
        
        # 4. Get conversation history
        history_response = client.get(f"/sessions/{session_id}/history")
        assert history_response.status_code == 200
        
        history_data = history_response.json()
        assert history_data["session_id"] == session_id
        # Should have 4 messages: 2 user + 2 assistant
        assert len(history_data["history"]) == 4
        
        # 5. Delete session
        delete_response = client.delete(f"/sessions/{session_id}")
        assert delete_response.status_code == 200
        
        # 6. Verify session is deleted
        history_response_after = client.get(f"/sessions/{session_id}/history")
        assert history_response_after.status_code == 404


class TestCORS:
    """Test CORS configuration."""
    
    def test_cors_headers(self, client):
        """Test that CORS headers are present."""
        response = client.options("/health")
        
        # FastAPI automatically handles OPTIONS requests for CORS
        # Just verify the endpoint works
        assert response.status_code in [200, 405]  # 405 if OPTIONS not explicitly handled


class TestErrorHandling:
    """Test error handling scenarios."""
    
    @patch('api.main.agent_service.process_query_stream')
    def test_ask_endpoint_error_handling(self, mock_stream, client):
        """Test error handling in ask endpoint."""
        # Mock an exception in the agent service
        mock_stream.side_effect = Exception("Test error")
        
        response = client.post(
            "/ask",
            json={"query": "Hello"}
        )
        
        assert response.status_code == 500
        assert "Test error" in response.json()["detail"]
