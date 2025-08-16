"use client";

import { useState, useRef, useEffect } from "react";
import { Send, Bot, User } from "lucide-react";

// Types
interface Message {
  id: string;
  content: string;
  sender: "user" | "bot";
  timestamp: Date;
}

interface Session {
  id: string;
  name: string;
  messages: Message[];
  createdAt: Date;
}

export default function ChatBot() {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [inputValue, setInputValue] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [streamingMessage, setStreamingMessage] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const API_URL =
    "https://pocadk-apiadk-wo9w6w-759b4d-103-199-184-68.traefik.me";

  // Get current session
  const currentSession = sessions.find((s) => s.id === currentSessionId);

  // Auto-scroll to bottom
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [currentSession?.messages, streamingMessage]);

  // Create new session
  const createNewSession = () => {
    const newSession: Session = {
      id: Date.now().toString(),
      name: `Conversa ${sessions.length + 1}`,
      messages: [],
      createdAt: new Date(),
    };
    setSessions((prev) => [...prev, newSession]);
    setCurrentSessionId(newSession.id);
    return newSession;
  };

  // Initialize first session
  useEffect(() => {
    if (sessions.length === 0) {
      createNewSession();
    }
  }, []);

  // Send message
  const sendMessage = async () => {
    if (!inputValue.trim() || isLoading) return;

    let session = currentSession;
    if (!session) {
      session = createNewSession();
    }
    // Guarda o id original da sessão para referência
    const originalSessionId = session.id;

    const userMessage: Message = {
      id: Date.now().toString(),
      content: inputValue.trim(),
      sender: "user",
      timestamp: new Date(),
    };

    // Add user message
    setSessions((prev) =>
      prev.map((s) =>
        s.id === originalSessionId
          ? { ...s, messages: [...s.messages, userMessage] }
          : s
      )
    );

    const query = inputValue.trim();
    setInputValue("");
    setIsLoading(true);
    setStreamingMessage("");

    try {
      // Prepara o payload base
      const bodyPayload: any = { query };

      // Se a sessão já tem mensagens (não é a primeira pergunta), envia o session_id
      if (session && session.messages.length >= 2) {
        bodyPayload.session_id = originalSessionId;
      }

      const response = await fetch(`${API_URL}/ask`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(bodyPayload),
      });

      if (!response.body) {
        throw new Error("No response body");
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let accumulatedMessage = "";
      let capturedSessionId: string | null = null; // Armazena o session_id capturado

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split("\n");

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            const data = line.slice(6);
            try {
              const parsed = JSON.parse(data);

              // Captura session_id no primeiro chunk que contém, mas não atualiza estado ainda
              if (parsed.session_id && !capturedSessionId) {
                capturedSessionId = parsed.session_id;
              }

              if (parsed.data) {
                accumulatedMessage += parsed.data;
                setStreamingMessage(accumulatedMessage);
              } else if (parsed.turn_complete) {
                // Agora sim atualiza o estado com o session_id capturado
                let finalSessionId = capturedSessionId || originalSessionId;
                if (finalSessionId !== originalSessionId) {
                  setCurrentSessionId(finalSessionId);
                }
                setSessions((prev) =>
                  prev.map((s) =>
                    s.id === originalSessionId
                      ? {
                          ...s,
                          id: finalSessionId,
                          messages: [
                            ...s.messages,
                            {
                              id: (Date.now() + 1).toString(),
                              content: accumulatedMessage.trim(),
                              sender: "bot",
                              timestamp: new Date(),
                            },
                          ],
                        }
                      : s
                  )
                );

                setStreamingMessage("");
                setIsLoading(false);
                return;
              }
            } catch (e) {
              // Silently ignore JSON parse errors
            }
          }
        }
      }
    } catch (error) {
      setIsLoading(false);
      setStreamingMessage("");

      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        content:
          "Erro ao conectar com o servidor. Verifique se a API está rodando.",
        sender: "bot",
        timestamp: new Date(),
      };

      setSessions((prev) =>
        prev.map((s) =>
          s.id === session!.id
            ? { ...s, messages: [...s.messages, errorMessage] }
            : s
        )
      );
    }
  };

  // Handle Enter key
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <div className="w-64 bg-white border-r border-gray-200 flex flex-col">
        <div className="p-4 border-b border-gray-200">
          <button
            onClick={createNewSession}
            className="w-full bg-blue-600 text-white rounded-lg px-4 py-2 hover:bg-blue-700 transition-colors"
          >
            Nova Conversa
          </button>
        </div>

        <div className="flex-1 overflow-y-auto">
          {sessions.map((session) => (
            <div
              key={session.id}
              className={`p-3 cursor-pointer border-b border-gray-100 hover:bg-gray-50 ${
                currentSessionId === session.id
                  ? "bg-blue-50 border-blue-200"
                  : ""
              }`}
              onClick={() => setCurrentSessionId(session.id)}
            >
              <div className="font-medium text-sm text-gray-900">
                {session.name}
              </div>
              <div className="text-xs text-gray-500 mt-1">
                {session.messages.length} mensagens
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="bg-white border-b border-gray-200 px-6 py-4">
          <div className="flex items-center">
            <Bot className="w-6 h-6 text-blue-600 mr-3" />
            <h1 className="text-xl font-semibold text-gray-900">
              Assistente de Aprendizagem
            </h1>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {currentSession ? (
            <>
              {currentSession.messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex ${
                    message.sender === "user" ? "justify-end" : "justify-start"
                  }`}
                >
                  <div
                    className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                      message.sender === "user"
                        ? "bg-blue-600 text-white"
                        : "bg-white border border-gray-200 text-gray-900"
                    }`}
                  >
                    <div className="flex items-start space-x-2">
                      {message.sender === "bot" && (
                        <Bot className="w-4 h-4 mt-0.5 text-blue-600 flex-shrink-0" />
                      )}
                      {message.sender === "user" && (
                        <User className="w-4 h-4 mt-0.5 text-white flex-shrink-0" />
                      )}
                      <div className="whitespace-pre-wrap text-sm">
                        {message.content}
                      </div>
                    </div>
                  </div>
                </div>
              ))}

              {/* Streaming message */}
              {streamingMessage && (
                <div className="flex justify-start">
                  <div className="max-w-xs lg:max-w-md px-4 py-2 rounded-lg bg-white border border-gray-200 text-gray-900">
                    <div className="flex items-start space-x-2">
                      <Bot className="w-4 h-4 mt-0.5 text-blue-600 flex-shrink-0" />
                      <div className="whitespace-pre-wrap text-sm">
                        {streamingMessage}
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Loading indicator */}
              {isLoading && !streamingMessage && (
                <div className="flex justify-start">
                  <div className="max-w-xs lg:max-w-md px-4 py-2 rounded-lg bg-white border border-gray-200 text-gray-900">
                    <div className="flex items-start space-x-2">
                      <Bot className="w-4 h-4 mt-0.5 text-blue-600 flex-shrink-0" />
                      <div className="text-sm text-gray-500">
                        <span className="animate-pulse">PENSANDO...</span>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </>
          ) : (
            <div className="text-center text-gray-500 mt-8">
              Selecione uma conversa ou crie uma nova para começar
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="bg-white border-t border-gray-200 p-4">
          <div className="flex space-x-4">
            <textarea
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={handleKeyPress}
              placeholder="Digite sua pergunta..."
              className="flex-1 border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
              rows={1}
              disabled={isLoading}
            />
            <button
              onClick={sendMessage}
              disabled={!inputValue.trim() || isLoading}
              className="bg-blue-600 text-white rounded-lg px-4 py-2 hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
            >
              <Send className="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
