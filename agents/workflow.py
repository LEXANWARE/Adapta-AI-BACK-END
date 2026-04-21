import logging
from agno.workflow import Step, Workflow
from agents.models import (
    vacancy_agent,
    resume_agent,
    resume_upgrade_agent,
    quality_agent,
    ats_agent
)

logger = logging.getLogger(__name__)

class ResumeOptimizerWorkflow(Workflow):
    """
    Workflow linear para transformar um currículo original em um 
    currículo otimizado para uma vaga específica.
    """
    def __init__(self, **kwargs):
        super().__init__(
            name="resume_optimizer",
            steps=[
                Step(
                    name="Parse Vacancy",
                    agent=vacancy_agent,
                    description="Extrai keywords e requisitos da descrição da vaga"
                ),
                Step(
                    name="Parse Resume",
                    agent=resume_agent,
                    description="Converte o currículo original para formato estruturado"
                ),
                Step(
                    name="Generate Optimized Resume",
                    agent=resume_upgrade_agent,
                    description="Cria a versão final otimizada baseada nos inputs anteriores"
                ),
            ],
            **kwargs
        )

class ResumeQualityWorkflow(Workflow):
    """
    Workflow independente para análise técnica, gramatical e de apresentação.
    """
    def __init__(self, **kwargs):
        super().__init__(
            name="resume_quality_audit",
            steps=[
                Step(
                    name="Quality Analysis",
                    agent=quality_agent,
                    description="Realiza auditoria linguística e de branding pessoal"
                ),
            ],
            **kwargs
        )

class AtsCheckWorkflow(Workflow):
    """
    Workflow independente para cálculo de score de robôs e match de keywords.
    """
    def __init__(self, **kwargs):
        super().__init__(
            name="ats_check",
            steps=[
                Step(
                    name="ATS Scoring",
                    agent=ats_agent,
                    description="Calcula compatibilidade entre currículo e vaga"
                ),
            ],
            **kwargs
        )