from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field

STRICT_CONFIG = ConfigDict(
    extra='ignore',
)

class KeyElement(BaseModel):
    model_config = STRICT_CONFIG
    element_name: str = Field(..., description="Nome do elemento chave")

class AtsAnalysis(BaseModel):
    model_config = STRICT_CONFIG
    ats_score: int = Field(..., ge=0, le=100, description="Score de compatibilidade ATS (0-100)")
    matched_keywords: List[KeyElement] = Field(default_factory=list, description="Palavras-chave da vaga encontradas no currículo")
    missing_keywords: List[KeyElement] = Field(default_factory=list, description="Palavras-chave da vaga ausentes no currículo")
    recommendations: List[str] = Field(default_factory=list, description="Lista de recomendações para melhorar o score ATS")
    strengths: List[str] = Field(default_factory=list, description="Pontos fortes do currículo em relação à vaga")
    weaknesses: List[str] = Field(default_factory=list, description="Pontos fracos ou lacunas do currículo em relação à vaga")
    user_proceeds: Optional[bool] = Field(None, description="Decisão do usuário: se aceitou prosseguir com a otimização (HITL)")
