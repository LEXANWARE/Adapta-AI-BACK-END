import os
import json
import logging
from textwrap import dedent
from agno.db.sqlite import SqliteDb
from agno.workflow import Condition, Parallel, Step, Workflow
from agno.workflow.types import StepInput, StepOutput, OnReject, OnError
from opentelemetry import trace as trace_api
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor # Use Batch instead of Simple
from openinference.instrumentation.agno import AgnoInstrumentor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from agents.models import (
    vacancy_agent,
    resume_agent,
    resume_upgrade_agent,
    resume_enricher_agent,
    ats_agent,
)

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

    content = dedent(f"""
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
    """)
    return StepOutput(content=content)


def combine_for_upgrade(step_input: StepInput) -> StepOutput:
    """Combina todas as análises para o agente de upgrade.

    Verifica a decisão do usuário antes de prosseguir com a otimização.
    Extrai corretamente os dados dos objetos Pydantic retornados pelos agentes.
    """

    logger = logging.getLogger(__name__)
    data = step_input.additional_data or {}

    # Obtém resultado da confirmação do usuário
    user_confirmation_raw = step_input.get_step_content("User Confirmation") or ""
    user_proceeds = True  # Default para True se não encontrado

    try:
        if user_confirmation_raw:
            # Tenta parsear como JSON (novo formato)
            user_confirmation = json.loads(user_confirmation_raw)
            user_proceeds = user_confirmation.get("user_proceeds", True)
            logger.info(f"Confirmação do usuário (JSON): {user_confirmation}")
    except (json.JSONDecodeError, TypeError):
        # Formato antigo: string de texto
        if "Não prosseguir" in user_confirmation_raw or "cancel" in user_confirmation_raw.lower():
            user_proceeds = False
        logger.info(f"Confirmação do usuário (texto): {user_confirmation_raw}, user_proceeds={user_proceeds}")

    # Se usuário não prosseguir, retorna mensagem de cancelamento
    if not user_proceeds:
        return StepOutput(
            content=json.dumps({
                "cancelled": True,
                "reason": "Usuário optou por não prosseguir com a otimização"
            }, ensure_ascii=False)
        )

    # Prossegue com combinação normal
    # Extrai análises dos agentes (podem ser objetos Pydantic ou strings)
    vacancy_analysis_raw = step_input.get_step_content("Analyze Vacancy") or ""
    resume_analysis_raw = step_input.get_step_content("Analyze Resume") or ""
    enriched_resume_raw = step_input.get_step_content("Enrich Resume") or ""
    ats_analysis_output = step_input.get_step_content("ATS Analysis") or ""

    # Converte para string se necessário
    vacancy_analysis = str(vacancy_analysis_raw) if vacancy_analysis_raw else ""
    resume_analysis = str(resume_analysis_raw) if resume_analysis_raw else ""
    enriched_resume = str(enriched_resume_raw) if enriched_resume_raw else ""
    ats_analysis = str(ats_analysis_output) if ats_analysis_output else ""

    # Logging para debug
    logger.info(f"Vacancy analysis length: {len(vacancy_analysis)}")
    logger.info(f"Resume analysis length: {len(resume_analysis)}")
    logger.info(f"Enriched resume length: {len(enriched_resume)}")
    logger.info(f"ATS analysis length: {len(ats_analysis)}")

    # Usa o currículo enriquecido se disponível, senão usa o original
    resume_base = enriched_resume if enriched_resume and enriched_resume != "None" else data.get('curriculo', '')

    if not resume_base:
        resume_base = "(Nenhuma informação de currículo fornecida)"

    combined = dedent(f"""
    ## CURRÍCULO (ORIGINAL OU ENRIQUECIDO):
    {resume_base}

    ## ANÁLISE DA VAGA (Requisitos Identificados):
    {vacancy_analysis}

    ## ANÁLISE DO CURRÍCULO ATUAL:
    {resume_analysis}

    ## ANÁLISE ATS (Score e Recomendações):
    {ats_analysis}

    ## DECISÃO DO USUÁRIO (HITL):
    Prosseguir com otimização

    ---
    TAREFA: Com base nas análises acima, crie um currículo otimizado no formato JSON Resume.
    
    IMPORTANTE:
    - Use APENAS os dados REAIS do currículo fornecido acima (NÃO invente dados)
    - Mantenha o nome, experiências, formação e informações do candidato original
    - Destaque as qualificações alinhadas aos requisitos da vaga
    - Use palavras-chave identificadas na análise da vaga
    - Foque em resultados e conquistas mensuráveis
    - Considere as recomendações da análise ATS para melhorar o score
    - Incorpore o feedback adicional do usuário quando aplicável
    - Mantenha a estrutura completa do JSON Resume (basics, work, education, skills, projects, languages, profiles)
    - Retorne APENAS o JSON válido
    """)
    return StepOutput(content=combined)


def prepare_ats_input(step_input: StepInput) -> StepOutput:
    """Prepara input para análise ATS combinando vaga e currículo"""
    data = step_input.additional_data or {}

    vacancy_analysis = step_input.get_step_content("Analyze Vacancy") or ""
    resume_analysis = step_input.get_step_content("Analyze Resume") or ""
    resume_text = data.get('curriculo', '')

    content = dedent(f"""
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
    Retorne APENAS a análise no formato JSON especificado.
    """)
    return StepOutput(content=content)


def extract_ats_score(step_input: StepInput) -> StepOutput:
    """Extrai o score ATS do resultado para usar na mensagem de confirmação"""
    ats_result = step_input.get_step_content("ATS Analysis") or ""

    try:
        ats_data = json.loads(ats_result)
        score = ats_data.get("ats_score", "N/A")
        message = f"Score ATS: {score}/100\n\nRecomendações principais:\n"
        for rec in ats_data.get("recommendations", [])[:3]:
            message += f"- {rec}\n"
        return StepOutput(content=message)
    except:
        return StepOutput(content="Análise ATS concluída.")


def process_user_confirmation(step_input: StepInput) -> StepOutput:
    """Processa a confirmação do usuário (HITL) e armazena a decisão.
    
    Retorna um JSON estruturado com a decisão do usuário para facilitar
    o processamento downstream no workflow.
    """
    
    logger = logging.getLogger(__name__)
    logger.info(f"Processando confirmação do usuário. step_input: {step_input}")

    # Tenta obter user_input de diferentes formas compatíveis com agno
    user_input = None
    if hasattr(step_input, 'user_input') and step_input.user_input:
        user_input = step_input.user_input
        logger.info(f"user_input obtido de step_input.user_input: {user_input}")
    elif hasattr(step_input, 'additional_data') and step_input.additional_data:
        user_input = step_input.additional_data
        logger.info(f"user_input obtido de step_input.additional_data: {user_input}")
    else:
        user_input = {}
        logger.warning("Nenhum user_input encontrado, usando dict vazio")

    user_proceeds = user_input.get("user_proceeds", True)
    feedback = user_input.get("feedback", "")
    
    logger.info(f"Decisão do usuário: user_proceeds={user_proceeds}, feedback={feedback}")

    # Retorna JSON estruturado com a decisão
    decision_data = {
        "user_proceeds": user_proceeds,
        "feedback": feedback or None,
        "decision": "proceed" if user_proceeds else "cancel"
    }
    
    return StepOutput(
        content=json.dumps(decision_data, ensure_ascii=False)
    )

endpoint = "https://api.smith.langchain.com/otel/v1/traces"
headers = {
    "x-api-key": os.getenv("LANGSMITH_API_KEY"),
    "Langsmith-Project": os.getenv("LANGSMITH_PROJECT")
}

tracer_provider = TracerProvider()

# 3. Use BatchSpanProcessor (Documentation recommended for production/complex workflows)
tracer_provider.add_span_processor(
    BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint, headers=headers))
)
trace_api.set_tracer_provider(tracer_provider=tracer_provider)

# 4. Instrument Agno
AgnoInstrumentor().instrument()

resume_optimizer_workflow = Workflow(
    name="Resume Optimizer",
    description="Otimiza currículos para vagas específicas com análise ATS e HITL",
    db=SqliteDb(db_file="workflow.db"),
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
        
        Step(
            name="Prepare ATS Input", 
            executor=prepare_ats_input
        ),
        Step(
            name="ATS Analysis",
            agent=ats_agent,
        ),
        Step(
            name="Extract ATS Score",
            executor=extract_ats_score,
        ),
        Step(
            name="User Confirmation",
            executor=process_user_confirmation,
            requires_user_input=True,
            on_reject=OnReject.cancel,
            on_error=OnError.pause,
            user_input_message="""📊 Análise ATS concluída!

            {previous_output}

            Deseja prosseguir com a otimização do currículo baseado nas recomendações acima?

            Isso irá gerar uma versão otimizada do seu currículo destacando:
            - Palavras-chave alinhadas com a vaga
            - Experiências mais relevantes
            - Melhorias sugeridas pela análise ATS

            Escolha uma opção:
            1. ✅ Sim, prosseguir com otimização
            2. ❌ Não, manter currículo original

            Por favor, confirme sua decisão:""",
            user_input_schema=[
                {
                    "name": "user_proceeds",
                    "field_type": "bool",
                    "description": "Prosseguir com otimização?",
                    "required": True
                },
                {
                    "name": "feedback",
                    "field_type": "string",
                    "description": "Feedback adicional (opcional)",
                    "required": False
                },
            ],
        ),
        Step(
            name="Combine Analyses", 
            executor=combine_for_upgrade
        ),
        Step(
            name="Generate Optimized Resume", 
            agent=resume_upgrade_agent
        ),
    ],
)