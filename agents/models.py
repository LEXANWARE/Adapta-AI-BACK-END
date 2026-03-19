from pathlib import Path
from dotenv import load_dotenv
from agno.agent import Agent
from agno.models.google import Gemini
from agents.instructions import (
    VACANCY_AGENT_INSTRUCTIONS,
    RESUME_AGENT_INSTRUCTIONS,
    UPGRADE_RESUME_AGENT_INSTRUCTIONS,
    ENRICH_RESUME_INSTRUCTIONS,
    ATS_AGENT_INSTRUCTIONS,
)
from agents.schemas.vacancy import VacancyKeyThemes
from agents.schemas.resume import ResumeScheme
from agents.schemas.ats import AtsAnalysis

ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=Path(ENV_PATH))

model_instance = Gemini(id="gemini-2.5-flash")

vacancy_agent = Agent(
    name="vacancy_agent",
    description="Agente que analisa descrições de vagas",
    model=model_instance,
    instructions=VACANCY_AGENT_INSTRUCTIONS,
    output_schema=VacancyKeyThemes,
    debug_mode=True
)

resume_agent = Agent(
    name="resume_agent",
    description="Agente que converte currículos para JSON",
    model=model_instance,
    instructions=RESUME_AGENT_INSTRUCTIONS,
    output_schema=ResumeScheme,
    debug_mode=True
)

resume_upgrade_agent = Agent(
    name="resume_upgrade_agent",
    description="Agente que melhora currículos",
    model=model_instance,
    instructions=UPGRADE_RESUME_AGENT_INSTRUCTIONS,
    output_schema=ResumeScheme,
    debug_mode=True
)

resume_enricher_agent = Agent(
    name="resume_enricher_agent",
    description="Agente que adiciona informações extras ao currículo",
    model=model_instance,
    instructions=ENRICH_RESUME_INSTRUCTIONS,
    output_schema=ResumeScheme,
    debug_mode=True
)

ats_agent = Agent(
    name="ats_agent",
    description="Agente que analisa compatibilidade de currículo com vaga para ATS",
    model=model_instance,
    instructions=ATS_AGENT_INSTRUCTIONS,
    output_schema=AtsAnalysis,
    debug_mode=True
)