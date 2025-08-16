import pytest
import asyncio
from datetime import datetime, timedelta
from services.session_service import (
    SessionService, 
    InMemorySessionStorage, 
    ConversationSession, 
    Message
)


@pytest.fixture
def session_storage():
    """Create a fresh session storage for each test."""
    return InMemorySessionStorage()


@pytest.fixture
def session_service(session_storage):
    """Create a session service with the storage."""
    return SessionService(session_storage)


class TestMessage:
    """Test Message dataclass."""
    
    def test_message_creation(self):
        """Test message creation with default values."""
        message = Message(role="user", content="Hello")
        
        assert message.role == "user"
        assert message.content == "Hello"
        assert isinstance(message.timestamp, datetime)
        assert message.metadata == {}
    
    def test_message_with_metadata(self):
        """Test message creation with metadata."""
        metadata = {"source": "test"}
        message = Message(role="assistant", content="Hi there", metadata=metadata)
        
        assert message.role == "assistant"
        assert message.content == "Hi there"
        assert message.metadata == metadata


class TestConversationSession:
    """Test ConversationSession dataclass."""
    
    def test_session_creation(self):
        """Test session creation with default values."""
        session = ConversationSession(session_id="test-123")
        
        assert session.session_id == "test-123"
        assert session.messages == []
        assert isinstance(session.created_at, datetime)
        assert isinstance(session.updated_at, datetime)
        assert session.metadata == {}
    
    def test_add_message(self):
        """Test adding messages to session."""
        session = ConversationSession(session_id="test-123")
        original_updated = session.updated_at
        
        # Small delay to ensure timestamp difference
        import time
        time.sleep(0.01)
        
        session.add_message("user", "Hello", {"test": True})
        
        assert len(session.messages) == 1
        assert session.messages[0].role == "user"
        assert session.messages[0].content == "Hello"
        assert session.messages[0].metadata == {"test": True}
        assert session.updated_at > original_updated
    
    def test_get_conversation_history(self):
        """Test getting conversation history."""
        session = ConversationSession(session_id="test-123")
        session.add_message("user", "Hello")
        session.add_message("assistant", "Hi there")
        
        history = session.get_conversation_history()
        
        assert len(history) == 2
        assert history[0]["role"] == "user"
        assert history[0]["content"] == "Hello"
        assert "timestamp" in history[0]
        assert history[1]["role"] == "assistant"
        assert history[1]["content"] == "Hi there"


class TestInMemorySessionStorage:
    """Test InMemorySessionStorage implementation."""
    
    @pytest.mark.asyncio
    async def test_create_session_with_id(self, session_storage):
        """Test creating session with specific ID."""
        session = await session_storage.create_session("test-123")
        
        assert session.session_id == "test-123"
        assert len(session.messages) == 0
    
    @pytest.mark.asyncio
    async def test_create_session_auto_id(self, session_storage):
        """Test creating session with auto-generated ID."""
        session = await session_storage.create_session()
        
        assert session.session_id is not None
        assert len(session.session_id) > 0
    
    @pytest.mark.asyncio
    async def test_create_duplicate_session(self, session_storage):
        """Test creating session with duplicate ID raises error."""
        await session_storage.create_session("test-123")
        
        with pytest.raises(ValueError, match="Session test-123 already exists"):
            await session_storage.create_session("test-123")
    
    @pytest.mark.asyncio
    async def test_get_session(self, session_storage):
        """Test retrieving existing session."""
        created_session = await session_storage.create_session("test-123")
        retrieved_session = await session_storage.get_session("test-123")
        
        assert retrieved_session is not None
        assert retrieved_session.session_id == created_session.session_id
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_session(self, session_storage):
        """Test retrieving non-existent session returns None."""
        session = await session_storage.get_session("nonexistent")
        
        assert session is None
    
    @pytest.mark.asyncio
    async def test_update_session(self, session_storage):
        """Test updating session."""
        session = await session_storage.create_session("test-123")
        session.add_message("user", "Hello")
        
        await session_storage.update_session(session)
        
        retrieved = await session_storage.get_session("test-123")
        assert len(retrieved.messages) == 1
        assert retrieved.messages[0].content == "Hello"
    
    @pytest.mark.asyncio
    async def test_delete_session(self, session_storage):
        """Test deleting session."""
        await session_storage.create_session("test-123")
        
        deleted = await session_storage.delete_session("test-123")
        assert deleted is True
        
        session = await session_storage.get_session("test-123")
        assert session is None
    
    @pytest.mark.asyncio
    async def test_delete_nonexistent_session(self, session_storage):
        """Test deleting non-existent session."""
        deleted = await session_storage.delete_session("nonexistent")
        assert deleted is False
    
    @pytest.mark.asyncio
    async def test_cleanup_expired_sessions(self, session_storage):
        """Test cleaning up expired sessions."""
        # Create sessions with different timestamps
        recent_session = await session_storage.create_session("recent")
        old_session = await session_storage.create_session("old")
        
        # Manually set old session timestamp
        old_session.updated_at = datetime.now() - timedelta(hours=25)
        await session_storage.update_session(old_session)
        
        # Cleanup sessions older than 24 hours
        cleaned = await session_storage.cleanup_expired_sessions(24)
        
        assert cleaned == 1
        assert await session_storage.get_session("recent") is not None
        assert await session_storage.get_session("old") is None


class TestSessionService:
    """Test SessionService."""
    
    @pytest.mark.asyncio
    async def test_create_session(self, session_service):
        """Test creating session through service."""
        session = await session_service.create_session("test-123")
        
        assert session.session_id == "test-123"
    
    @pytest.mark.asyncio
    async def test_get_or_create_existing(self, session_service):
        """Test getting existing session."""
        created = await session_service.create_session("test-123")
        retrieved = await session_service.get_or_create_session("test-123")
        
        assert retrieved.session_id == created.session_id
    
    @pytest.mark.asyncio
    async def test_get_or_create_new(self, session_service):
        """Test creating new session when not found."""
        session = await session_service.get_or_create_session("new-session")
        
        assert session.session_id == "new-session"
    
    @pytest.mark.asyncio
    async def test_get_or_create_auto_id(self, session_service):
        """Test creating new session with auto-generated ID."""
        session = await session_service.get_or_create_session()
        
        assert session.session_id is not None
        assert len(session.session_id) > 0
    
    @pytest.mark.asyncio
    async def test_add_message(self, session_service):
        """Test adding message to session."""
        session = await session_service.create_session("test-123")
        
        updated_session = await session_service.add_message(
            "test-123", 
            "user", 
            "Hello", 
            {"source": "test"}
        )
        
        assert len(updated_session.messages) == 1
        assert updated_session.messages[0].content == "Hello"
        assert updated_session.messages[0].metadata == {"source": "test"}
    
    @pytest.mark.asyncio
    async def test_add_message_nonexistent_session(self, session_service):
        """Test adding message to non-existent session raises error."""
        with pytest.raises(ValueError, match="Session nonexistent not found"):
            await session_service.add_message("nonexistent", "user", "Hello")
    
    @pytest.mark.asyncio
    async def test_get_conversation_history(self, session_service):
        """Test getting conversation history."""
        session = await session_service.create_session("test-123")
        await session_service.add_message("test-123", "user", "Hello")
        await session_service.add_message("test-123", "assistant", "Hi there")
        
        history = await session_service.get_conversation_history("test-123")
        
        assert len(history) == 2
        assert history[0]["role"] == "user"
        assert history[1]["role"] == "assistant"
    
    @pytest.mark.asyncio
    async def test_get_history_nonexistent_session(self, session_service):
        """Test getting history for non-existent session raises error."""
        with pytest.raises(ValueError, match="Session nonexistent not found"):
            await session_service.get_conversation_history("nonexistent")
    
    @pytest.mark.asyncio
    async def test_delete_session(self, session_service):
        """Test deleting session through service."""
        await session_service.create_session("test-123")
        
        deleted = await session_service.delete_session("test-123")
        assert deleted is True
    
    @pytest.mark.asyncio
    async def test_cleanup_expired_sessions(self, session_service):
        """Test cleanup through service."""
        await session_service.create_session("test-123")
        
        # Should not clean any recent sessions
        cleaned = await session_service.cleanup_expired_sessions(24)
        assert cleaned == 0
