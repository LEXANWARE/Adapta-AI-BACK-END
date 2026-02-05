import os
import json
from dotenv import load_dotenv

from agno.workflow import Condition, Parallel, Step, Workflow
from agno.workflow.types import StepInput, StepOutput

from agents.models import (
    vacancy_agent,
    resume_agent,
    resume_upgrade_agent,
    resume_enricher_agent,
)
from agents.utils.pdf import gerar_pdf 

load_dotenv()

def has_additional_info(step_input: StepInput) -> bool:
    """Retorna True se houver informações adicionais do candidato"""
    data = step_input.additional_data or {}
    info = data.get("info_adicional", "")
    return bool(info and info.strip())


def prepare_vacancy_input(step_input: StepInput) -> StepOutput:
    """Prepara input específico para análise da vaga"""
    data = step_input.additional_data or {}
    vaga = data.get("vaga", "Vaga não fornecida")
    return StepOutput(content=vaga)


def prepare_resume_input(step_input: StepInput) -> StepOutput:
    """Prepara input específico para análise do currículo"""
    data = step_input.additional_data or {}
    curriculo = data.get("curriculo", "Currículo não fornecido")
    return StepOutput(content=curriculo)


def prepare_enrich_input(step_input: StepInput) -> StepOutput:
    """Prepara input para enriquecimento com info adicional"""
    data = step_input.additional_data or {}
    curriculo = data.get("curriculo", "")
    info_adicional = data.get("info_adicional", "")
    
    content = f"""
CURRÍCULO ATUAL:
{curriculo}

INFORMAÇÕES ADICIONAIS DO CANDIDATO:
{info_adicional}

Integre as informações adicionais ao currículo existente.
"""
    return StepOutput(content=content)


def combine_for_upgrade(step_input: StepInput) -> StepOutput:
    """Combina todas as análises para o agente de upgrade"""
    data = step_input.additional_data or {}
    
    # Acessa outputs dos steps anteriores
    vacancy_analysis = step_input.get_step_content("Analyze Vacancy") or ""
    resume_analysis = step_input.get_step_content("Analyze Resume") or ""
    enriched_resume = step_input.get_step_content("Enrich Resume") or ""
    
    combined = f"""
## CURRÍCULO ORIGINAL:
{data.get('curriculo', '')}

## ANÁLISE DA VAGA (Requisitos Identificados):
{vacancy_analysis}

## ANÁLISE DO CURRÍCULO ATUAL:
{resume_analysis}

## CURRÍCULO ENRIQUECIDO COM INFORMAÇÕES ADICIONAIS:
{enriched_resume if enriched_resume else "Nenhuma informação adicional fornecida"}

---
TAREFA: Com base nas análises acima, crie um currículo otimizado no formato JSON Resume.
- Destaque as qualificações alinhadas aos requisitos da vaga
- Use palavras-chave identificadas na análise da vaga
- Foque em resultados e conquistas mensuráveis
"""
    return StepOutput(content=combined)


def generate_pdf_step(step_input: StepInput) -> StepOutput:
    """Gera o PDF do currículo otimizado"""
    # Pega o output do step anterior (currículo otimizado)
    optimized_resume = step_input.previous_step_content
    
    # Se for um objeto Pydantic (ResumeScheme), converte para dict
    if hasattr(optimized_resume, 'model_dump'):
        resume_dict = optimized_resume.model_dump()
    elif isinstance(optimized_resume, str):
        try:
            resume_dict = json.loads(optimized_resume)
        except json.JSONDecodeError:
            return StepOutput(
                content="Erro: Não foi possível processar o currículo",
                success=False
            )
    else:
        resume_dict = optimized_resume
    
    # Gera o PDF
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    
    nome = resume_dict.get("basics", {}).get("name", "curriculo")
    nome_arquivo = nome.lower().replace(" ", "_")
    arquivo_pdf = f"{output_dir}/{nome_arquivo}_otimizado.pdf"
    arquivo_json = f"{output_dir}/{nome_arquivo}_otimizado.json"
    
    # Salva JSON
    with open(arquivo_json, 'w', encoding='utf-8') as f:
        json.dump(resume_dict, f, ensure_ascii=False, indent=2)
    
    # Gera PDF
    gerar_pdf(resume_dict, arquivo_pdf)
    
    return StepOutput(
        content=f"Currículo otimizado gerado com sucesso!\n- PDF: {arquivo_pdf}\n- JSON: {arquivo_json}",
        success=True
    )


# === WORKFLOW COMPLETO ===
resume_optimizer_workflow = Workflow(
    name="Resume Optimizer",
    description="Otimiza currículos para vagas específicas e gera PDF",
    steps=[
        # 1️⃣ Preparação de inputs em paralelo
        Parallel(
            Step(name="Prepare Vacancy", executor=prepare_vacancy_input),
            Step(name="Prepare Resume", executor=prepare_resume_input),
            Condition(
                name="Check Additional Info",
                evaluator=has_additional_info,
                steps=[Step(name="Prepare Enrich", executor=prepare_enrich_input)],
            ),
            name="Prepare Phase"
        ),
        
        # 2️⃣ Análises com agentes em paralelo
        Parallel(
            Step(name="Analyze Vacancy", agent=vacancy_agent),
            Step(name="Analyze Resume", agent=resume_agent),
            Condition(
                name="Run Enrichment",
                evaluator=has_additional_info,
                steps=[Step(name="Enrich Resume", agent=resume_enricher_agent)],
            ),
            name="Analysis Phase"
        ),
        
        # 3️⃣ Combina as análises
        Step(name="Combine Analyses", executor=combine_for_upgrade),
        
        # 4️⃣ Gera currículo otimizado (retorna ResumeScheme)
        Step(name="Generate Optimized Resume", agent=resume_upgrade_agent),
        
        # 5️⃣ Gera PDF e JSON
        Step(name="Generate PDF", executor=generate_pdf_step),
    ],
)


# === EXECUÇÃO ===
if __name__ == "__main__":
    result = resume_optimizer_workflow.run(
        input="Otimize meu currículo para esta vaga",
        additional_data={
            "curriculo": """
Maria Silva
Email: maria@email.com | Tel: (11) 98765-4321
São Paulo, SP

EXPERIÊNCIA PROFISSIONAL:

Desenvolvedora Full Stack - TechCorp (2021-2024)
- Desenvolvimento de APIs REST com Python e Django
- Frontend com React e TypeScript
- Banco de dados PostgreSQL

Estagiária de Desenvolvimento - StartupXYZ (2020-2021)
- Suporte ao desenvolvimento de aplicações web
- Testes automatizados

FORMAÇÃO:
Ciência da Computação - Universidade de São Paulo (2020)

HABILIDADES:
Python, Django, React, TypeScript, PostgreSQL, Git
            """,
            "vaga": """
Vaga: Desenvolvedora Backend Sênior
Empresa: BigTech Brasil

Requisitos:
- 4+ anos de experiência com Python
- Experiência com FastAPI ou Django
- Conhecimento em AWS (EC2, S3, Lambda)
- Docker e Kubernetes
- Inglês avançado

Diferenciais:
- Experiência com microsserviços
- CI/CD (GitHub Actions, Jenkins)
- Liderança técnica
            """,
            "info_adicional": """
- Tenho certificação AWS Solutions Architect Associate
- Liderei a migração de monolito para microsserviços no último emprego
- Inglês fluente (morei 6 meses no Canadá)
- Implementei CI/CD com GitHub Actions em 3 projetos
            """,
        },
    )
    
    print("\n" + "=" * 50)
    print("RESULTADO FINAL:")
    print("=" * 50)
    print(result.content)