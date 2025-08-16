import json
import asyncio
from fastapi.responses import StreamingResponse

async def stream_response(response: str):
    words = response.split()
    for word in words:
        yield f"data: {json.dumps({'mime_type': 'text/plain', 'data': f'{word} '})}\n\n"
        await asyncio.sleep(0.1)
    yield f"data: {json.dumps({'turn_complete': True, 'interrupted': None})}\n\n"
