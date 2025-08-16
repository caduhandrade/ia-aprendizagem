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
        metadata: Dict[str, Any] = None,
        file_data: Optional[Dict[str, str]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Process a query with streaming response."""
        try:
            # Get or create session
            session = await self.session_service.get_or_create_session(session_id)
            
            # Process file if provided
            enhanced_query = query
            if file_data:
                try:
                    file_content = await self._extract_file_content(file_data)
                    enhanced_query = f"""
Analise o currículo fornecido e com base na pergunta do usuário, forneça recomendações personalizadas de estudo e carreira.

CURRÍCULO:
{file_content}

PERGUNTA DO USUÁRIO:
{query}

Por favor, analise o currículo e forneça recomendações específicas para ajudar a pessoa a atingir seus objetivos, incluindo:
1. Habilidades que devem ser desenvolvidas
2. Cursos ou certificações recomendados
3. Áreas de melhoria identificadas no currículo
4. Estratégias de carreira baseadas no perfil atual
"""
                except Exception as e:
                    logger.error(f"Error processing file: {e}")
                    enhanced_query = f"{query}\n\n(Nota: Houve um erro ao processar o arquivo anexado)"
            
            # Add user message to session
            await self.session_service.add_message(
                session.session_id, 
                "user", 
                enhanced_query, 
                metadata or {}
            )
            
            # Prepare conversation context for the agent
            conversation_history = session.get_conversation_history()
            context = self._build_context_from_history(conversation_history, enhanced_query)
            
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
        """Process context with Gemini model via google.generativeai."""
        try:
            import google.generativeai as genai
            from config.settings import settings
            api_key = settings.google_api_key
            if not api_key:
                return "Erro: GOOGLE_API_KEY não configurada"
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-2.0-flash-exp')
            response = model.generate_content(context, stream=True)
            full_response = ""
            for chunk in response:
                if hasattr(chunk, 'text') and chunk.text:
                    full_response += chunk.text
            return full_response
        except Exception as e:
            logger.error(f"Error processing with Gemini: {e}")
            raise
    
    async def _process_with_agent_stream(self, context: str) -> AsyncGenerator[str, None]:
        """Process context with Gemini and stream response as SSE."""
        try:
            response = await self._process_with_agent(context)
            # Simula streaming SSE por palavra
            for word in response.split():
                yield word + " "
                await asyncio.sleep(0.05)
        except Exception as e:
            logger.error(f"Error streaming with Gemini: {e}")
            raise
    
    async def get_session_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Get conversation history for a session."""
        return await self.session_service.get_conversation_history(session_id)
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete a conversation session."""
        return await self.session_service.delete_session(session_id)

    async def _extract_file_content(self, file_data: Dict[str, str]) -> str:
        """Extract text content from uploaded file."""
        import base64
        import io
        import docx2txt
        import PyPDF2
        
        try:
            # Decode base64 content
            content_b64 = file_data["content"]
            if content_b64.startswith("data:"):
                content_b64 = content_b64.split(",")[1]
            
            file_bytes = base64.b64decode(content_b64)
            file_stream = io.BytesIO(file_bytes)
            
            # Extract text based on file type
            if file_data["type"] == "application/pdf":
                pdf_reader = PyPDF2.PdfReader(file_stream)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() or ""
                return text
            elif file_data["type"] == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                return docx2txt.process(file_stream)
            else:
                raise ValueError(f"Unsupported file type: {file_data['type']}")
                
        except Exception as e:
            logger.error(f"Error extracting file content: {e}")
            raise
