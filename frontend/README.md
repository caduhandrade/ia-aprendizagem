# Frontend - Assistente de Aprendizagem

Este é o frontend do chatbot de IA para auxiliar no aprendizado, construído com Next.js, TypeScript e Tailwind CSS.

## Funcionalidades

- 🤖 **Interface de chatbot moderna** com design responsivo
- 💬 **Múltiplas sessões de conversa** com histórico preservado
- 🔄 **Streaming em tempo real** via Server-Sent Events (SSE)
- 💾 **Gerenciamento de sessões em memória**
- ⚡ **Loading state** com indicador "PENSANDO..."
- 🎨 **Design clean** com Tailwind CSS

## Instalação e Execução

### Pré-requisitos

- Node.js 18+ 
- npm ou yarn

### Configuração

1. **Instale as dependências:**
   ```bash
   cd frontend
   npm install
   ```

2. **Configure as variáveis de ambiente:**
   
   Crie um arquivo `.env.local` na pasta `frontend` com:
   ```env
   NEXT_PUBLIC_API_URL=http://localhost:49152
   ```

   > **Nota:** Ajuste a URL conforme a configuração do seu backend.

3. **Execute o servidor de desenvolvimento:**
   ```bash
   npm run dev
   ```

4. **Acesse a aplicação:**
   
   Abra [http://localhost:3000](http://localhost:3000) no seu navegador.

## Como Usar

### Criando uma Nova Conversa

1. Clique no botão **"Nova Conversa"** na barra lateral
2. Uma nova sessão será criada e você poderá começar a conversar

### Enviando Mensagens

1. Digite sua pergunta no campo de texto na parte inferior
2. Pressione **Enter** ou clique no botão de enviar
3. Aguarde a resposta do assistente (verá "PENSANDO..." durante o processamento)

### Navegando entre Conversas

- Clique em qualquer conversa na barra lateral para visualizar seu histórico
- O número de mensagens é exibido para cada sessão
- O histórico de todas as conversas é preservado na memória

## Estrutura do Projeto

```
frontend/
├── src/
│   ├── app/
│   │   ├── layout.tsx      # Layout principal da aplicação
│   │   ├── page.tsx        # Página inicial (chatbot)
│   │   └── globals.css     # Estilos globais
│   └── components/
│       └── ChatBot.tsx     # Componente principal do chatbot
├── .env.local              # Configuração de ambiente (local)
├── package.json            # Dependências e scripts
└── README.md              # Este arquivo
```

## Tecnologias Utilizadas

- **Next.js 15** - Framework React para aplicações web
- **TypeScript** - Tipagem estática para JavaScript
- **Tailwind CSS** - Framework CSS utilitário
- **Lucide React** - Biblioteca de ícones
- **Server-Sent Events (SSE)** - Para streaming de respostas em tempo real

## API Integration

O frontend se conecta ao backend FastAPI através de:

- **Endpoint:** `POST /ask`
- **Formato:** Server-Sent Events (SSE)
- **Dados:** `{"query": "sua pergunta"}`

### Formato das Respostas SSE

```
data: {"mime_type": "text/plain", "data": "palavra "}
data: {"turn_complete": true, "interrupted": null}
```

## Desenvolvimento

### Scripts Disponíveis

- `npm run dev` - Inicia o servidor de desenvolvimento
- `npm run build` - Gera build de produção
- `npm run start` - Inicia o servidor de produção
- `npm run lint` - Executa verificação de código

### Estrutura de Dados

#### Mensagem
```typescript
interface Message {
  id: string;
  content: string;
  sender: 'user' | 'bot';
  timestamp: Date;
}
```

#### Sessão
```typescript
interface Session {
  id: string;
  name: string;
  messages: Message[];
  createdAt: Date;
}
```

## Próximos Passos

- [ ] Implementar persistência de dados no localStorage/banco
- [ ] Adicionar autenticação de usuários
- [ ] Melhorar a responsividade mobile
- [ ] Adicionar export/import de conversas
- [ ] Implementar busca no histórico de conversas
