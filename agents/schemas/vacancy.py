from typing import List
from pydantic import BaseModel, ConfigDict, Field

STRICT_CONFIG = ConfigDict(
    extra='ignore',
)

class KeyElement(BaseModel):
    model_config = STRICT_CONFIG
    element_name: str = Field(..., description="Nome do elemento chave")

class VacancyKeyThemes(BaseModel):
    model_config = STRICT_CONFIG
    key_tools: List[KeyElement] = Field(default_factory=list, description="Ferramentas e tecnologias principais")
    key_skills: List[KeyElement] = Field(default_factory=list, description="Habilidades técnicas e comportamentais")
    key_phrases: List[KeyElement] = Field(default_factory=list, description="Frases chaves ou diferenciais da vaga")