from typing import List, Optional
from pydantic import BaseModel, Field

class QualityIssue(BaseModel):
    category: str = Field(..., description="Gramática, Pontuação, Concordância ou Clareza")
    description: str = Field(..., description="Descrição do problema")
    original_text: str = Field(..., description="Trecho com erro")
    suggestion: str = Field(..., description="Sugestão de correção")

class ExperienceGap(BaseModel):
    company: str
    gap_description: str = Field(..., description="O que falta (ex: falta de métricas, descrição rasa)")

class VisualLayoutAudit(BaseModel):
    category: str = Field(..., description="Ex: Espaçamento, Fontes, Hierarquia, Margens")
    assessment: str = Field(..., description="Avaliação visual do impacto")
    improvement: str = Field(..., description="Sugestão de ajuste visual")

class ContactLinkAudit(BaseModel):
    platform: str = Field(..., description="Ex: LinkedIn, GitHub, Portfólio")
    status: str = Field(..., description="Ex: Presente, Ausente, Mal formatado")
    professional_score: int = Field(..., description="Nota para a aparência do perfil externo")

class KeywordOptimization(BaseModel):
    skill: str
    relevance: str = Field(..., description="Alta, Média ou Baixa para a senioridade")
    context_found: bool = Field(..., description="Se a skill está inserida em um contexto de conquista")

from typing import List
from pydantic import BaseModel, Field

# ... (Classes QualityIssue, ExperienceGap, VisualLayoutAudit, etc. conforme definido antes)

class ResumeQualityAnalysis(BaseModel):
    presentation_score: int
    grammar_score: int
    branding_impact: str
    perceived_seniority: str
    language_issues: List[QualityIssue] = Field(default_factory=list)
    incomplete_experiences: List[ExperienceGap] = Field(default_factory=list)
    keywords_audit: List[KeywordOptimization] = Field(default_factory=list)
    links_audit: List[ContactLinkAudit] = Field(default_factory=list)
    layout_feedback: List[VisualLayoutAudit] = Field(default_factory=list)
    main_strengths: List[str] = Field(default_factory=list)
    red_flags: List[str] = Field(default_factory=list)
    presentation_feedback: str
    general_recommendations: List[str] = Field(default_factory=list)