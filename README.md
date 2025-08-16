# Instalação e Execução

1. Instale o gerenciador de pacotes uv:
	```sh
	pip install uv
	```

2. Crie e ative o ambiente virtual:
	```sh
	python -m venv .venv
	source .venv/bin/activate
	```

3. Instale as dependências do projeto:
	```sh
	uv pip install -r requirements.txt
	# ou
	uv add fastapi uvicorn python-dotenv pydantic google-generativeai google-adk
	```

4. Rode a aplicação FastAPI:
	```sh
	uvicorn api.main:app --reload --port 49152
	```

5. (Opcional) Rode o ADK Web:
	```sh
	adk web
	```
