import logging
import json
from typing import Optional, Dict, Any
from langsmith import traceable
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

    @traceable(run_type="chain", name="Optimize Resume Service")
    def optimize_resume(
        self, 
        vaga: str, 
        curriculo: str,
        info_adicional: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executa otimização completa do currículo para a vaga.
        """
        logger.info("Executando otimização estratégica.")
        
        response = self.optimizer_wf.run(
            vaga=vaga, 
            curriculo=curriculo, 
            info_adicional=info_adicional or ""
        )
        
        # Extrai resultados dos steps mapeados no StepOutput
        step_outputs = getattr(response, 'step_outputs', {})
        
        vacancy_analysis = step_outputs.get("Parse Vacancy")
        parsed_original = step_outputs.get("Parse Resume")
        optimized_resume = step_outputs.get("Generate Optimized Resume")
        
        # Converte para dict se forem modelos Pydantic
        def to_dict(obj):
            return obj.model_dump() if hasattr(obj, 'model_dump') else obj

        return {
            "optimized_resume": to_dict(optimized_resume) if optimized_resume else to_dict(response.content),
            "vacancy_analysis": to_dict(vacancy_analysis),
            "parsed_original": to_dict(parsed_original),
            "raw_response": response
        }

    @traceable(run_type="chain", name="Analyze Quality Service")
    def analyze_quality(self, curriculo: str) -> ResumeQualityAnalysis:
        """
        Executa auditoria de qualidade.
        O workflow agora faz o parse automático antes da análise.
        """
        logger.info("Executando auditoria de qualidade.")
        response = self.quality_wf.run(raw_resume=curriculo)
        return response.content

    @traceable(run_type="chain", name="Check ATS Service")
    def check_ats(self, vaga: str, curriculo: str) -> AtsAnalysis:
        """
        Calcula score ATS.
        O workflow agora estrutura vaga e currículo antes da comparação.
        """
        logger.info("Executando análise ATS.")
        response = self.ats_wf.run(vaga=vaga, curriculo=curriculo)
        return response.content

    def full_pipeline(
        self, 
        vaga: str, 
        curriculo: str,
        info_adicional: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Pipeline completo: Quality → ATS → Optimize.
        """
        logger.info("Executando pipeline completo.")
        
        # 1. Análise de qualidade (usa o workflow que já faz parse)
        quality_result = self.analyze_quality(curriculo)
        
        # 2. Análise ATS (usa o workflow que já faz parse da vaga e currículo)
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
