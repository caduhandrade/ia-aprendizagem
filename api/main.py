
import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from config.settings import settings
from services.session_service import SessionService, InMemorySessionStorage
from services.agent_service import AgentService
from api.streaming import stream_agent_response

# Setup logging
logger = logging.getLogger(__name__)

# Initialize services
session_storage = InMemorySessionStorage()
session_service = SessionService(session_storage)
agent_service = AgentService(session_service)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for startup and shutdown."""
    # Startup
    logger.info(f"Starting {settings.app_name} in {settings.environment} mode")
    
    # Schedule periodic cleanup of expired sessions
    async def cleanup_sessions():
        while True:
            try:
                cleaned = await session_service.cleanup_expired_sessions(settings.session_timeout_hours)
                if cleaned > 0:
                    logger.info(f"Cleaned up {cleaned} expired sessions")
            except Exception as e:
                logger.error(f"Error during session cleanup: {e}")
            
            # Wait 1 hour before next cleanup
            await asyncio.sleep(3600)
    
    # Start cleanup task in background
    cleanup_task = asyncio.create_task(cleanup_sessions())
    
    yield
    
    # Shutdown
    logger.info(f"Shutting down {settings.app_name}")
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass


# FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="AI Learning Assistant API with conversation sessions",
    version="1.0.0",
    debug=settings.debug,
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class QueryRequest(BaseModel):
    """Request model for asking the agent."""
    query: str = Field(..., min_length=1, max_length=2000, description="User query")
    session_id: Optional[str] = Field(None, description="Optional session ID for conversation continuity")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Optional metadata")


class SessionResponse(BaseModel):
    """Response model for session operations."""
    session_id: str
    message: str
    

class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str
    version: str
    environment: str


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        environment=settings.environment
    )


@app.post("/ask")
async def ask_agent(request: QueryRequest):
    """Ask the agent a question with optional session continuity."""
    try:
        logger.info(f"Processing query for session: {request.session_id}")
        
        # Stream the response from the agent service
        return StreamingResponse(
            stream_agent_response(agent_service, request),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Cache-Control"
            }
        )
        
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/sessions", response_model=SessionResponse)
async def create_session():
    """Create a new conversation session."""
    try:
        session = await session_service.create_session()
        return SessionResponse(
            session_id=session.session_id,
            message="Session created successfully"
        )
    except Exception as e:
        logger.error(f"Error creating session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/sessions/{session_id}/history")
async def get_session_history(session_id: str):
    """Get conversation history for a session."""
    try:
        history = await agent_service.get_session_history(session_id)
        return {
            "session_id": session_id,
            "history": history
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting session history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/sessions/{session_id}", response_model=SessionResponse)
async def delete_session(session_id: str):
    """Delete a conversation session."""
    try:
        deleted = await agent_service.delete_session(session_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return SessionResponse(
            session_id=session_id,
            message="Session deleted successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.is_development,
        workers=1 if settings.is_development else settings.api_workers
    )
