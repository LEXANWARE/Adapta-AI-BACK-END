import logging
from typing import Any, Dict, Optional
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
                Step(name="Parse Vacancy", agent=vacancy_agent),
                Step(name="Parse Resume", agent=resume_agent),
                Step(name="Generate Optimized Resume", agent=resume_upgrade_agent),
            ],
            **kwargs
        )

    @traceable(run_type="chain", name="Resume Optimizer Workflow")
    def run(self, vaga: str, curriculo: str, info_adicional: str = "") -> StepOutput:
        logger.info("Iniciando Workflow de Otimização")

        # 1. Parse da Vaga
        vacancy_res = self.run_step(step=self.steps[0], input=vaga)

        # 2. Parse do Currículo
        resume_res = self.run_step(step=self.steps[1], input=curriculo)

        # 3. Geração do Currículo Otimizado
        upgrade_input = f"""
        CURRÍCULO ORIGINAL (ESTRUTURADO):
        {resume_res.content}

        ANÁLISE DA VAGA:
        {vacancy_res.content}

        INFORMAÇÕES ADICIONAIS DO CANDIDATO:
        {info_adicional}
        """

        final_res = self.run_step(step=self.steps[2], input=upgrade_input)

        return StepOutput(
            content=final_res.content,
            step_outputs={
                "Parse Vacancy": vacancy_res.content,
                "Parse Resume": resume_res.content,
                "Generate Optimized Resume": final_res.content
            }
        )

class ResumeQualityWorkflow(Workflow):
    """
    Workflow para análise técnica e gramatical.
    Integra o parseamento do currículo antes da auditoria.
    """
    def __init__(self, **kwargs):
        super().__init__(
            name="resume_quality_audit",
            steps=[
                Step(name="Parse Resume", agent=resume_agent),
                Step(name="Quality Analysis", agent=quality_agent),
            ],
            **kwargs
        )

    @traceable(run_type="chain", name="Resume Quality Workflow")
    def run(self, raw_resume: str) -> StepOutput:
        logger.info("Iniciando Workflow de Qualidade")
        
        # 1. Parse do Currículo
        resume_json = self.run_step(step=self.steps[0], input=raw_resume)
        
        # 2. Análise de Qualidade
        quality_res = self.run_step(
            step=self.steps[1], 
            input=f"Analise a qualidade deste currículo estruturado: {resume_json.content}"
        )
        
        return StepOutput(
            content=quality_res.content,
            step_outputs={
                "Parse Resume": resume_json.content,
                "Quality Analysis": quality_res.content
            }
        )

class AtsCheckWorkflow(Workflow):
    """
    Workflow para cálculo de score ATS.
    Estrutura Vaga e Currículo antes de comparar.
    """
    def __init__(self, **kwargs):
        super().__init__(
            name="ats_check",
            steps=[
                Step(name="Parse Resume", agent=resume_agent),
                Step(name="Parse Vacancy", agent=vacancy_agent),
                Step(name="ATS Scoring", agent=ats_agent),
            ],
            **kwargs
        )

    @traceable(run_type="chain", name="ATS Check Workflow")
    def run(self, vaga: str, curriculo: str) -> StepOutput:
        logger.info("Iniciando Workflow ATS")
        
        # 1. Estrutura o Currículo
        res_json = self.run_step(step=self.steps[0], input=curriculo)
        
        # 2. Estrutura a Vaga
        vaga_json = self.run_step(step=self.steps[1], input=vaga)
        
        # 3. Auditoria ATS
        ats_res = self.run_step(
            step=self.steps[2],
            input=f"CURRÍCULO ESTRUTURADO: {res_json.content}\n\nVAGA ESTRUTURADA: {vaga_json.content}"
        )
        
        return StepOutput(
            content=ats_res.content,
            step_outputs={
                "Parse Resume": res_json.content,
                "Parse Vacancy": vaga_json.content,
                "ATS Scoring": ats_res.content
            }
        )
