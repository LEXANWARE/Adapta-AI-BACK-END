import json
from typing import Any, Dict, List, Optional
from agno.run.workflow import WorkflowRunOutput


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
                return content_dict
        except (json.JSONDecodeError, TypeError):
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
                return content_dict
        except (json.JSONDecodeError, TypeError):
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
        return requirement.is_resolved
    except Exception as e:
        print(f"Erro ao resolver requirement: {e}")
        return False


def get_workflow_status(run_response: WorkflowRunOutput) -> str:
    """
    Determina o status atual do workflow.
    
    Args:
        run_response: Resposta da execução do workflow
        
    Returns:
        Status: "paused", "completed", "cancelled", ou "running"
    """
    if not hasattr(run_response, 'status'):
        # Se não tem status, verifica is_paused
        if hasattr(run_response, 'is_paused') and run_response.is_paused:
            return "paused"
        return "completed"
    
    status = str(run_response.status).lower()
    
    if 'paused' in status:
        return "paused"
    elif 'completed' in status or 'success' in status:
        return "completed"
    elif 'cancelled' in status or 'failed' in status:
        return "cancelled"
    else:
        return "running"


def extract_workflow_result(run_response: WorkflowRunOutput) -> Optional[Dict[str, Any]]:
    """
    Extrai o resultado final do workflow.
    
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


def format_user_input_message(message: str, previous_output: str = None) -> str:
    """
    Formata a mensagem de input do usuário substituindo placeholders.
    
    Args:
        message: Mensagem template
        previous_output: Output do step anterior para substituir {previous_output}
        
    Returns:
        Mensagem formatada
    """
    if previous_output and '{previous_output}' in message:
        return message.replace('{previous_output}', previous_output)
    return message


def validate_user_input(user_data: Dict[str, Any], schema: List[Dict[str, Any]]) -> tuple[bool, str]:
    """
    Valida input do usuário contra o schema.
    
    Args:
        user_data: Dados fornecidos pelo usuário
        schema: Schema esperado (lista de dicts com name, field_type, required)
        
    Returns:
        Tuple (is_valid, error_message)
    """
    for field in schema:
        field_name = field.get('name')
        field_type = field.get('field_type', 'str')
        required = field.get('required', True)
        
        # Verifica campo obrigatório
        if required and field_name not in user_data:
            return False, f"Campo obrigatório '{field_name}' não fornecido"
        
        if field_name in user_data:
            value = user_data[field_name]
            
            # Valida tipo
            if field_type == 'bool' and not isinstance(value, bool):
                return False, f"Campo '{field_name}' deve ser booleano"
            elif field_type == 'int' and not isinstance(value, int):
                return False, f"Campo '{field_name}' deve ser inteiro"
            elif field_type == 'float' and not isinstance(value, (int, float)):
                return False, f"Campo '{field_name}' deve ser numérico"
            elif field_type == 'str' and not isinstance(value, str):
                return False, f"Campo '{field_name}' deve ser string"
    
    return True, ""
