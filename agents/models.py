from agno.agent import Agent
from agno.models.openrouter import OpenRouter
from dotenv import load_dotenv
from instructions import VACANCY_AGENT_INSTRUCTIONS, RESUME_AGENT_INSTRUCTIONS, UPGRADE_RESUME_AGENT_INSTRUCTIONS
from schemas.vacancy import VacancyKeyThemes
from schemas.resume import ResumeSchema
from pydantic import BaseModel, Field
from typing import List, Optional

load_dotenv()

# Schema para o resume_agent
class ResumeAnalysis(BaseModel):
    key_tools: List[dict] = Field(..., description="Key tools/technologies from resume")
    key_skills: List[dict] = Field(..., description="Key skills from resume")
    key_experiences: List[dict] = Field(..., description="Key experiences from resume")

# Schema para o resume_upgrade_agent
class ResumeUpgradeSuggestions(BaseModel):
    keyword_optimization: List[dict] = Field(..., description="Keyword optimization suggestions")
    skills_enhancement: List[dict] = Field(..., description="Skills enhancement suggestions")
    experience_relevance: List[dict] = Field(..., description="Experience relevance suggestions")

vacancy_agent = Agent(
    name="vacancy_agent",
    description="Agent that analyzes job descriptions and extracts key themes",
    model=OpenRouter(
        id="liquid/lfm-2.5-1.2b-thinking:free",
        instructions=VACANCY_AGENT_INSTRUCTIONS
    ),
    output_schema=VacancyKeyThemes,
    use_json_mode=True,
    reasoning=True,
    debug_mode=True,
    debug_level=2,
)

resume_agent = Agent(
    name="resume_agent",
    description="Agent that analyzes resumes and extracts key information",
    model=OpenRouter(
        id="liquid/lfm-2.5-1.2b-thinking:free",
        instructions=RESUME_AGENT_INSTRUCTIONS,
    ),
    output_schema=ResumeAnalysis,
    use_json_mode=True,
    reasoning=True,
    debug_mode=True,
    debug_level=2,
)

resume_upgrade_agent = Agent(
    name="resume_upgrade_agent",
    description="Agent that suggests resume improvements based on job descriptions",
    model=OpenRouter(
        id="liquid/lfm-2.5-1.2b-thinking:free",
        instructions=UPGRADE_RESUME_AGENT_INSTRUCTIONS,
    ),
    output_schema=ResumeUpgradeSuggestions,
    use_json_mode=True,
    reasoning=True,
    debug_mode=True,
    debug_level=2,
)

if __name__ == "__main__":
    # Dados de teste
    vacancy_description = '''
Venha para uma das maiores empresas de Serviços IT do mundo!! Aqui você pode transformar sua carreira!

Por que fazer parte da TCS? Aqui na TCS acreditamos que as pessoas fazem a diferença, por isso vivemos uma cultura de aprendizado ilimitado cheio de oportunidades de melhorias e desenvolvimento mútuo. O cenário ideal para expandir ideias através das ferramentas certas, contribuindo para nosso sucesso num ambiente colaborativo.

Procuramos Python + Pyspark,Remote mode in Sao Paulo/Londrina que queira aprender e transformar sua carreira.

Nesta função você irá: (responsabilidades) 

Buscamos um profissional com perfil técnico para atuar no desenvolvimento, integração e manutenção de soluções orientadas a dados, utilizando modernas tecnologias de nuvem e linguagens de programação.

Responsabilidades: 

• Desenvolver scripts e automações utilizando Python e PySpark;
• Projetar e implementar pipelines de dados utilizando AWS Glue;
• Trabalhar com serviços da AWS como S3, SNS, API Gateway, Glue, Lambda, CloudWatch e outros; • Colaborar com equipes multifuncionais para entender os requisitos de negócio e traduzi-los em soluções técnicas;
• Garantir as melhores práticas para versionamento, testes e documentação de código.

Requisitos Técnicos: 

• Sólidos conhecimentos de Python e Spark para manipulação e automação de dados;
• Experiência prática com AWS Glue (SQS, SNS, API Gateway, Lambda, DynamoDB, Glue, Glue DataCatalog, Athena, QuickSight, CodePipeline, ERM, ETL, crawlers e jobs);

• Democratização da malha de dados • Conhecimento de bancos de dados relacionais e não relacionais
• Experiência com o ecossistema AWS (S3, Lambda, IAM, etc.);
• Familiaridade com bancos de dados relacionais e não relacionais;
• Conhecimento de versionamento com Git.

Desejável: 

• Angular, Java, Kafka, Docker
• Observabilidade do Datadog
• Certificações AWS (ex.: AWS Certified Data Analytics, Developer Associate);
• Experiência com integração de sistemas e APIs REST;
    '''
    
    # Currículo de exemplo para teste
    sample_resume = '''
DESENVOLVEDOR DE DADOS SÊNIOR

Resumo:
Profissional com 8 anos de experiência em desenvolvimento de soluções de dados, especializado em Python, PySpark e ecossistema AWS. Expertise em construção de pipelines de dados escaláveis e implementação de práticas de engenharia de dados.

Habilidades Técnicas:
• Linguagens: Python, SQL, PySpark
• Cloud: AWS (S3, Lambda, Glue, IAM)
• Bancos de Dados: PostgreSQL, MongoDB, DynamoDB
• Ferramentas: Git, Docker, Apache Spark
• Metodologias: Ágil, Scrum, CI/CD

Experiência Profissional:
1. Engenheiro de Dados Sênior - Tech Solutions (2020-presente)
   - Desenvolvimento de pipelines de dados usando PySpark e AWS Glue
   - Implementação de soluções de armazenamento em S3 para 10TB de dados
   - Colaboração com equipes de negócio para definição de requisitos

2. Desenvolvedor Python - Data Corp (2018-2020)
   - Criação de scripts de automação em Python
   - Integração de APIs REST para coleta de dados
   - Manutenção de bancos de dados relacionais

Certificações:
• AWS Certified Developer Associate
• Scrum Master Certified

Educação:
• Bacharelado em Ciência da Computação - Universidade Federal
    '''
    
    print("=" * 80)
    print("TESTANDO VACANCY AGENT")
    print("=" * 80)
    vacancy_result = vacancy_agent.run(vacancy_description)
    print("Resultado da análise da vaga:")
    print(vacancy_result.content)
    print("\n" + "=" * 80)
    
    print("TESTANDO RESUME AGENT")
    print("=" * 80)
    resume_result = resume_agent.run(sample_resume)
    print("Resultado da análise do currículo:")
    print(resume_result.content)
    print("\n" + "=" * 80)
    
    print("TESTANDO RESUME UPGRADE AGENT")
    print("=" * 80)
    # Combinar currículo e vaga para o upgrade agent
    combined_input = f"""
DESCRIÇÃO DA VAGA:
{vacancy_description}

CURRÍCULO ATUAL:
{sample_resume}
"""
    upgrade_result = resume_upgrade_agent.run(combined_input)
    print("Sugestões de melhoria do currículo:")
    print(upgrade_result.content)
    print("\n" + "=" * 80)