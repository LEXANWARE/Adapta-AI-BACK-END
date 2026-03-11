import os
import json
from agno.workflow.types import StepInput, StepOutput
from agno.workflow import Condition, Parallel, Step, Workflow
from opentelemetry import trace as trace_api
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from openinference.instrumentation.agno import AgnoInstrumentor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

from agents.utils.pdf import gerar_pdf 
from agents.models import (
    vacancy_agent,
    resume_agent,
    resume_upgrade_agent,
    resume_enricher_agent,
)

# Set the endpoint and headers for LangSmith
endpoint = "https://api.smith.langchain.com/otel/v1/traces"

headers = {
    "x-api-key": os.getenv("LANGSMITH_API_KEY"),
    "Langsmith-Project": os.getenv("LANGSMITH_PROJECT"),
}

# Configure the tracer provider
tracer_provider = TracerProvider()
tracer_provider.add_span_processor(
    SimpleSpanProcessor(OTLPSpanExporter(endpoint=endpoint, headers=headers))
)
AgnoInstrumentor().instrument(tracer_provider=tracer_provider)


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
    """Prepara input para enriquecimento com info adicional.

    O currículo pode ser texto livre ou já estar em JSON Resume.
    O agente de enriquecimento sempre deve devolver um JSON Resume válido.
    """
    data = step_input.additional_data or {}
    curriculo = data.get("curriculo", "")
    info_adicional = data.get("info_adicional", "")
    
    content = f"""
### CURRICULO_ATUAL
O bloco abaixo contém o currículo atual do candidato. Ele pode estar em TEXTO LIVRE ou já em formato JSON Resume.
Use esse currículo como base estrutural.

{curriculo}

### INFORMACOES_ADICIONAIS
O bloco abaixo contém informações adicionais enviadas pelo candidato. Use-as para enriquecer o currículo:

{info_adicional}

### TAREFA
Atualize o currículo para incluir as informações adicionais, mantendo um único currículo final em formato JSON Resume.
Respeite toda a estrutura do JSON Resume (basics, work, education, skills, projects, languages, etc.).
Retorne APENAS o JSON do currículo atualizado.
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
    
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    
    nome = resume_dict.get("basics", {}).get("name", "curriculo")
    nome_arquivo = nome.lower().replace(" ", "_")
    arquivo_pdf = f"{output_dir}/{nome_arquivo}_otimizado.pdf"
    arquivo_json = f"{output_dir}/{nome_arquivo}_otimizado.json"
    
    with open(arquivo_json, 'w', encoding='utf-8') as f:
        json.dump(resume_dict, f, ensure_ascii=False, indent=2)
    
    gerar_pdf(resume_dict, arquivo_pdf)
    
    return StepOutput(
        content=f"Currículo otimizado gerado com sucesso!\n- PDF: {arquivo_pdf}\n- JSON: {arquivo_json}",
        success=True
    )


resume_optimizer_workflow = Workflow(
    name="Resume Optimizer",
    description="Otimiza currículos para vagas específicas e gera PDF",
    steps=[
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
        Step(name="Combine Analyses", executor=combine_for_upgrade),
        Step(name="Generate Optimized Resume", agent=resume_upgrade_agent),
    ],
)