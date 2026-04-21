import logging
from typing import Optional
from agno.run.workflow import WorkflowRunOutput
from agents.workflow import (
    ResumeOptimizerWorkflow, 
    ResumeQualityWorkflow, 
    AtsCheckWorkflow
)

logger = logging.getLogger(__name__)

class WorkflowService:
    def __init__(self):
        self.optimizer_wf = ResumeOptimizerWorkflow()
        self.quality_wf = ResumeQualityWorkflow()
        self.ats_wf = AtsCheckWorkflow()

    def optimize_resume(self, vaga: str, curriculo: str) -> WorkflowRunOutput:
        """Executa a otimização (criação do novo JSON de currículo)."""
        logger.info("Executando otimização estratégica.")
        return self.optimizer_wf.run(
            additional_data={"vaga": vaga, "curriculo": curriculo}
        )

    def analyze_quality(self, curriculo: str) -> WorkflowRunOutput:
        """Executa o relatório de qualidade e erros gramaticais."""
        logger.info("Executando auditoria de qualidade.")
        return self.quality_wf.run(content=curriculo)

    def check_ats(self, vaga: str, curriculo: str) -> WorkflowRunOutput:
        """Executa o cálculo de score ATS."""
        logger.info("Executando análise ATS.")
        return self.ats_wf.run(content=f"VAGA: {vaga}\n\nCURRÍCULO: {curriculo}")

# Singleton para a aplicação
workflow_service = WorkflowService()