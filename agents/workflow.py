import logging
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
        vacancy_res = self.steps[0].agent.run(vaga)
        if not vacancy_res or not vacancy_res.content or isinstance(vacancy_res.content, str) and "error" in vacancy_res.content.lower():
            raise Exception(f"Erro ao processar vaga: {vacancy_res.content}")

        # 2. Parse do Currículo
        resume_res = self.steps[1].agent.run(curriculo)
        if not resume_res or not resume_res.content or isinstance(resume_res.content, str) and "error" in resume_res.content.lower():
            raise Exception(f"Erro ao processar currículo: {resume_res.content}")

        # 3. Geração do Currículo Otimizado
        upgrade_input = f"""
        CURRÍCULO ESTRUTURADO:
        {resume_res.content}

        ANÁLISE DA VAGA:
        {vacancy_res.content}

        INFORMAÇÕES ADICIONAIS DO CANDIDATO:
        {info_adicional}
        """

        final_res = self.steps[2].agent.run(upgrade_input)
        if not final_res or not final_res.content or isinstance(final_res.content, str) and "error" in final_res.content.lower():
            raise Exception(f"Erro ao gerar currículo otimizado: {final_res.content}")

        return StepOutput(
            content={
                "optimized_resume": final_res.content,
                "vacancy_analysis": vacancy_res.content,
                "parsed_original": resume_res.content
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
        resume_json = self.steps[0].agent.run(raw_resume)
        if not resume_json or not resume_json.content or isinstance(resume_json.content, str) and "error" in resume_json.content.lower():
             raise Exception(f"Erro no parse do currículo: {resume_json.content}")
        
        # 2. Análise de Qualidade
        quality_res = self.steps[1].agent.run(
            f"Analise a qualidade deste currículo estruturado: {resume_json.content}"
        )
        if not quality_res or not quality_res.content or isinstance(quality_res.content, str) and "error" in quality_res.content.lower():
             raise Exception(f"Erro na análise de qualidade: {quality_res.content}")
        
        return StepOutput(content=quality_res.content)

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
        res_json = self.steps[0].agent.run(curriculo)
        if not res_json or not res_json.content or isinstance(res_json.content, str) and "error" in res_json.content.lower():
             raise Exception(f"Erro no parse do currículo (ATS): {res_json.content}")
        
        # 2. Estrutura a Vaga
        vaga_json = self.steps[1].agent.run(vaga)
        if not vaga_json or not vaga_json.content or isinstance(vaga_json.content, str) and "error" in vaga_json.content.lower():
             raise Exception(f"Erro no parse da vaga (ATS): {vaga_json.content}")
        
        # 3. Auditoria ATS
        ats_res = self.steps[2].agent.run(
            f"CURRÍCULO ESTRUTURADO: {res_json.content}\n\nVAGA ESTRUTURADA: {vaga_json.content}"
        )
        if not ats_res or not ats_res.content or isinstance(ats_res.content, str) and "error" in ats_res.content.lower():
             raise Exception(f"Erro no score ATS: {ats_res.content}")
        
        return StepOutput(content=ats_res.content)
