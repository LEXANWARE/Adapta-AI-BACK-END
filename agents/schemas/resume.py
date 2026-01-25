from typing import List, Optional
from pydantic import BaseModel, Field

# --- Sub-models ---

class Basics(BaseModel):
    name: str = Field(..., description="Nome completo do candidato")
    email: Optional[str] = Field(None, description="Email do candidato")
    phone: Optional[str] = Field(None, description="Telefone")
    summary: Optional[str] = Field(None, description="Resumo profissional")
    location: Optional[dict] = Field(None, description="Localização (Cidade, Estado)")

class Work(BaseModel):
    name: str = Field(..., description="Nome da empresa")
    position: str = Field(..., description="Cargo ocupado")
    startDate: Optional[str] = Field(None, description="Data de início")
    endDate: Optional[str] = Field(None, description="Data de fim ou 'Presente'")
    summary: Optional[str] = Field(None, description="Descrição das atividades")
    highlights: List[str] = Field(default_factory=list, description="Lista de conquistas/pontos chave")

class Education(BaseModel):
    institution: str = Field(..., description="Instituição de ensino")
    area: str = Field(..., description="Curso ou área de estudo")
    studyType: str = Field(..., description="Tipo (Bacharelado, Curso, etc)")
    startDate: Optional[str] = None
    endDate: Optional[str] = None

class Skill(BaseModel):
    name: str = Field(..., description="Categoria da habilidade (ex: Linguagens)")
    keywords: List[str] = Field(default_factory=list, description="Lista de skills (ex: Python, Java)")

class Project(BaseModel):
    name: str = Field(..., description="Nome do projeto")
    description: Optional[str] = None
    url: Optional[str] = None

class Language(BaseModel):
    language: str = Field(..., description="Idioma")
    fluency: Optional[str] = Field(None, description="Nível de fluência")

# --- MODELO PRINCIPAL (O que o Python está tentando importar) ---

class ResumeScheme(BaseModel):  # <--- Note o "Scheme" com E no final
    basics: Basics
    work: List[Work] = Field(default_factory=list)
    education: List[Education] = Field(default_factory=list)
    skills: List[Skill] = Field(default_factory=list)
    projects: List[Project] = Field(default_factory=list)
    languages: List[Language] = Field(default_factory=list)