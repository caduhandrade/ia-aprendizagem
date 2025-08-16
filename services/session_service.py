import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from abc import ABC, abstractmethod


@dataclass
class Message:
    """Represents a single message in a conversation."""
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConversationSession:
    """Represents a conversation session with history."""
    session_id: str
    messages: List[Message] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_message(self, role: str, content: str, metadata: Dict[str, Any] = None) -> None:
        """Add a message to the conversation."""
        message = Message(
            role=role,
            content=content,
            metadata=metadata or {}
        )
        self.messages.append(message)
        self.updated_at = datetime.now()
    
    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Get the conversation history in a format suitable for the AI model."""
        return [
            {
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat()
            }
            for msg in self.messages
        ]


class SessionStorage(ABC):
    """Abstract base class for session storage implementations."""
    
    @abstractmethod
    async def create_session(self, session_id: str = None) -> ConversationSession:
        """Create a new conversation session."""
        pass
    
    @abstractmethod
    async def get_session(self, session_id: str) -> Optional[ConversationSession]:
        """Retrieve a conversation session by ID."""
        pass
    
    @abstractmethod
    async def update_session(self, session: ConversationSession) -> None:
        """Update an existing conversation session."""
        pass
    
    @abstractmethod
    async def delete_session(self, session_id: str) -> bool:
        """Delete a conversation session."""
        pass
    
    @abstractmethod
    async def cleanup_expired_sessions(self, max_age_hours: int = 24) -> int:
        """Clean up expired sessions and return the number of sessions removed."""
        pass


class InMemorySessionStorage(SessionStorage):
    """In-memory implementation of session storage for development/testing."""
    
    def __init__(self):
        self._sessions: Dict[str, ConversationSession] = {}
    
    async def create_session(self, session_id: str = None) -> ConversationSession:
        """Create a new conversation session."""
        if session_id is None:
            session_id = str(uuid.uuid4())
        
        if session_id in self._sessions:
            raise ValueError(f"Session {session_id} already exists")
        
        session = ConversationSession(session_id=session_id)
        self._sessions[session_id] = session
        return session
    
    async def get_session(self, session_id: str) -> Optional[ConversationSession]:
        """Retrieve a conversation session by ID."""
        return self._sessions.get(session_id)
    
    async def update_session(self, session: ConversationSession) -> None:
        """Update an existing conversation session."""
        self._sessions[session.session_id] = session
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete a conversation session."""
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False
    
    async def cleanup_expired_sessions(self, max_age_hours: int = 24) -> int:
        """Clean up expired sessions and return the number of sessions removed."""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        expired_sessions = [
            session_id for session_id, session in self._sessions.items()
            if session.updated_at < cutoff_time
        ]
        
        for session_id in expired_sessions:
            del self._sessions[session_id]
        
        return len(expired_sessions)


class SessionService:
    """Service for managing conversation sessions."""
    
    def __init__(self, storage: SessionStorage):
        self.storage = storage
    
    async def create_session(self, session_id: str = None) -> ConversationSession:
        """Create a new conversation session."""
        return await self.storage.create_session(session_id)
    
    async def get_or_create_session(self, session_id: str = None) -> ConversationSession:
        """Get an existing session or create a new one."""
        if session_id:
            session = await self.storage.get_session(session_id)
            if session:
                return session
        
        return await self.storage.create_session(session_id)
    
    async def add_message(
        self, 
        session_id: str, 
        role: str, 
        content: str, 
        metadata: Dict[str, Any] = None
    ) -> ConversationSession:
        """Add a message to a conversation session."""
        session = await self.storage.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        session.add_message(role, content, metadata)
        await self.storage.update_session(session)
        return session
    
    async def get_conversation_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Get the conversation history for a session."""
        session = await self.storage.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        return session.get_conversation_history()
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete a conversation session."""
        return await self.storage.delete_session(session_id)
    
    async def cleanup_expired_sessions(self, max_age_hours: int = 24) -> int:
        """Clean up expired sessions."""
        return await self.storage.cleanup_expired_sessions(max_age_hours)
