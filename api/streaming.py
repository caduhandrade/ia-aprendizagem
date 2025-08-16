import json
import asyncio
import logging
from typing import AsyncGenerator, Dict, Any

from services.agent_service import AgentService

logger = logging.getLogger(__name__)


async def stream_agent_response(
    agent_service: AgentService, 
    request
) -> AsyncGenerator[str, None]:
    """Stream response from the agent service."""
    try:
        async for chunk_data in agent_service.process_query_stream(
            request.query,
            request.session_id,
            request.metadata
        ):
            if chunk_data.get("type") == "chunk":
                # Send content chunk
                yield f"data: {json.dumps({
                    'mime_type': 'text/plain',
                    'data': chunk_data['content'],
                    'session_id': chunk_data['session_id']
                })}\n\n"
                
            elif chunk_data.get("type") == "complete":
                # Send completion signal
                yield f"data: {json.dumps({
                    'turn_complete': True,
                    'interrupted': None,
                    'session_id': chunk_data['session_id'],
                    'metadata': chunk_data.get('metadata', {})
                })}\n\n"
                
            elif chunk_data.get("type") == "error":
                # Send error signal
                yield f"data: {json.dumps({
                    'error': True,
                    'message': chunk_data.get('error', 'Unknown error'),
                    'turn_complete': True,
                    'interrupted': True
                })}\n\n"
                
    except Exception as e:
        logger.error(f"Error in stream_agent_response: {e}")
        yield f"data: {json.dumps({
            'error': True,
            'message': f'Streaming error: {str(e)}',
            'turn_complete': True,
            'interrupted': True
        })}\n\n"


async def stream_response(response: str) -> AsyncGenerator[str, None]:
    """Legacy streaming function for backward compatibility."""
    words = response.split()
    for word in words:
        yield f"data: {json.dumps({'mime_type': 'text/plain', 'data': f'{word} '})}\n\n"
        await asyncio.sleep(0.1)
    yield f"data: {json.dumps({'turn_complete': True, 'interrupted': None})}\n\n"
