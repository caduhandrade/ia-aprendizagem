# Imagem base Python
FROM python:3.13-slim

# Diretório de trabalho
WORKDIR /app

# Copia os arquivos do projeto
COPY . /app

# Instala dependências
RUN pip install --upgrade pip \
    && pip install fastapi uvicorn python-dotenv pydantic google-generativeai google-adk

# Expõe portas altas e pouco comuns para FastAPI e ADK Web
EXPOSE 49152
EXPOSE 49153

# Comando padrão para rodar FastAPI
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "49152"]
