import os
from opentelemetry.sdk.trace import TracerProvider
from agno.workflow.types import StepInput, StepOutput
from agno.workflow import Condition, Parallel, Step, Workflow
from agno.db.sqlite import SqliteDb
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from openinference.instrumentation.agno import AgnoInstrumentor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from agents.models import (
    vacancy_agent,
    resume_agent,
    resume_upgrade_agent,
    resume_enricher_agent,
    ats_agent,
)

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
    ats_analysis_output = step_input.get_step_content("ATS Analysis") or ""

    # Extrair user_proceeds do objeto AtsAnalysis (HITL)
    user_proceeds = True  # Valor padrão se não conseguir extrair
    if ats_analysis_output and hasattr(ats_analysis_output, 'content'):
        try:
            ats_content = ats_analysis_output.content
            if hasattr(ats_content, 'user_proceeds') and ats_content.user_proceeds is not None:
                user_proceeds = ats_content.user_proceeds
        except:
            pass

    if not enriched_resume:
        enriched_resume = "(Nenhuma informação adicional fornecida)"

    # Se usuário não quis prosseguir, retornar mensagem
    if not user_proceeds:
        return StepOutput(
            content="Usuário optou por não prosseguir com a otimização.",
            success=False
        )

    combined = f"""
## CURRÍCULO ORIGINAL:
{data.get('curriculo', '')}

## ANÁLISE DA VAGA (Requisitos Identificados):
{vacancy_analysis}

## ANÁLISE DO CURRÍCULO ATUAL:
{resume_analysis}

## CURRÍCULO ENRIQUECIDO COM INFORMAÇÕES ADICIONAIS:
{enriched_resume}

## ANÁLISE ATS (Score e Recomendações):
{ats_analysis_output}

## DECISÃO DO USUÁRIO (HITL):
{'Prosseguir com otimização' if user_proceeds else 'Não prosseguir'}

---
TAREFA: Com base nas análises acima, crie um currículo otimizado no formato JSON Resume.
- Destaque as qualificações alinhadas aos requisitos da vaga
- Use palavras-chave identificadas na análise da vaga
- Foque em resultados e conquistas mensuráveis
- Considere as recomendações da análise ATS para melhorar o score
- Incorpore o feedback adicional do usuário quando aplicável
- Mantenha a estrutura completa do JSON Resume (incluindo campos como basics.profiles, volunteer, projects, etc.)
- Retorne APENAS o JSON válido
"""
    return StepOutput(content=combined)


def prepare_ats_input(step_input: StepInput) -> StepOutput:
    """Prepara input para análise ATS combinando vaga e currículo"""
    data = step_input.additional_data or {}

    vacancy_analysis = step_input.get_step_content("Analyze Vacancy") or ""
    resume_analysis = step_input.get_step_content("Analyze Resume") or ""
    resume_text = data.get('curriculo', '')

    content = f"""
## DESCRIÇÃO DA VAGA:
{data.get('vaga', '')}

## ANÁLISE DA VAGA (Requisitos Identificados):
{vacancy_analysis}

## CURRÍCULO (JSON):
{resume_analysis}

## CURRÍCULO ORIGINAL (TEXTO):
{resume_text}

---
TAREFA: Analise a compatibilidade ATS entre o currículo e a vaga.
Retorne o JSON com: ats_score (0-100), matched_keywords, missing_keywords, recommendations, strengths, weaknesses.
"""
    return StepOutput(content=content)


def update_ats_with_user_decision(step_input: StepInput) -> StepOutput:
    """
    Atualiza o objeto AtsAnalysis com a decisão do usuário (HITL).
    Este step é executado após o usuário fornecer o input.
    """
    ats_analysis_output = step_input.get_step_content("ATS Analysis")
    data = step_input.additional_data or {}
    user_input = data.get("user_input", {})
    user_proceeds = user_input.get("user_proceeds", True)

    if ats_analysis_output and hasattr(ats_analysis_output, 'content'):
        ats_content = ats_analysis_output.content
        if hasattr(ats_content, 'user_proceeds'):
            ats_content.user_proceeds = user_proceeds
            return StepOutput(content=ats_content)

    # Se não conseguir atualizar, retorna o output original
    return ats_analysis_output if ats_analysis_output else StepOutput(content=None)


resume_optimizer_workflow = Workflow(
    name="Resume Optimizer",
    description="Otimiza currículos para vagas específicas com análise ATS e HITL",
    db=SqliteDb(db_file="workflow.db"),  # Persistência para HITL
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
        Step(name="Prepare ATS Input", executor=prepare_ats_input),
        Step(
            name="ATS Analysis",
            agent=ats_agent,
            requires_user_input=True,
            user_input_message="Analise ATS concluída! Revise o score e recomendações abaixo. Deseja prosseguir com a otimização?",
            user_input_schema=[
                {
                    "name": "user_proceeds",
                    "field_type": "bool",
                    "description": "Deseja prosseguir com a otimização do currículo?",
                    "required": True
                }
            ],
        ),
        Step(name="Update ATS with User Decision", executor=update_ats_with_user_decision),
        Step(name="Combine Analyses", executor=combine_for_upgrade),
        Step(name="Generate Optimized Resume", agent=resume_upgrade_agent),
    ],
)