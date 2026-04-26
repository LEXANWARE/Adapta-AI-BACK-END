# AdaptaAi - Backend

Backend da aplicação AdaptaAi, uma plataforma inteligente para otimização estratégica de currículos usando IA (Gemini), análise ATS avançada e auditoria de qualidade.

## 🚀 Tecnologias e Frameworks

- **FastAPI** - Framework web de alta performance.
- **Agno (Phidata)** - Framework para orquestração de Agentes de IA e Workflows.
- **Google Gemini (2.5 Flash)** - LLM para processamento de linguagem natural.
- **SQLModel** - ORM moderno para interação com banco de dados.
- **LangSmith** - Rastreamento e observabilidade da IA.
- **PyPDF** - Extração de texto de documentos PDF.

## 🧠 Arquitetura de IA (Agentes)

O sistema utiliza múltiplos agentes especializados com instruções rigorosas:

1.  **Vacancy Agent**: Extrai ferramentas, habilidades e frases-chave de descrições de vagas.
2.  **Resume Agent**: Converte currículos de texto livre para o formato **JSON Resume** estruturado.
3.  **Quality Agent**: Realiza auditoria 360º (Gramática, Branding, Senioridade Percebida e Escaneabilidade).
4.  **ATS Agent**: Calcula score de compatibilidade (0-100) e identifica lacunas técnicas/comportamentais.
5.  **Upgrade Agent**: Otimiza o currículo usando a **Metodologia STAR** (Situação, Tarefa, Ação, Resultado).
6.  **Enricher Agent**: Integra informações adicionais e links de perfis (LinkedIn/GitHub).

## 📋 Pré-requisitos

- Python 3.11+
- Google AI API Key (Gemini)
- SQLite (padrão) ou PostgreSQL

## ⚙️ Configuração

### 1. Instalação

```bash
python -m venv venv
source venv/bin/activate  # ou venv\Scripts\activate no Windows
pip install -r requirements.txt
```

### 2. Variáveis de Ambiente (.env)

```env
GOOGLE_API_KEY=sua-chave-gemini
DATABASE_URL=sqlite:///./database.db
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=sua-chave-langsmith
CORS_ORIGINS=http://localhost:5173
```

## 🏃‍♂️ Como Rodar

```bash
uvicorn app.main:app --reload
```

## 📚 Documentação da API (Endpoints Principais)

### Autenticação
- `POST /api/v1/auth/register`: Registro de usuário.
- `POST /api/v1/auth/login`: Login e obtenção de Token JWT.
- `GET /api/v1/auth/users/me`: Dados do usuário logado.

### Gestão de Currículos
- `POST /api/v1/resumes/upload`: Upload de PDF e extração de texto.
- `GET /api/v1/resumes/`: Lista currículos do usuário.
- `GET /api/v1/resumes/{id}`: Detalhes do currículo e dados processados.

### Inteligência e Otimização
- `POST /api/v1/resumes/analyze-quality`: Auditoria gramatical e de branding.
- `POST /api/v1/resumes/check-ats`: Cálculo de score e match de palavras-chave para uma vaga.
- `POST /api/v1/resumes/optimize`: Gera versão otimizada baseada em uma vaga.
- `POST /api/v1/resumes/full-pipeline`: Executa Quality → ATS → Optimize em sequência.
- `POST /api/v1/resumes/adapt-full`: Atalho para Upload de PDF + Pipeline completo.

## 📁 Estrutura do Projeto

```text
AdaptaAi-BACKEND/
├── agents/              # Inteligência Artificial
│   ├── schemas/        # Schemas Pydantic para saída dos agentes
│   ├── instructions.py # Prompts e regras de negócio da IA
│   ├── models.py       # Definição e configuração dos Agentes
│   └── workflow.py     # Orquestração de workflows lineares
├── app/
│   ├── api/v1/         # Endpoints e rotas da API
│   ├── core/           # Segurança (JWT) e configurações
│   ├── models/         # Modelos SQLModel (User, Resume)
│   └── services/       # Lógica de integração Workflow-API
├── database.db         # Banco de dados local (SQLite)
└── requirements.txt    # Dependências do projeto
```

## 🛡️ Diferenciais Técnicos

- **Metodologia STAR**: A IA reescreve conquistas focando em resultados mensuráveis.
- **Humanização**: Análise de voluntariado e indicadores de impacto social.
- **Validação de Schema**: Todas as saídas da IA são validadas via Pydantic para garantir integridade.
- **Observabilidade**: Integração nativa com LangSmith para monitorar performance dos agentes.

## 📝 Licença

MIT
