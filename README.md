# AdaptaAi - Backend

Backend da aplicação AdaptaAi, uma API para otimização de currículos com análise ATS e Human-in-the-Loop (HITL).

## 🚀 Tecnologias

- **FastAPI** - Framework web Python
- **SQLModel** - ORM para banco de dados
- **SQLite/PostgreSQL** - Banco de dados
- **Docker** - Containerização
- **LangSmith** - Observabilidade

## 📋 Pré-requisitos

- Python 3.11+
- Docker e Docker Compose (opcional)
- pip ou poetry

## ⚙️ Configuração

### 1. Clone o repositório

```bash
git clone <url-do-repositorio>
cd AdaptaAi-BACKEND
```

### 2. Crie o ambiente virtual

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

### 4. Configure as variáveis de ambiente

O arquivo `.env` já está configurado com os valores padrão. Para personalizar, edite o arquivo `.env`:

```env
# Database
DATABASE_URL=sqlite:///./database.db

# LangSmith (Observability)
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=sua-api-key
LANGSMITH_PROJECT=Adaptaai

# Google AI (Gemini)
GOOGLE_API_KEY=sua-api-key

# CORS
CORS_ORIGINS=http://localhost:5173,http://localhost:3000

# Server
HOST=0.0.0.0
PORT=8000
```

## 🏃‍♂️ Como Rodar

### Opção 1: Local (Desenvolvimento)

```bash
# Ative o ambiente virtual e execute
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

A API estará disponível em: **http://localhost:8000**

### Opção 2: Docker Compose (Produção com PostgreSQL)

```bash
docker-compose up --build
```

## 📚 Documentação da API

Após iniciar o servidor, acesse:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Endpoints Principais

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/` | Status do servidor |
| POST | `/api/v1/auth/register` | Registrar usuário |
| POST | `/api/v1/auth/login` | Login |
| POST | `/api/v1/resumes/` | Criar currículo |
| GET | `/api/v1/resumes/` | Listar currículos |
| POST | `/api/v1/resumes/{id}/analyze` | Analisar currículo |

## 🔗 Conexão com Front-end

O backend está configurado para aceitar requisições CORS do front-end rodando em:

- `http://localhost:5173` (Vite - Desenvolvimento)
- `http://localhost:3000` (React - Alternativa)

### Configuração CORS (app/main.py)

```python
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
```

## 🗄️ Banco de Dados

### SQLite (Desenvolvimento)

O banco SQLite é criado automaticamente na primeira execução em `database.db`.

### PostgreSQL (Produção)

Use Docker Compose para subir o PostgreSQL:

```bash
docker-compose up db
```

## 🧪 Testes

```bash
pytest
```

## 📁 Estrutura do Projeto

```
AdaptaAi-BACKEND/
├── app/
│   ├── api/          # Rotas da API
│   ├── core/         # Configurações principais
│   ├── db/           # Conexão com banco de dados
│   ├── models/       # Modelos de dados
│   ├── schemas/      # Schemas Pydantic
│   └── services/     # Serviços de negócio
├── agents/           # Agentes de IA
├── .env              # Variáveis de ambiente
├── compose.yaml      # Docker Compose
├── Dockerfile        # Configuração Docker
└── requirements.txt  # Dependências Python
```

## 🔑 Variáveis de Ambiente

| Variável | Descrição | Padrão |
|----------|-----------|--------|
| `DATABASE_URL` | URL de conexão com banco | `sqlite:///./database.db` |
| `DB_PASSWORD` | Senha do PostgreSQL | `adaptaai_secret_password` |
| `LANGSMITH_API_KEY` | API Key LangSmith | - |
| `GOOGLE_API_KEY` | API Key Google AI | - |
| `SECRET_KEY` | Chave secreta JWT | `adaptaai` |
| `CORS_ORIGINS` | Origens permitidas | `http://localhost:5173` |
| `PORT` | Porta do servidor | `8000` |

## 🤝 Integração com Front-end

Para mais detalhes sobre a integração, consulte o README do [Front-end](../Adapta-AI-FRONT-END/README.md).

## 📝 Licença

MIT
