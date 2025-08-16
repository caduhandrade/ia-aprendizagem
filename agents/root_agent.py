from google.adk.agents import Agent
from google.adk.tools import google_search

root_agent = Agent(
    name="learning_specialist",
    model="gemini-2.0-flash-live-001",
    description="Você é um agente especialista em aprendizagem, capaz de buscar e explicar conteúdos educacionais usando o Google.",
    instruction="""Você é um agente especialista em aprendizagem. Use a ferramenta google_search para buscar informações relevantes e explique de forma clara e didática para o usuário.""",
    tools=[google_search]
)
