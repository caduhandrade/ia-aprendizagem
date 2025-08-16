#!/usr/bin/env python3
"""
Example client for the IA Aprendizagem API.

This script demonstrates how to interact with the API for conversation sessions.
"""

import requests
import json
import time
from typing import Optional


class IAAprendizagemClient:
    """Client for interacting with the IA Aprendizagem API."""
    
    def __init__(self, base_url: str = "http://localhost:49152"):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
    
    def create_session(self) -> str:
        """Create a new conversation session."""
        response = self.session.post(f"{self.base_url}/sessions")
        response.raise_for_status()
        return response.json()["session_id"]
    
    def ask_question(self, query: str, session_id: Optional[str] = None, metadata: dict = None) -> str:
        """Ask a question and get the complete response."""
        payload = {"query": query}
        if session_id:
            payload["session_id"] = session_id
        if metadata:
            payload["metadata"] = metadata
        
        response = self.session.post(
            f"{self.base_url}/ask",
            json=payload,
            stream=True
        )
        response.raise_for_status()
        
        full_response = ""
        current_session_id = None
        
        for line in response.iter_lines():
            if line:
                data_line = line.decode('utf-8')
                if data_line.startswith('data: '):
                    try:
                        event_data = json.loads(data_line[6:])
                        
                        if event_data.get('turn_complete'):
                            current_session_id = event_data.get('session_id')
                            break
                        elif 'data' in event_data:
                            full_response += event_data['data']
                            current_session_id = event_data.get('session_id')
                            
                    except json.JSONDecodeError:
                        continue
        
        return full_response.strip(), current_session_id
    
    def ask_question_streaming(self, query: str, session_id: Optional[str] = None):
        """Ask a question with streaming output."""
        payload = {"query": query}
        if session_id:
            payload["session_id"] = session_id
        
        response = self.session.post(
            f"{self.base_url}/ask",
            json=payload,
            stream=True
        )
        response.raise_for_status()
        
        print(f"🤖 Assistente: ", end="", flush=True)
        
        for line in response.iter_lines():
            if line:
                data_line = line.decode('utf-8')
                if data_line.startswith('data: '):
                    try:
                        event_data = json.loads(data_line[6:])
                        
                        if event_data.get('turn_complete'):
                            print()  # New line
                            return event_data.get('session_id')
                        elif 'data' in event_data:
                            print(event_data['data'], end="", flush=True)
                            
                    except json.JSONDecodeError:
                        continue
    
    def get_session_history(self, session_id: str) -> list:
        """Get conversation history for a session."""
        response = self.session.get(f"{self.base_url}/sessions/{session_id}/history")
        response.raise_for_status()
        return response.json()["history"]
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a conversation session."""
        response = self.session.delete(f"{self.base_url}/sessions/{session_id}")
        return response.status_code == 200
    
    def health_check(self) -> dict:
        """Check API health."""
        response = self.session.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()


def interactive_conversation():
    """Interactive conversation with the AI assistant."""
    client = IAAprendizagemClient()
    
    # Check if API is healthy
    try:
        health = client.health_check()
        print(f"✅ API Status: {health['status']} (v{health['version']})")
    except requests.RequestException as e:
        print(f"❌ API não está disponível: {e}")
        return
    
    # Create a new session
    try:
        session_id = client.create_session()
        print(f"🆕 Nova sessão criada: {session_id[:8]}...")
    except requests.RequestException as e:
        print(f"❌ Erro ao criar sessão: {e}")
        return
    
    print("\n💬 Conversa iniciada! Digite 'quit' para sair, 'history' para ver histórico.\n")
    
    while True:
        try:
            user_input = input("👤 Você: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'sair']:
                break
            elif user_input.lower() in ['history', 'histórico', 'historico']:
                history = client.get_session_history(session_id)
                print("\n📜 Histórico da conversa:")
                for i, msg in enumerate(history, 1):
                    role = "👤 Você" if msg["role"] == "user" else "🤖 Assistente"
                    print(f"{i}. {role}: {msg['content']}")
                print()
                continue
            elif not user_input:
                continue
            
            # Ask question with streaming
            session_id = client.ask_question_streaming(user_input, session_id)
            print()  # Extra line for readability
            
        except KeyboardInterrupt:
            print("\n\n👋 Conversa interrompida.")
            break
        except requests.RequestException as e:
            print(f"❌ Erro na requisição: {e}")
            break
    
    # Clean up
    try:
        client.delete_session(session_id)
        print(f"🗑️ Sessão {session_id[:8]}... deletada.")
    except:
        pass


def example_programmatic_usage():
    """Example of programmatic usage."""
    client = IAAprendizagemClient()
    
    print("🤖 Exemplo de uso programático")
    print("=" * 40)
    
    # Create session
    session_id = client.create_session()
    print(f"Sessão criada: {session_id}")
    
    # Ask questions
    questions = [
        "O que é inteligência artificial?",
        "Quais são as principais aplicações?",
        "Como posso começar a estudar IA?"
    ]
    
    for i, question in enumerate(questions, 1):
        print(f"\n{i}. Pergunta: {question}")
        response, session_id = client.ask_question(question, session_id)
        print(f"   Resposta: {response[:100]}...")
    
    # Show full history
    print("\n📜 Histórico completo:")
    history = client.get_session_history(session_id)
    for msg in history:
        role = "Usuário" if msg["role"] == "user" else "Assistente"
        print(f"- {role}: {msg['content'][:50]}...")
    
    # Clean up
    client.delete_session(session_id)
    print(f"\n✅ Sessão deletada.")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--example":
        example_programmatic_usage()
    else:
        interactive_conversation()