from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class KeyElement(BaseModel):
    element_name: str = Field(..., description="Nome do elemento chave")


class TransferableSkill(BaseModel):
    """Skill transferida de outra área ou experiência"""
    element_name: str = Field(..., description="Nome da skill transferível")
    source: Optional[str] = Field(None, description="De onde veio (ex: 'Experiência anterior em Engenharia')")


class AtsAnalysis(BaseModel):
    """Schema para análise ATS - agente retorna este formato"""
    model_config = ConfigDict(extra='ignore')
    ats_score: int = Field(..., ge=0, le=100, description="Score de compatibilidade ATS (0-100)")
    matched_keywords: List[KeyElement] = Field(default_factory=list, description="Palavras-chave da vaga encontradas no currículo")
    missing_keywords: List[KeyElement] = Field(default_factory=list, description="Palavras-chave da vaga ausentes no currículo")
    recommendations: List[str] = Field(default_factory=list, description="Lista de recomendações para melhorar o score ATS")
    strengths: List[str] = Field(default_factory=list, description="Pontos fortes do currículo em relação à vaga")
    weaknesses: List[str] = Field(default_factory=list, description="Pontos fracos ou lacunas do currículo em relação à vaga")
    
    # Novos campos para STAR e Soft Skills
    star_achievements_count: Optional[int] = Field(None, description="Número de achievements no formato STAR encontrados")
    soft_skills_count: Optional[int] = Field(None, description="Número de soft skills com evidências encontradas")
    soft_skills_match_vaga: List[KeyElement] = Field(default_factory=list, description="Soft skills que são relevantes para a vaga")
    transferable_skills: List[TransferableSkill] = Field(default_factory=list, description="Skills transferíveis de outras áreas/experiências")
    humanization_indicators: List[str] = Field(default_factory=list, description="Indicadores de currículo humanizado (voluntariado, contexto, impacto)")