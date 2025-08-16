from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from services.agent_service import AgentService
import io
from typing import Optional
import docx2txt
import PyPDF2

router = APIRouter()

@router.post("/upload")
async def upload_resume(file: UploadFile = File(...), goal: Optional[str] = Form(None)):
    # Aceita apenas PDF ou DOCX
    if file.content_type not in ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]:
        raise HTTPException(status_code=400, detail="Apenas PDF ou DOCX são permitidos.")

    # Extrai texto do arquivo
    content = ""
    if file.content_type == "application/pdf":
        pdf_reader = PyPDF2.PdfReader(file.file)
        for page in pdf_reader.pages:
            content += page.extract_text() or ""
    elif file.content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        content = docx2txt.process(file.file)

    # Aqui você pode vetorizar se necessário
    # Passa para o agente junto com a meta
    agent = AgentService(None)  # Adapte para usar o agent_service correto
    result = await agent.analyze_resume_and_goal(content, goal)

    return JSONResponse({"result": result})
