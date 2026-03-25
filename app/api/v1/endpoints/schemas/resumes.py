from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal


# ==================== Schemas Existentes ====================

class ResumeSummary(BaseModel):
    """Resumo de currículo para listagem"""
    id: int
    title: str
    created_at: str


# ==================== Schemas para Análise ATS ====================

class ElementName(BaseModel):
    """Schema para elementos com element_name"""
    element_name: str


class ATSAnalysis(BaseModel):
    """Schema para análise ATS"""
    ats_score: int = Field(..., description="Score de compatibilidade ATS (0-100)")
    matched_keywords: List[ElementName] = Field(default=[], description="Palavras-chave encontradas no currículo")
    missing_keywords: List[ElementName] = Field(default=[], description="Palavras-chave da vaga ausentes no currículo")
    recommendations: List[str] = Field(default=[], description="Recomendações de melhoria")
    strengths: List[str] = Field(default=[], description="Pontos fortes do currículo")
    weaknesses: List[str] = Field(default=[], description="Pontos de atenção do currículo")

    class Config:
        json_schema_extra = {
            "example": {
                "ats_score": 75,
                "matched_keywords": [{"element_name": "Python"}, {"element_name": "FastAPI"}],
                "missing_keywords": [{"element_name": "Docker"}, {"element_name": "AWS"}],
                "recommendations": [
                    "Adicione experiência com Docker nos highlights",
                    "Mencione projetos com AWS na seção de projects"
                ],
                "strengths": ["Experiência sólida com Python e APIs REST"],
                "weaknesses": ["Falta menção a ferramentas de deploy"]
            }
        }


# ==================== Schemas para Workflow HITL ====================

class UserInputFieldSchema(BaseModel):
    """Schema para campo de input do usuário no HITL"""
    name: str = Field(..., description="Nome do campo")
    field_type: str = Field(default="str", description="Tipo do campo: str, int, float, bool, list, dict")
    description: Optional[str] = Field(None, description="Descrição do campo")
    required: bool = Field(default=True, description="Se o campo é obrigatório")
    allowed_values: Optional[List[Any]] = Field(None, description="Valores permitidos")


class WorkflowStepRequirement(BaseModel):
    """Representa um StepRequirement do Agno que requer input do usuário"""
    step_id: str = Field(..., description="ID do step")
    step_name: str = Field(..., description="Nome do step")
    requires_user_input: bool = Field(default=True, description="Se requer input do usuário")
    user_input_message: Optional[str] = Field(None, description="Mensagem exibida ao usuário")
    user_input_schema: List[UserInputFieldSchema] = Field(default_factory=list, description="Schema dos campos")
    is_resolved: bool = Field(default=False, description="Se o requirement já foi resolvido")


class WorkflowSessionInfo(BaseModel):
    """Informações básicas de uma sessão de workflow"""
    session_id: str = Field(..., description="ID da sessão")
    run_id: str = Field(..., description="ID do run")
    status: Literal["running", "paused", "completed", "cancelled"] = Field(..., description="Status da sessão")
    created_at: Optional[str] = Field(None, description="Data de criação")
    resume_id: Optional[int] = Field(None, description="ID do currículo")


class WorkflowSessionList(BaseModel):
    """Lista de sessões de workflow"""
    sessions: List[WorkflowSessionInfo]


class WorkflowSessionDetails(BaseModel):
    """Detalhes completos de uma sessão de workflow"""
    session_id: str = Field(..., description="ID da sessão")
    run_id: str = Field(..., description="ID do run")
    status: Literal["running", "paused", "completed", "cancelled"] = Field(..., description="Status da sessão")
    ats_analysis: Optional[ATSAnalysis] = Field(None, description="Análise ATS completa")
    optimized_resume: Optional[Dict[str, Any]] = Field(None, description="Currículo otimizado em JSON Resume")
    steps_requiring_user_input: List[WorkflowStepRequirement] = Field(
        default_factory=list,
        description="Steps aguardando input do usuário"
    )
    message: Optional[str] = Field(None, description="Mensagem de status")


class ATSUserInput(BaseModel):
    """Schema para validação do user_input no HITL do workflow"""
    user_proceeds: bool = Field(
        ...,
        description="Deseja prosseguir com a otimização do currículo?"
    )
    feedback: Optional[str] = Field(
        None,
        description="Feedback adicional opcional"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "user_proceeds": True,
                "feedback": "Destacar mais experiências com liderança"
            }
        }


class WorkflowOptimizeRequest(BaseModel):
    """Requisição para otimizar currículo com workflow"""
    resume_id: int = Field(..., description="ID do currículo")
    vacancy_text: str = Field(..., description="Descrição da vaga")
    additional_info: Optional[str] = Field(None, description="Informações adicionais")


class WorkflowContinueRequest(BaseModel):
    """Requisição para continuar workflow pausado"""
    session_id: str = Field(..., description="ID da sessão do workflow")
    run_id: str = Field(..., description="ID do run pausado")
    user_input: Dict[str, Any] = Field(
        ...,
        description="Input do usuário (campos dinâmicos baseados no schema)"
    )


class HitlContinueResponse(BaseModel):
    """Resposta para continuação de workflow HITL"""
    status: Literal["completed", "cancelled", "paused"] = Field(..., description="Status final")
    session_id: str = Field(..., description="ID da sessão")
    run_id: str = Field(..., description="ID do run")
    optimized_resume: Optional[Dict[str, Any]] = Field(None, description="Currículo otimizado")
    ats_analysis: Optional[ATSAnalysis] = Field(None, description="Análise ATS")
    message: str = Field(..., description="Mensagem de status")


class AdaptFullResponse(BaseModel):
    """Resposta do endpoint adapt-full"""
    status: Literal["completed", "paused"] = Field(..., description="Status da execução")
    optimized_resume: Optional[Dict[str, Any]] = Field(None, description="Currículo otimizado")
    ats_analysis: Optional[ATSAnalysis] = Field(None, description="Análise ATS")
    session_id: Optional[str] = Field(None, description="ID da sessão")
    run_id: Optional[str] = Field(None, description="ID do run")
    message: str = Field(..., description="Mensagem de status")
