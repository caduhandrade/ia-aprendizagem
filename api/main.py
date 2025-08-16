
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import google.generativeai as genai
from agents import root_agent
from config.settings import settings
from api.streaming import stream_response

class QueryRequest(BaseModel):
    query: str

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_agent_response(query: str) -> str:
    api_key = settings.GOOGLE_API_KEY
    if not api_key:
        return "Erro: GOOGLE_API_KEY não configurada"
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.0-flash-exp')
    response = model.generate_content(query, stream=True)
    full_response = ""
    for chunk in response:
        if chunk.text:
            full_response += chunk.text
    return full_response

@app.post("/ask")
async def ask_agent(request: QueryRequest):
    response = await asyncio.to_thread(get_agent_response, request.query)
    return StreamingResponse(
        stream_response(response),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control"
        }
    )
