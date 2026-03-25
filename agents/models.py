import os
from pathlib import Path
from dotenv import load_dotenv
from agno.agent import Agent
from agno.models.google import Gemini
from agno.guardrails import PromptInjectionGuardrail
from agents.schemas.ats import AtsAnalysis
from agents.schemas.resume import ResumeScheme
from agents.schemas.vacancy import VacancyKeyThemes
from agents.instructions import (
    VACANCY_AGENT_INSTRUCTIONS,
    RESUME_AGENT_INSTRUCTIONS,
    UPGRADE_RESUME_AGENT_INSTRUCTIONS,
    ENRICH_RESUME_INSTRUCTIONS,
    ATS_AGENT_INSTRUCTIONS,
)

# Carrega variáveis de ambiente
ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=Path(ENV_PATH))

# Configuração do LangSmith (Observabilidade)
if os.getenv("LANGSMITH_TRACING", "").lower() == "true":
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_ENDPOINT"] = os.getenv(
        "LANGSMITH_ENDPOINT", "https://api.smith.langchain.com"
    )
    os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGSMITH_API_KEY", "")
    os.environ["LANGCHAIN_PROJECT"] = os.getenv("LANGSMITH_PROJECT", "AdaptaAi")

# Configuração do Modelo e Guradrails
model_instance = Gemini(
    id="gemini-2.5-flash",
    api_key=os.getenv("GOOGLE_API_KEY"),
)
pi_guardrail = PromptInjectionGuardrail()


# Agents
vacancy_agent = Agent(
    name="vacancy_agent",
    description="Agente que analisa descrições de vagas",
    model=model_instance,
    instructions=VACANCY_AGENT_INSTRUCTIONS,
    output_schema=VacancyKeyThemes,
    debug_mode=True,
)

resume_agent = Agent(
    name="resume_agent",
    description="Agente que converte currículos para JSON",
    model=model_instance,
    instructions=RESUME_AGENT_INSTRUCTIONS,
    output_schema=ResumeScheme,
    debug_mode=True,
)

resume_upgrade_agent = Agent(
    name="resume_upgrade_agent",
    description="Agente que melhora currículos",
    model=model_instance,
    instructions=UPGRADE_RESUME_AGENT_INSTRUCTIONS,
    output_schema=ResumeScheme,
    debug_mode=True,
)

resume_enricher_agent = Agent(
    name="resume_enricher_agent",
    description="Agente que adiciona informações extras ao currículo",
    model=model_instance,
    instructions=ENRICH_RESUME_INSTRUCTIONS,
    output_schema=ResumeScheme,
    debug_mode=True,
)

ats_agent = Agent(
    name="ats_agent",
    description="Agente que analisa compatibilidade de currículo com vaga para ATS",
    model=model_instance,
    instructions=ATS_AGENT_INSTRUCTIONS,
    output_schema=AtsAnalysis,
    debug_mode=True,
)