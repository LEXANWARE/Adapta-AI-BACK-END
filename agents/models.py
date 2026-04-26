import os
from pathlib import Path
from dotenv import load_dotenv
from agno.agent import Agent
from agno.models.google import Gemini
from agno.guardrails import PromptInjectionGuardrail
from agents.schemas.ats import AtsAnalysis
from agents.schemas.resume import ResumeScheme
from agents.schemas.vacancy import VacancyKeyThemes
from agents.schemas.quality import ResumeQualityAnalysis
from agents.schemas.ats import AtsAnalysis
from agents.instructions import (
    VACANCY_AGENT_INSTRUCTIONS,
    RESUME_AGENT_INSTRUCTIONS,
    UPGRADE_RESUME_AGENT_INSTRUCTIONS,
    ENRICH_RESUME_INSTRUCTIONS,
    ATS_AGENT_INSTRUCTIONS,
    QUALITY_AGENT_INSTRUCTIONS
)

# Carrega variáveis de ambiente
ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=Path(ENV_PATH))

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
    pre_hooks=[pi_guardrail],
    debug_mode=True,
)

resume_agent = Agent(
    name="resume_agent",
    description="Agente que converte currículos para JSON",
    model=model_instance,
    instructions=RESUME_AGENT_INSTRUCTIONS,
    output_schema=ResumeScheme,
    pre_hooks=[pi_guardrail],
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
    pre_hooks=[pi_guardrail],
    debug_mode=True,
)

ats_agent = Agent(
    name="ats_agent",
    description="Agente que analisa compatibilidade de currículo com vaga para ATS",
    model=model_instance,
    instructions=ATS_AGENT_INSTRUCTIONS,
    output_schema=AtsAnalysis,
    pre_hooks=[pi_guardrail],
    debug_mode=True,
)

quality_agent = Agent(
    name="quality_agent",
    description="Agente responsável pela auditoria linguística e de apresentação do currículo",
    model=model_instance,
    instructions=QUALITY_AGENT_INSTRUCTIONS,
    output_schema=ResumeQualityAnalysis,
    pre_hooks=[pi_guardrail],
    markdown=False,
    debug_mode=True,
)