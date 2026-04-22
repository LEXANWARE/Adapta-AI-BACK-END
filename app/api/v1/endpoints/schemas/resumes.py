from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


# ==================== Schemas de Currículo ====================

class ResumeSummary(BaseModel):
    """Resumo de currículo para listagem"""
    id: int
    created_at: str
    has_optimized_version: bool = Field(default=False)


class ResumeDetail(BaseModel):
    """Detalhes completos de um currículo"""
    id: int
    raw_text: str
    parsed_data: Optional[Dict[str, Any]] = Field(default=None)
    created_at: str


# ==================== Schemas de Requisição ====================

class OptimizeRequest(BaseModel):
    """Requisição para otimizar currículo"""
    resume_id: int = Field(..., description="ID do currículo")
    vacancy_text: str = Field(..., description="Descrição da vaga")
    additional_info: Optional[str] = Field(None, description="Informações adicionais")


class FullPipelineRequest(BaseModel):
    """Requisição para pipeline completo"""
    resume_id: int = Field(..., description="ID do currículo")
    vacancy_text: str = Field(..., description="Descrição da vaga")
    additional_info: Optional[str] = Field(None, description="Informações adicionais")


# ==================== Schemas de Resposta ====================

class OptimizeResponse(BaseModel):
    """Resposta da otimização de currículo"""
    resume_id: int
    optimized_resume: Optional[Dict[str, Any]] = Field(None)
    vacancy_analysis: Optional[Dict[str, Any]] = Field(None)
    message: str


class QualityAnalysisResponse(BaseModel):
    """Resposta da análise de qualidade"""
    resume_id: int
    analysis: Optional[Dict[str, Any]] = Field(None)


class ATSAnalysisResponse(BaseModel):
    """Resposta da análise ATS"""
    resume_id: int
    analysis: Optional[Dict[str, Any]] = Field(None)


class FullPipelineResponse(BaseModel):
    """Resposta do pipeline completo"""
    resume_id: int
    quality_analysis: Optional[Dict[str, Any]] = Field(None)
    ats_analysis: Optional[Dict[str, Any]] = Field(None)
    optimized_resume: Optional[Dict[str, Any]] = Field(None)
    vacancy_analysis: Optional[Dict[str, Any]] = Field(None)
    message: str