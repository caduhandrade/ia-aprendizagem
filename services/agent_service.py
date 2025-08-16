import asyncio
from typing import Dict, List, Optional, Any, AsyncGenerator
from dataclasses import dataclass
import logging

from google.adk.agents import Agent
from google.adk.tools import google_search
from agents.root_agent import root_agent

from services.session_service import SessionService, ConversationSession


logger = logging.getLogger(__name__)


@dataclass
class AgentResponse:
    """Represents a response from the agent."""
    content: str
    session_id: str
    metadata: Dict[str, Any]
    
    
class AgentService:
    """Service for managing AI agent interactions with session support."""
    
    def __init__(self, session_service: SessionService, agent: Agent = None):
        self.session_service = session_service
        self.agent = agent or root_agent
        
    async def process_query(
        self, 
        query: str, 
        session_id: Optional[str] = None,
        metadata: Dict[str, Any] = None
    ) -> AgentResponse:
        """Process a query with the agent using session context."""
        try:
            # Get or create session
            session = await self.session_service.get_or_create_session(session_id)
            
            # Add user message to session
            await self.session_service.add_message(
                session.session_id, 
                "user", 
                query, 
                metadata or {}
            )
            
            # Prepare conversation context for the agent
            conversation_history = session.get_conversation_history()
            
            # Build context from conversation history
            context = self._build_context_from_history(conversation_history, query)
            
            # Process with agent
            response = await self._process_with_agent(context)
            
            # Add agent response to session
            await self.session_service.add_message(
                session.session_id,
                "assistant", 
                response,
                {"agent_name": self.agent.name}
            )
            
            return AgentResponse(
                content=response,
                session_id=session.session_id,
                metadata={
                    "agent_name": self.agent.name,
                    "conversation_length": len(session.messages)
                }
            )
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            raise
    
    async def process_query_stream(
        self, 
        query: str, 
        session_id: Optional[str] = None,
        metadata: Dict[str, Any] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Process a query with streaming response."""
        try:
            # Get or create session
            session = await self.session_service.get_or_create_session(session_id)
            
            # Add user message to session
            await self.session_service.add_message(
                session.session_id, 
                "user", 
                query, 
                metadata or {}
            )
            
            # Prepare conversation context for the agent
            conversation_history = session.get_conversation_history()
            context = self._build_context_from_history(conversation_history, query)
            
            # Stream response from agent
            full_response = ""
            async for chunk in self._process_with_agent_stream(context):
                full_response += chunk
                yield {
                    "content": chunk,
                    "session_id": session.session_id,
                    "type": "chunk"
                }
            
            # Add complete response to session
            await self.session_service.add_message(
                session.session_id,
                "assistant",
                full_response,
                {"agent_name": self.agent.name}
            )
            
            # Send completion signal
            yield {
                "session_id": session.session_id,
                "type": "complete",
                "metadata": {
                    "agent_name": self.agent.name,
                    "conversation_length": len(session.messages)
                }
            }
            
        except Exception as e:
            logger.error(f"Error processing streaming query: {e}")
            yield {
                "type": "error",
                "error": str(e)
            }
    
    def _build_context_from_history(self, history: List[Dict[str, Any]], current_query: str) -> str:
        """Build context string from conversation history."""
        if not history:
            return current_query
        
        # Include recent conversation context (last 10 messages)
        recent_history = history[-10:] if len(history) > 10 else history
        
        context_parts = []
        
        # Add conversation context
        if len(recent_history) > 1:  # More than just the current message
            context_parts.append("Contexto da conversa anterior:")
            for msg in recent_history[:-1]:  # Exclude the current message
                role_pt = "Usuário" if msg["role"] == "user" else "Assistente"
                context_parts.append(f"{role_pt}: {msg['content']}")
            context_parts.append("\nPergunta atual:")
        
        context_parts.append(current_query)
        
        return "\n".join(context_parts)
    
    async def _process_with_agent(self, context: str) -> str:
        """Process context with the agent and return response."""
        try:
            # Use the agent to process the context
            # Note: This is a simplified implementation. In a real scenario,
            # you might need to use the agent's streaming capabilities or
            # implement proper conversation management
            
            # For now, we'll use a mock implementation
            # In practice, you would call the agent's methods
            response = f"Processed by {self.agent.name}: {context[:100]}..."
            
            # Simulate some processing time
            await asyncio.sleep(0.1)
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing with agent: {e}")
            raise
    
    async def _process_with_agent_stream(self, context: str) -> AsyncGenerator[str, None]:
        """Process context with the agent and stream response."""
        try:
            # Simulate streaming response by breaking down the response
            response = f"Esta é uma resposta processada pelo agente {self.agent.name} para o contexto fornecido. O agente especializado em aprendizagem analisou sua pergunta e fornece uma resposta educativa e detalhada."
            
            words = response.split()
            for word in words:
                yield f"{word} "
                await asyncio.sleep(0.05)  # Simulate streaming delay
                
        except Exception as e:
            logger.error(f"Error streaming with agent: {e}")
            raise
    
    async def get_session_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Get conversation history for a session."""
        return await self.session_service.get_conversation_history(session_id)
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete a conversation session."""
        return await self.session_service.delete_session(session_id)
