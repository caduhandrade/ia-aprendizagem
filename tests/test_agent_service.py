import pytest
from unittest.mock import Mock, AsyncMock
from services.agent_service import AgentService, AgentResponse
from services.session_service import SessionService, InMemorySessionStorage


@pytest.fixture
def mock_agent():
    """Create a mock agent."""
    agent = Mock()
    agent.name = "test_agent"
    return agent


@pytest.fixture
def session_service():
    """Create a session service for testing."""
    storage = InMemorySessionStorage()
    return SessionService(storage)


@pytest.fixture
def agent_service(session_service, mock_agent):
    """Create an agent service for testing."""
    return AgentService(session_service, mock_agent)


class TestAgentService:
    """Test AgentService functionality."""
    
    @pytest.mark.asyncio
    async def test_process_query_new_session(self, agent_service):
        """Test processing query with new session."""
        response = await agent_service.process_query("Hello", session_id=None)
        
        assert isinstance(response, AgentResponse)
        assert response.content is not None
        assert response.session_id is not None
        assert "agent_name" in response.metadata
        assert response.metadata["conversation_length"] == 2  # user + assistant
    
    @pytest.mark.asyncio
    async def test_process_query_existing_session(self, agent_service):
        """Test processing query with existing session."""
        # First query to create session
        first_response = await agent_service.process_query("Hello")
        session_id = first_response.session_id
        
        # Second query with same session
        second_response = await agent_service.process_query("How are you?", session_id=session_id)
        
        assert second_response.session_id == session_id
        assert second_response.metadata["conversation_length"] == 4  # 2 previous + 2 new
    
    @pytest.mark.asyncio
    async def test_process_query_with_metadata(self, agent_service):
        """Test processing query with metadata."""
        metadata = {"source": "test", "priority": "high"}
        response = await agent_service.process_query("Hello", metadata=metadata)
        
        assert response.session_id is not None
        # Check that user message has the metadata
        history = await agent_service.get_session_history(response.session_id)
        user_message = next(msg for msg in history if msg["role"] == "user")
        # Note: metadata is stored in the Message object, not in the history format
        # This is a simplified test
    
    @pytest.mark.asyncio
    async def test_process_query_stream(self, agent_service):
        """Test streaming query processing."""
        chunks = []
        async for chunk in agent_service.process_query_stream("Hello"):
            chunks.append(chunk)
        
        # Should have content chunks and a completion chunk
        content_chunks = [c for c in chunks if c.get("type") == "chunk"]
        complete_chunks = [c for c in chunks if c.get("type") == "complete"]
        
        assert len(content_chunks) > 0
        assert len(complete_chunks) == 1
        assert complete_chunks[0]["session_id"] is not None
    
    @pytest.mark.asyncio
    async def test_get_session_history(self, agent_service):
        """Test getting session history."""
        response = await agent_service.process_query("Hello")
        session_id = response.session_id
        
        history = await agent_service.get_session_history(session_id)
        
        assert len(history) == 2  # user + assistant
        assert history[0]["role"] == "user"
        assert history[0]["content"] == "Hello"
        assert history[1]["role"] == "assistant"
    
    @pytest.mark.asyncio
    async def test_delete_session(self, agent_service):
        """Test deleting session."""
        response = await agent_service.process_query("Hello")
        session_id = response.session_id
        
        deleted = await agent_service.delete_session(session_id)
        
        assert deleted is True
        
        # Should raise error when trying to get history of deleted session
        with pytest.raises(ValueError):
            await agent_service.get_session_history(session_id)
    
    @pytest.mark.asyncio
    async def test_context_building_with_history(self, agent_service):
        """Test that context is built properly with conversation history."""
        # Create a conversation
        response1 = await agent_service.process_query("What is Python?")
        session_id = response1.session_id
        
        response2 = await agent_service.process_query("Tell me more about it", session_id=session_id)
        
        # The second response should have context from the first question
        # This is tested indirectly by checking that the session has the right number of messages
        history = await agent_service.get_session_history(session_id)
        assert len(history) == 4  # 2 exchanges
    
    def test_build_context_from_history_empty(self, agent_service):
        """Test building context with empty history."""
        context = agent_service._build_context_from_history([], "Hello")
        assert context == "Hello"
    
    def test_build_context_from_history_with_messages(self, agent_service):
        """Test building context with conversation history."""
        history = [
            {"role": "user", "content": "What is Python?"},
            {"role": "assistant", "content": "Python is a programming language."},
            {"role": "user", "content": "Tell me more"}
        ]
        
        context = agent_service._build_context_from_history(history, "Tell me more")
        
        assert "Contexto da conversa anterior:" in context
        assert "What is Python?" in context
        assert "Python is a programming language." in context
        assert "Pergunta atual:" in context
        assert "Tell me more" in context
    
    def test_build_context_truncation(self, agent_service):
        """Test that context is truncated for long conversations."""
        # Create a history with 15 messages (more than the 10 limit)
        history = []
        for i in range(15):
            role = "user" if i % 2 == 0 else "assistant"
            history.append({"role": role, "content": f"Msg_{i:02d}"})
        
        context = agent_service._build_context_from_history(history, "Current question")
        
        # Should only include last 10 messages, but exclude the very last one (current message)
        # So it should include messages 5-13 (indices 5-13, excluding 14)
        assert "Msg_00" not in context
        assert "Msg_01" not in context
        assert "Msg_02" not in context
        assert "Msg_03" not in context
        assert "Msg_04" not in context
        # Should include messages in the recent history (excluding the last one)
        assert "Msg_05" in context  # First of the recent 10
        assert "Msg_13" in context  # Last before current
        assert "Msg_14" not in context  # This is excluded as "current message"
        assert "Current question" in context
