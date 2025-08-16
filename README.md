# IA Aprendizagem - AI Learning Assistant

Uma API moderna e escalável para assistência de aprendizagem com IA, construída com FastAPI, Google ADK e arquitetura limpa.

## 🚀 Características

- **Sessões de Conversa**: Mantenha o contexto das conversações com gerenciamento automático de sessões
- **Streaming em Tempo Real**: Respostas em streaming para melhor experiência do usuário
- **Arquitetura Limpa**: Padrão de serviços com injeção de dependência e separação de responsabilidades
- **Google ADK Integration**: Integração nativa com Google AI Development Kit
- **Testes Abrangentes**: 47+ testes unitários e de integração
- **Configuração Robusta**: Validação de configurações com Pydantic
- **Logging Estruturado**: Sistema de logs com diferentes níveis por ambiente

## 📋 Pré-requisitos

- Python 3.12+
- Google API Key para Generative AI
- UV package manager (recomendado) ou pip

## 🛠️ Instalação e Execução

### 1. Clone o repositório
```bash
git clone <repository-url>
cd ia-aprendizagem
```

### 2. Instale o gerenciador de pacotes UV
```bash
pip install uv
```

### 3. Crie e ative o ambiente virtual
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# ou
.venv\Scripts\activate  # Windows
```

### 4. Instale as dependências
```bash
uv pip install -r requirements.txt
# ou usando pip
pip install fastapi uvicorn python-dotenv pydantic google-generativeai google-adk pytest pytest-asyncio httpx pydantic-settings
```

### 5. Configure as variáveis de ambiente
Crie um arquivo `.env` na raiz do projeto:
```env
GOOGLE_API_KEY=your_google_api_key_here
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO
API_HOST=0.0.0.0
API_PORT=49152
SESSION_TIMEOUT_HOURS=24
CORS_ORIGINS=*
```

### 6. Execute a aplicação
```bash
uvicorn api.main:app --reload --port 49152
```

### 7. (Opcional) Execute o ADK Web Interface
```bash
adk web
```

## 🧪 Executando os Testes

```bash
# Executar todos os testes
pytest

# Executar testes com cobertura
pytest --cov=services --cov=api

# Executar testes específicos
pytest tests/test_session_service.py -v
pytest tests/test_agent_service.py -v
pytest tests/test_api.py -v
```

## 📡 API Endpoints

### Health Check
```http
GET /health
```
Retorna o status da aplicação.

**Resposta:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "environment": "development"
}
```

### Criar Sessão
```http
POST /sessions
```
Cria uma nova sessão de conversa.

**Resposta:**
```json
{
  "session_id": "uuid-here",
  "message": "Session created successfully"
}
```

### Fazer Pergunta
```http
POST /ask
Content-Type: application/json

{
  "query": "Sua pergunta aqui",
  "session_id": "optional-session-id",
  "metadata": {
    "optional": "metadata"
  }
}
```

**Resposta:** Server-Sent Events (SSE) stream
```
data: {"mime_type": "text/plain", "data": "palavra ", "session_id": "uuid"}

data: {"turn_complete": true, "session_id": "uuid", "metadata": {...}}
```

### Histórico da Sessão
```http
GET /sessions/{session_id}/history
```

**Resposta:**
```json
{
  "session_id": "uuid",
  "history": [
    {
      "role": "user",
      "content": "Pergunta do usuário",
      "timestamp": "2025-08-16T01:22:08.209517"
    },
    {
      "role": "assistant", 
      "content": "Resposta do assistente",
      "timestamp": "2025-08-16T01:22:09.572755"
    }
  ]
}
```

### Deletar Sessão
```http
DELETE /sessions/{session_id}
```

## 💡 Exemplos de Uso

### Exemplo com cURL

1. **Criar uma sessão:**
```bash
curl -X POST "http://localhost:49152/sessions"
```

2. **Fazer uma pergunta:**
```bash
curl -X POST "http://localhost:49152/ask" \
  -H "Content-Type: application/json" \
  -d '{"query":"Explique o que é inteligência artificial"}'
```

3. **Continuar a conversa:**
```bash
curl -X POST "http://localhost:49152/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "query":"Pode dar exemplos práticos?",
    "session_id":"sua-session-id-aqui"
  }'
```

4. **Ver histórico:**
```bash
curl "http://localhost:49152/sessions/sua-session-id-aqui/history"
```

### Exemplo com Python

```python
import requests
import json

# Criar sessão
response = requests.post("http://localhost:49152/sessions")
session_id = response.json()["session_id"]

# Fazer pergunta com streaming
def ask_question(query, session_id=None):
    payload = {"query": query}
    if session_id:
        payload["session_id"] = session_id
    
    response = requests.post(
        "http://localhost:49152/ask",
        json=payload,
        stream=True
    )
    
    for line in response.iter_lines():
        if line:
            data_line = line.decode('utf-8')
            if data_line.startswith('data: '):
                event_data = json.loads(data_line[6:])
                if event_data.get('turn_complete'):
                    return event_data['session_id']
                elif 'data' in event_data:
                    print(event_data['data'], end='')

# Primeira pergunta
session = ask_question("O que é aprendizado de máquina?")

# Pergunta de follow-up
ask_question("Pode dar exemplos?", session)

# Ver histórico
history = requests.get(f"http://localhost:49152/sessions/{session}/history")
print(json.dumps(history.json(), indent=2))
```

## 🏗️ Arquitetura

A aplicação segue os princípios de arquitetura limpa:

```
├── api/                    # Camada de apresentação
│   ├── main.py            # FastAPI app e endpoints
│   └── streaming.py       # Utilitários de streaming
├── services/              # Camada de serviços
│   ├── session_service.py # Gerenciamento de sessões
│   └── agent_service.py   # Integração com agentes IA
├── agents/                # Configuração dos agentes
│   └── root_agent.py      # Agente principal com Google ADK
├── config/                # Configurações
│   └── settings.py        # Settings com Pydantic
└── tests/                 # Testes automatizados
    ├── test_session_service.py
    ├── test_agent_service.py
    └── test_api.py
```

### Componentes Principais

- **SessionService**: Gerencia sessões de conversa com armazenamento em memória
- **AgentService**: Integra com o Google ADK para processamento de consultas
- **StreamingResponse**: Fornece respostas em tempo real via Server-Sent Events
- **Settings**: Configuração validada com Pydantic e suporte a múltiplos ambientes

## 🐳 Docker

### Construir e executar com Docker:
```bash
docker build -t ia-aprendizagem .
docker run -p 49152:49152 -e GOOGLE_API_KEY=your_key_here ia-aprendizagem
```

## ⚙️ Configuração

Variáveis de ambiente disponíveis:

| Variável | Padrão | Descrição |
|----------|---------|-----------|
| `GOOGLE_API_KEY` | - | **Obrigatório**: Chave da API do Google |
| `ENVIRONMENT` | development | Ambiente (development/staging/production) |
| `DEBUG` | false | Ativar modo debug |
| `LOG_LEVEL` | INFO | Nível de log (DEBUG/INFO/WARNING/ERROR) |
| `API_HOST` | 0.0.0.0 | Host da API |
| `API_PORT` | 49152 | Porta da API |
| `SESSION_TIMEOUT_HOURS` | 24 | Timeout das sessões em horas |
| `CORS_ORIGINS` | * | Origens permitidas pelo CORS |

## 🤝 Contribuindo

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para detalhes.

## 🔧 Solução de Problemas

### Erro: "GOOGLE_API_KEY não configurada"
- Certifique-se de que definiu a variável `GOOGLE_API_KEY` no arquivo `.env`
- Verifique se o arquivo `.env` está na raiz do projeto

### Erro de porta em uso
- Mude a porta na variável `API_PORT` ou use `--port` diferente
- Verifique se não há outra instância rodando

### Problemas com dependências
- Use `uv pip install` em vez de `pip install`
- Certifique-se de estar no ambiente virtual ativado
- Limpe o cache: `pip cache purge`

## 📈 Roadmap

- [ ] Implementar armazenamento persistente (Redis/PostgreSQL)
- [ ] Adicionar autenticação e autorização
- [ ] Métricas e monitoramento com Prometheus
- [ ] Rate limiting e throttling
- [ ] Suporte a múltiplos agentes especializados
- [ ] Interface web para interação
- [ ] Integração com mais modelos de IA
