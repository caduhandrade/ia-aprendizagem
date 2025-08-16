# Sistema de IA para Aprendizagem

Sistema completo com chatbot de IA para auxiliar no aprendizado, composto por:
- **Backend**: API FastAPI com streaming em tempo real via Server-Sent Events
- **Frontend**: Interface moderna em Next.js com TypeScript e Tailwind CSS

## 🚀 Início Rápido

### Opção 1: Executar Tudo Automaticamente (Recomendado)

```bash
# 1. Instalar dependências completas
npm run install:all

# 2. Executar backend + frontend simultaneamente
npm run dev
```

### Opção 2: Executar Separadamente

#### Backend (API FastAPI)

1. **Instale o gerenciador de pacotes uv:**
   ```sh
   pip install uv
   ```

2. **Crie e ative o ambiente virtual:**
   ```sh
   python -m venv .venv
   source .venv/bin/activate
   ```

3. **Instale as dependências do projeto:**
   ```sh
   uv pip install -r pyproject.toml
   ```

4. **Configure as variáveis de ambiente:**
   ```sh
   # Crie um arquivo .env com sua chave da API do Google
   echo "GOOGLE_API_KEY=sua_chave_aqui" > .env
   ```

5. **Execute a API FastAPI:**
   ```sh
   uvicorn api.main:app --reload --port 49152
   ```

#### Frontend (Next.js)

1. **Entre na pasta do frontend:**
   ```sh
   cd frontend
   ```

2. **Instale as dependências:**
   ```sh
   npm install
   ```

3. **Configure as variáveis de ambiente:**
   ```sh
   # O arquivo .env.local já está configurado com:
   # NEXT_PUBLIC_API_URL=http://localhost:49152
   ```

4. **Execute o frontend:**
   ```sh
   npm run dev
   ```

5. **Acesse a aplicação:**
   
   Abra [http://localhost:3000](http://localhost:3000) no navegador

## 📁 Estrutura do Projeto

```
ia-aprendizagem/
├── api/                    # Backend FastAPI
│   ├── main.py            # Endpoint principal com SSE
│   └── streaming.py       # Lógica de streaming
├── frontend/              # Frontend Next.js
│   ├── src/
│   │   ├── app/           # Páginas Next.js
│   │   └── components/    # Componentes React
│   ├── .env.local         # Configuração do frontend
│   └── README.md          # Documentação do frontend
├── agents/                # Agentes de IA
├── config/                # Configurações
├── .env                   # Variáveis de ambiente do backend
├── pyproject.toml         # Dependências Python
└── README.md              # Este arquivo
```

## 🔧 Configuração

### Variáveis de Ambiente

#### Backend (.env)
```env
GOOGLE_API_KEY=sua_chave_da_api_google
```

#### Frontend (.env.local)
```env
NEXT_PUBLIC_API_URL=http://localhost:49152
```

## 🎯 Funcionalidades

### Backend
- ✅ API FastAPI com endpoint `/ask`
- ✅ Streaming de respostas via Server-Sent Events (SSE)
- ✅ Integração com Google Generative AI
- ✅ CORS configurado para frontend
- ✅ Processamento word-by-word para UX fluida

### Frontend
- ✅ Interface de chatbot moderna e responsiva
- ✅ Múltiplas sessões de conversa
- ✅ Histórico preservado em memória
- ✅ Loading state com "PENSANDO..."
- ✅ Navegação entre conversas
- ✅ Design clean com Tailwind CSS
- ✅ Ícones com Lucide React

## 🛠️ Tecnologias

### Backend
- **FastAPI** - Framework web moderno para Python
- **Google Generative AI** - Modelo Gemini para IA
- **Uvicorn** - Servidor ASGI
- **Pydantic** - Validação de dados

### Frontend  
- **Next.js 15** - Framework React
- **TypeScript** - Tipagem estática
- **Tailwind CSS** - Framework CSS utilitário
- **Lucide React** - Biblioteca de ícones

## 🧪 Testando a Integração

1. **Inicie ambos os serviços** (backend e frontend)
2. **Acesse** http://localhost:3000
3. **Clique em "Nova Conversa"**
4. **Digite uma pergunta** no campo de texto
5. **Observe** o streaming da resposta em tempo real

## 📝 Scripts Disponíveis

```bash
# Instalar todas as dependências
npm run install:all

# Executar backend + frontend
npm run dev

# Executar apenas o backend
npm run dev:api

# Executar apenas o frontend  
npm run dev:frontend
```

## 🔮 Próximos Passos

- [ ] Implementar persistência de dados
- [ ] Adicionar autenticação de usuários
- [ ] Melhorar responsividade mobile
- [ ] Deploy para produção
- [ ] Testes automatizados
- [ ] Métricas e monitoramento

## (Opcional) ADK Web

Para usar o ADK Web:
```sh
adk web
```
