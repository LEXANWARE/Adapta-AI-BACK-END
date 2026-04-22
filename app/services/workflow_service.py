import logging
import json
from typing import Optional, Dict, Any
from agno.run.workflow import WorkflowRunOutput
from agents.workflow import (
    ResumeOptimizerWorkflow, 
    ResumeQualityWorkflow, 
    AtsCheckWorkflow
)
from agents.schemas.resume import ResumeScheme
from agents.schemas.ats import AtsAnalysis
from agents.schemas.quality import ResumeQualityAnalysis

logger = logging.getLogger(__name__)


class WorkflowService:
    """Serviço unificado para execução de workflows de currículo."""
    
    def __init__(self):
        self.optimizer_wf = ResumeOptimizerWorkflow()
        self.quality_wf = ResumeQualityWorkflow()
        self.ats_wf = AtsCheckWorkflow()

    def optimize_resume(
        self, 
        vaga: str, 
        curriculo: str,
        info_adicional: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executa otimização completa do currículo para a vaga.
        
        Fluxo completo sem HITL:
        1. Parse da vaga (vacancy_agent)
        2. Parse do currículo (resume_agent)
        3. Geração do currículo otimizado (resume_upgrade_agent)
        
        Returns:
            Dict com:
            - optimized_resume: ResumeScheme (dict)
            - vacancy_analysis: VacancyKeyThemes (dict)
            - parsed_original: ResumeScheme (dict)
        """
        logger.info("Executando otimização estratégica (fluxo completo).")
        
        additional_data = {
            "vaga": vaga,
            "curriculo": curriculo,
            "info_adicional": info_adicional or ""
        }
        
        response = self.optimizer_wf.run(additional_data=additional_data)
        
        # Extrai resultados dos steps
        step_outputs = getattr(response, 'step_outputs', {})
        
        vacancy_analysis = None
        parsed_original = None
        optimized_resume = None
        
        for step_name, output in step_outputs.items():
            if "Parse Vacancy" in step_name and output:
                vacancy_analysis = output.model_dump() if hasattr(output, 'model_dump') else output
            elif "Parse Resume" in step_name and output:
                parsed_original = output.model_dump() if hasattr(output, 'model_dump') else output
            elif "Generate Optimized Resume" in step_name and output:
                optimized_resume = output.model_dump() if hasattr(output, 'model_dump') else output
        
        return {
            "optimized_resume": optimized_resume or (response.output.model_dump() if response.output else None),
            "vacancy_analysis": vacancy_analysis,
            "parsed_original": parsed_original,
            "raw_response": response
        }

    def analyze_quality(self, curriculo: str) -> ResumeQualityAnalysis:
        """
        Executa auditoria de qualidade (gramática, branding, estrutura).
        
        Returns:
            ResumeQualityAnalysis com scores e recomendações
        """
        logger.info("Executando auditoria de qualidade.")
        response = self.quality_wf.run(content=curriculo)
        return response.output

    def check_ats(self, vaga: str, curriculo: str) -> AtsAnalysis:
        """
        Calcula score ATS e compatibilidade entre currículo e vaga.
        
        Returns:
            AtsAnalysis com score, matched/missing keywords e recomendações
        """
        logger.info("Executando análise ATS.")
        response = self.ats_wf.run(
            content=f"VAGA:\n{vaga}\n\nCURRÍCULO:\n{curriculo}"
        )
        return response.output

    def full_pipeline(
        self, 
        vaga: str, 
        curriculo: str,
        info_adicional: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Pipeline completo: Quality → ATS → Optimize.
        
        Executa todas as análises e otimização em sequência.
        
        Returns:
            Dict com:
            - quality_analysis: ResumeQualityAnalysis
            - ats_analysis: AtsAnalysis
            - optimized_resume: ResumeScheme
        """
        logger.info("Executando pipeline completo.")
        
        # 1. Análise de qualidade do currículo original
        quality_result = self.analyze_quality(curriculo)
        
        # 2. Análise ATS do currículo original vs vaga
        ats_result = self.check_ats(vaga, curriculo)
        
        # 3. Otimização do currículo
        optimize_result = self.optimize_resume(vaga, curriculo, info_adicional)
        
        return {
            "quality_analysis": quality_result.model_dump() if quality_result else None,
            "ats_analysis": ats_result.model_dump() if ats_result else None,
            "optimized_resume": optimize_result.get("optimized_resume"),
            "vacancy_analysis": optimize_result.get("vacancy_analysis"),
            "parsed_original": optimize_result.get("parsed_original")
        }


# Singleton para a aplicação
workflow_service = WorkflowService()