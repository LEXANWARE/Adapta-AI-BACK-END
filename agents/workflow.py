import json
from textwrap import dedent
from agno.db.sqlite import SqliteDb
from agno.workflow import Condition, Parallel, Step, Workflow
from agno.workflow.types import StepInput, StepOutput, OnReject, OnError
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
    """Combina todas as análises para o agente de upgrade"""
    data = step_input.additional_data or {}

    vacancy_analysis = step_input.get_step_content("Analyze Vacancy") or ""
    resume_analysis = step_input.get_step_content("Analyze Resume") or ""
    enriched_resume = step_input.get_step_content("Enrich Resume") or ""
    ats_analysis_output = step_input.get_step_content("ATS Analysis") or ""

    if not enriched_resume:
        enriched_resume = "(Nenhuma informação adicional fornecida)"

    combined = dedent(f"""
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
    Prosseguir com otimização

    ---
    TAREFA: Com base nas análises acima, crie um currículo otimizado no formato JSON Resume.
    - Destaque as qualificações alinhadas aos requisitos da vaga
    - Use palavras-chave identificadas na análise da vaga
    - Foque em resultados e conquistas mensuráveis
    - Considere as recomendações da análise ATS para melhorar o score
    - Incorpore o feedback adicional do usuário quando aplicável
    - Mantenha a estrutura completa do JSON Resume (incluindo campos como basics.profiles, volunteer, projects, etc.)
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
    """Processa a confirmação do usuário (HITL) e armazena a decisão"""

    # Tenta obter user_input de diferentes formas compatíveis com agno
    user_input = None
    if hasattr(step_input, 'user_input') and step_input.user_input:
        user_input = step_input.user_input
    elif hasattr(step_input, 'additional_data') and step_input.additional_data:
        user_input = step_input.additional_data
    else:
        user_input = {}

    user_proceeds = user_input.get("user_proceeds", True)
    feedback = user_input.get("feedback", "")

    return StepOutput(
        content=f"Usuário decidiu: {'Prosseguir' if user_proceeds else 'Não prosseguir'}"
    )


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