from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class Location(BaseModel):
    address: Optional[str] = Field(None, description="Endereço ou Rua")
    postalCode: Optional[str] = Field(None, description="CEP")
    city: Optional[str] = Field(None, description="Cidade")
    countryCode: Optional[str] = Field(None, description="Código do País (ex: BR)")
    region: Optional[str] = Field(None, description="Estado ou Região")


class Basics(BaseModel):
    name: str = Field(..., description="Nome completo do candidato")
    label: Optional[str] = Field(None, description="Título profissional ou cargo alvo")
    image: Optional[str] = Field(None, description="URL de imagem/foto de perfil")
    email: Optional[str] = Field(None, description="Email do candidato")
    phone: Optional[str] = Field(None, description="Telefone")
    url: Optional[str] = Field(None, description="URL de site pessoal ou portfólio")
    summary: Optional[str] = Field(None, description="Resumo profissional")
    location: Optional[Location] = Field(None, description="Localização detalhada")


class Profile(BaseModel):
    network: Optional[str] = Field(None, description="Nome da rede social (ex: LinkedIn, GitHub)")
    username: Optional[str] = Field(None, description="Usuário na rede social")
    url: Optional[str] = Field(None, description="URL do perfil")


class StarAchievement(BaseModel):
    """
    Estrutura para conquistas usando metodologia STAR:
    Situation (Situação), Task (Tarefa), Action (Ação), Result (Resultado)
    """
    situation: str = Field(..., description="Contexto ou desafio encontrado")
    task: str = Field(..., description="Responsabilidade ou missão diante da situação")
    action: str = Field(..., description="Ações específicas que foram tomadas")
    result: str = Field(..., description="Resultado alcançado (preferencialmente mensurável)")
    skills_used: List[str] = Field(default_factory=list, description="Competências aplicadas (ex: Liderança, Negociação)")


class SoftSkill(BaseModel):
    """
    Soft skill com evidências reais extraídas das experiências.
    Ex: Liderança comprovada por 'Liderei time de 8 pessoas no projeto X'
    """
    name: str = Field(..., description="Nome da soft skill (ex: Liderança, Comunicação, Resolução de Problemas)")
    level: Optional[str] = Field(None, description="Nível de proficiência (ex: Avançado, Intermediário, Básico)")
    evidence: List[str] = Field(default_factory=list, description="Evidências reais que comprovam esta soft skill")


class Work(BaseModel):
    name: str = Field(..., description="Nome da empresa")
    position: str = Field(..., description="Cargo ocupado")
    url: Optional[str] = Field(None, description="URL da empresa")
    startDate: Optional[str] = Field(None, description="Data de início")
    endDate: Optional[str] = Field(None, description="Data de fim ou 'Presente'")
    summary: Optional[str] = Field(None, description="Descrição das atividades")
    highlights: List[str] = Field(default_factory=list, description="Lista de conquistas/pontos chave")
    
    # Campos de humanização e contexto
    context: Optional[str] = Field(None, description="Contexto do ambiente de trabalho (ex: 'Startup de 20 pessoas', 'Hospital público de grande porte')")
    team_size: Optional[int] = Field(None, description="Tamanho do time liderado ou com que trabalhou")
    beneficiaries: Optional[str] = Field(None, description="Quem foi impactado pelo trabalho (ex: '500+ pacientes', '2000+ alunos')")
    star_achievements: List[StarAchievement] = Field(default_factory=list, description="Conquistas estruturadas no formato STAR")


class Education(BaseModel):
    institution: str = Field(..., description="Instituição de ensino")
    area: str = Field(..., description="Curso ou área de estudo")
    studyType: str = Field(..., description="Tipo (Bacharelado, Curso, etc)")
    url: Optional[str] = Field(None, description="URL da instituição")
    startDate: Optional[str] = None
    endDate: Optional[str] = None
    
    # Campos adicionais para humanização
    thesis_title: Optional[str] = Field(None, description="Título da tese ou TCC")
    honors: List[str] = Field(default_factory=list, description="Honrarias (ex: 'Magna cum laude', 'Primeira turma')")


class Award(BaseModel):
    title: str = Field(..., description="Título do prêmio")
    date: Optional[str] = Field(None, description="Data em que o prêmio foi recebido")
    awarder: Optional[str] = Field(None, description="Organização que concedeu o prêmio")
    summary: Optional[str] = Field(None, description="Resumo ou contexto do prêmio")


class Skill(BaseModel):
    name: str = Field(..., description="Categoria da habilidade (ex: Linguagens)")
    keywords: List[str] = Field(default_factory=list, description="Lista de skills (ex: Python, Java)")


class Project(BaseModel):
    name: str = Field(..., description="Nome do projeto")
    description: Optional[str] = None
    url: Optional[str] = None


class Certificate(BaseModel):
    name: str = Field(..., description="Nome da certificação")
    date: Optional[str] = Field(None, description="Data da certificação")
    issuer: Optional[str] = Field(None, description="Entidade emissora")
    url: Optional[str] = Field(None, description="URL da certificação")
    credential_id: Optional[str] = Field(None, description="ID ou código da credencial")
    skills_validated: List[str] = Field(default_factory=list, description="Skills validadas por esta certificação")


class Publication(BaseModel):
    name: str = Field(..., description="Nome da publicação")
    publisher: Optional[str] = Field(None, description="Publicador")
    releaseDate: Optional[str] = Field(None, description="Data de publicação")
    url: Optional[str] = Field(None, description="URL da publicação")
    summary: Optional[str] = Field(None, description="Resumo da publicação")


class Language(BaseModel):
    language: str = Field(..., description="Idioma")
    fluency: Optional[str] = Field(None, description="Nível de fluência")


class Interest(BaseModel):
    name: str = Field(..., description="Área de interesse")
    keywords: List[str] = Field(default_factory=list, description="Palavras-chave relacionadas ao interesse")


class Reference(BaseModel):
    name: str = Field(..., description="Nome da referência")
    reference: Optional[str] = Field(None, description="Texto da recomendação ou contato")


class VolunteerExperience(BaseModel):
    """Experiência de voluntariado - crucial para humanização do currículo"""
    organization: str = Field(..., description="Nome da organização")
    role: str = Field(..., description="Papel ou cargo ocupado")
    startDate: Optional[str] = None
    endDate: Optional[str] = None
    cause: Optional[str] = Field(None, description="Causa (ex: 'Educação', 'Saúde mental', 'Meio ambiente')")
    impact: Optional[str] = Field(None, description="Impacto gerado (ex: 'Capacitou 200 jovens em programação')")
    summary: Optional[str] = Field(None, description="Descrição das atividades")


class ResumeScheme(BaseModel):
    model_config = ConfigDict(extra='ignore')
    basics: Optional[Basics] = None
    work: List[Work] = Field(default_factory=list)
    education: List[Education] = Field(default_factory=list)
    skills: List[Skill] = Field(default_factory=list)
    projects: List[Project] = Field(default_factory=list)
    languages: List[Language] = Field(default_factory=list)
    profiles: List[Profile] = Field(default_factory=list)
    awards: List[Award] = Field(default_factory=list)
    certificates: List[Certificate] = Field(default_factory=list)
    publications: List[Publication] = Field(default_factory=list)
    interests: List[Interest] = Field(default_factory=list)
    references: List[Reference] = Field(default_factory=list)
    
    # Novos campos para humanização e metodologia STAR
    soft_skills: List[SoftSkill] = Field(default_factory=list, description="Soft skills com evidências reais")
    volunteer: List[VolunteerExperience] = Field(default_factory=list, description="Experiências de voluntariado")
    career_objective: Optional[str] = Field(None, description="Objetivo de carreira ou transição desejada")
    core_values: List[str] = Field(default_factory=list, description="Valores centrais (ex: 'Diversidade', 'Sustentabilidade', 'Inovação social')")