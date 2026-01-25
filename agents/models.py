from agno.agent import Agent
from agno.models.openrouter import OpenRouter
from dotenv import load_dotenv

# --- CORREÇÃO DOS IMPORTS AQUI ---
# Usamos 'agents.' antes para indicar que está dentro da pasta
from agents.instructions import VACANCY_AGENT_INSTRUCTIONS, RESUME_AGENT_INSTRUCTIONS, UPGRADE_RESUME_AGENT_INSTRUCTIONS
from agents.schemas.vacancy import VacancyKeyThemes
from agents.schemas.resume import ResumeScheme

load_dotenv()

vacancy_agent = Agent(
    name="vacancy_agent",
    description="Agent that generates a job description based on a job description",
    model=OpenRouter(
        id="bytedance-seed/seedream-4.5",
        instructions=VACANCY_AGENT_INSTRUCTIONS,
    ),
    output_schema=VacancyKeyThemes,
    # debug_mode=True, 
)

resume_agent = Agent(
    name="resume_agent",
    description="Agent that generates a resume based on a job description",
    model=OpenRouter(
        id="bytedance-seed/seedream-4.5",
        instructions=RESUME_AGENT_INSTRUCTIONS,
    ),
    output_schema=ResumeScheme,
    # debug_mode=True,
)

resume_upgrade_agent = Agent(
    name="resume_upgrade_agent",
    description="Agent that optimizes a resume for a specific job vacancy",
    model=OpenRouter(
        id="bytedance-seed/seedream-4.5",
        instructions=UPGRADE_RESUME_AGENT_INSTRUCTIONS,
    ),
    output_schema=ResumeScheme, # Garante que a saída seja estruturada
)