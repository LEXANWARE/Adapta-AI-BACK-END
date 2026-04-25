import logging
from typing import Any, Dict
from agno.workflow import Step, Workflow, StepOutput
from langsmith import traceable
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

    @traceable(run_type="chain", name="Resume Optimizer Workflow")
    def run(self, additional_data: Dict[str, Any]) -> StepOutput:
        """
        Executa o workflow utilizando run_step para processar cada etapa.
        """
        vaga = additional_data.get("vaga")
        curriculo = additional_data.get("curriculo")
        info_adicional = additional_data.get("info_adicional", "")

        logger.info("Iniciando Workflow de Otimização")

        # 1. Parse da Vaga - Correção: usa self.steps[0].agent.run
        vacancy_res = self.steps[0].agent.run(input=vaga)

        # 2. Parse do Currículo - Correção: usa self.steps[1].agent.run
        resume_res = self.steps[1].agent.run(input=curriculo)

        # 3. Geração do Currículo Otimizado
        upgrade_input = f"""
        CURRÍCULO ORIGINAL (ESTRUTURADO):
        {resume_res.content}

        ANÁLISE DA VAGA:
        {vacancy_res.content}

        INFORMAÇÕES ADICIONAIS DO CANDIDATO:
        {info_adicional}
        """

        # Correção: usa self.steps[2].agent.run
        final_res = self.steps[2].agent.run(input=upgrade_input)

        result = StepOutput(content=final_res.content)
        result.step_outputs = {
            "Parse Vacancy": vacancy_res.content,
            "Parse Resume": resume_res.content,
            "Generate Optimized Resume": final_res.content
        }
        return result

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

    @traceable(run_type="chain", name="Resume Quality Workflow")
    def run(self, content: str) -> StepOutput:
        # Correção: usa self.steps[0].agent.run
        res = self.steps[0].agent.run(input=content)
        return StepOutput(content=res.content)

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

    @traceable(run_type="chain", name="ATS Check Workflow")
    def run(self, content: str) -> StepOutput:
        # Correção: usa self.steps[0].agent.run
        res = self.steps[0].agent.run(input=content)
        return StepOutput(content=res.content)