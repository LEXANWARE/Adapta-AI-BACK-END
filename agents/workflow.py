import os
from opentelemetry.sdk.trace import TracerProvider
from agno.workflow.types import StepInput, StepOutput
from agno.workflow import Condition, Parallel, Step, Workflow
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from openinference.instrumentation.agno import AgnoInstrumentor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from agents.models import (
    vacancy_agent,
    resume_agent,
    resume_upgrade_agent,
    resume_enricher_agent,
)
from agents.utils.pdf import imprimir_json, salvar_json_final, gerar_pdf

endpoint = "https://api.smith.langchain.com/otel/v1/traces"

headers = {
    "x-api-key": os.getenv("LANGSMITH_API_KEY"),
    "Langsmith-Project": os.getenv("LANGSMITH_PROJECT"),
}

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
    """Prepara input para enriquecimento com info adicional."""
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

    vacancy_analysis = step_input.get_step_content("Analyze Vacancy") or ""
    resume_analysis = step_input.get_step_content("Analyze Resume") or ""
    enriched_resume = step_input.get_step_content("Enrich Resume") or ""

    if not enriched_resume:
        enriched_resume = "(Nenhuma informação adicional fornecida)"

    combined = f"""
## CURRÍCULO ORIGINAL:
{data.get('curriculo', '')}

## ANÁLISE DA VAGA (Requisitos Identificados):
{vacancy_analysis}

## ANÁLISE DO CURRÍCULO ATUAL:
{resume_analysis}

## CURRÍCULO ENRIQUECIDO COM INFORMAÇÕES ADICIONAIS:
{enriched_resume}

---
TAREFA: Com base nas análises acima, crie um currículo otimizado no formato JSON Resume.
- Destaque as qualificações alinhadas aos requisitos da vaga
- Use palavras-chave identificadas na análise da vaga
- Foque em resultados e conquistas mensuráveis
- Mantenha a estrutura completa do JSON Resume (incluindo campos como basics.profiles, volunteer, projects, etc.)
- Retorne APENAS o JSON válido
"""
    return StepOutput(content=combined)

def generate_pdf(step_input: StepInput) -> StepOutput:
    try:
        resume = step_input.get_step_content("Generate Optimized Resume")
        resume_content = resume.model_dump()

        imprimir_json("CURRÍCULO FINAL (PRONTO PRO ENVIO)", resume)

        salvar_json_final(resume_content, 'curriculo.json')

        gerar_pdf(resume_content, 'curriculo_completo.pdf')

        return StepOutput(
            content="PDF Gerado com Sucesso",
            success=True
        )
    except Exception as e:
        return StepOutput(
            content=f"Erro ao gerrar PDF: {str(e)}",
            success=False
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
        Step(name="Create PDF", executor=generate_pdf)
    ],
)