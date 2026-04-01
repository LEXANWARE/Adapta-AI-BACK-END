import json
import logging
from typing import Any, Dict, List, Optional
from agno.run.workflow import WorkflowRunOutput

logger = logging.getLogger(__name__)


def extract_step_content(step_output) -> Optional[str]:
    """
    Extrai o conteúdo de um step output.

    Args:
        step_output: Output de um step do workflow

    Returns:
        Conteúdo do step como string, ou None se não disponível
    """
    if step_output is None:
        return None

    if hasattr(step_output, 'content'):
        content = step_output.content
        return str(content) if content else None

    return None


def extract_ats_analysis(step_outputs: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Extrai análise ATS dos outputs do workflow.

    Args:
        step_outputs: Dicionário de outputs dos steps (step_name -> step_output)

    Returns:
        Dicionário com análise ATS ou None se não encontrado
    """
    if not step_outputs:
        return None

    for step_name, step_output in step_outputs.items():
        content = extract_step_content(step_output)
        if not content:
            continue

        try:
            if isinstance(content, str):
                content_dict = json.loads(content)
            else:
                content_dict = content

            if isinstance(content_dict, dict) and 'ats_score' in content_dict:
                logger.info(f"Análise ATS extraída do step {step_name}: score={content_dict.get('ats_score')}")
                return content_dict
        except (json.JSONDecodeError, TypeError) as e:
            logger.warning(f"Erro ao extrair ATS de {step_name}: {e}")
            continue

    return None


def extract_optimized_resume(step_outputs: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Extrai currículo otimizado dos outputs do workflow.

    Args:
        step_outputs: Dicionário de outputs dos steps

    Returns:
        Dicionário com currículo em formato JSON Resume ou None
    """
    if not step_outputs:
        return None

    for step_name, step_output in step_outputs.items():
        content = extract_step_content(step_output)
        if not content:
            continue

        try:
            if isinstance(content, str):
                content_dict = json.loads(content)
            else:
                content_dict = content

            # Verifica se é um JSON Resume válido
            if isinstance(content_dict, dict) and 'basics' in content_dict:
                logger.info(f"Currículo otimizado extraído do step {step_name}")
                return content_dict
        except (json.JSONDecodeError, TypeError) as e:
            logger.warning(f"Erro ao extrair currículo de {step_name}: {e}")
            continue

    return None


def handle_hitl_requirement(requirement, user_data: Dict[str, Any]) -> bool:
    """
    Resolve um StepRequirement com input do usuário.

    Args:
        requirement: Objeto StepRequirement do Agno
        user_data: Dicionário com dados fornecidos pelo usuário

    Returns:
        True se resolvido com sucesso, False caso contrário
    """
    try:
        # Usa o método set_user_input do StepRequirement
        requirement.set_user_input(**user_data)
        is_resolved = getattr(requirement, 'is_resolved', True)
        logger.info(f"Requirement resolvido: is_resolved={is_resolved}")
        return is_resolved
    except Exception as e:
        logger.error(f"Erro ao resolver requirement: {e}")
        return False


def get_workflow_status(run_response: WorkflowRunOutput) -> str:
    """
    Determina o status atual do workflow com verificação robusta.
    
    Verifica múltiplos indicadores de status na ordem:
    1. Atributo 'status' como string ou enum
    2. Atributo 'is_paused' booleano
    3. Presença de steps_requiring_user_input não resolvidos
    4. Eventos de pausa na run_response

    Args:
        run_response: Resposta da execução do workflow

    Returns:
        Status: "paused", "completed", "cancelled", ou "running"
    """
    if not run_response:
        logger.warning("run_response é None, retornando 'completed' como default")
        return "completed"

    # Verifica atributo 'status' primeiro
    if hasattr(run_response, 'status'):
        status = run_response.status
        status_str = str(status).lower() if status else ""
        
        logger.debug(f"Status raw: {status}, status_str: {status_str}")
        
        # Verifica estados explícitos
        if 'paused' in status_str or 'waiting' in status_str or 'pending' in status_str:
            logger.info("Workflow status: paused (via atributo status)")
            return "paused"
        if 'cancelled' in status_str:
            logger.info("Workflow status: cancelled (via atributo status)")
            return "cancelled"
        if 'completed' in status_str or 'success' in status_str or 'finished' in status_str:
            logger.info("Workflow status: completed (via atributo status)")
            return "completed"
        if 'running' in status_str or 'executing' in status_str:
            logger.info("Workflow status: running (via atributo status)")
            return "running"

    # Verifica atributo 'is_paused'
    if hasattr(run_response, 'is_paused') and run_response.is_paused:
        logger.info("Workflow status: paused (via is_paused)")
        return "paused"

    # Verifica se há steps_requiring_user_input não resolvidos
    if hasattr(run_response, 'steps_requiring_user_input'):
        steps_input = run_response.steps_requiring_user_input
        if steps_input:
            # Verifica se algum step ainda não foi resolvido
            unresolved = [
                s for s in steps_input 
                if not getattr(s, 'is_resolved', True)
            ]
            if unresolved:
                logger.info(f"Workflow status: paused ({len(unresolved)} steps não resolvidos)")
                return "paused"

    # Verifica eventos de pausa
    if hasattr(run_response, 'events'):
        events = getattr(run_response, 'events', [])
        for event in events:
            event_name = str(getattr(event, 'event', '')).lower() if hasattr(event, 'event') else str(event).lower()
            if 'paused' in event_name or 'waiting' in event_name:
                logger.info(f"Workflow status: paused (via evento: {event_name})")
                return "paused"

    # Default: assume completado se não houver indicadores de pausa
    logger.info("Workflow status: completed (default)")
    return "completed"


def extract_workflow_result(run_response: WorkflowRunOutput) -> Optional[Dict[str, Any]]:
    """
    Extrai o resultado final do workflow.
    Utilizado principalmente para testes e debugging.

    Args:
        run_response: Resposta da execução do workflow

    Returns:
        Resultado final como dicionário ou None
    """
    # Tenta extrair do output principal
    if hasattr(run_response, 'output') and run_response.output:
        output = run_response.output
        if isinstance(output, dict):
            return output
        if hasattr(output, 'model_dump'):
            return output.model_dump()
        if isinstance(output, str):
            try:
                return json.loads(output)
            except json.JSONDecodeError:
                pass

    # Tenta extrair do content
    if hasattr(run_response, 'content') and run_response.content:
        content = run_response.content
        if isinstance(content, dict):
            return content
        if hasattr(content, 'model_dump'):
            return content.model_dump()
        if isinstance(content, str):
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                pass

    # Tenta extrair dos step outputs (último step com output)
    if hasattr(run_response, 'step_outputs') and run_response.step_outputs:
        # Pega o último step que executou
        step_outputs = run_response.step_outputs
        if isinstance(step_outputs, dict):
            for step_name in reversed(list(step_outputs.keys())):
                step_output = step_outputs[step_name]
                content = extract_step_content(step_output)
                if content:
                    try:
                        if isinstance(content, str):
                            return json.loads(content)
                        return content
                    except (json.JSONDecodeError, TypeError):
                        continue

    return None
