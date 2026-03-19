"""Schemas para endpoints de currículos"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


# ==================== Schemas Existentes ====================

class ResumeSummary(BaseModel):
    """Resumo de currículo para listagem"""
    id: int
    title: str
    created_at: str


# ==================== Schemas para Workflow HITL ====================

class ATSUserInput(BaseModel):
    """Schema para validação do user_input no HITL do workflow"""
    user_proceeds: bool = Field(
        ...,
        description="Deseja prosseguir com a otimização do currículo?"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "user_proceeds": True
            }
        }


class WorkflowOptimizeRequest(BaseModel):
    """Requisição para otimizar currículo com workflow"""
    resume_id: int
    vacancy_text: str
    additional_info: Optional[str] = None


class WorkflowSessionResponse(BaseModel):
    """Resposta da sessão do workflow"""
    session_id: str
    run_id: str
    status: str  # "completed", "paused"
    ats_analysis: Optional[Dict[str, Any]] = None
    message: Optional[str] = None
    user_input_required: Optional[bool] = None


class WorkflowContinueRequest(BaseModel):
    """Requisição para continuar workflow pausado"""
    session_id: str
    run_id: str
    user_input: ATSUserInput
