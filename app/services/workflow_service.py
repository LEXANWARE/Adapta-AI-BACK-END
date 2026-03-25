from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from agno.run.workflow import WorkflowRunOutput
from app.schemas.wf_session import WorkflowSession
from agents.workflow import resume_optimizer_workflow


class WorkflowSessionManager:
    """
    Gerencia sessões de workflow HITL.
    
    Usa o SQLite nativo do Agno para persistência das execuções,
    mantendo um registro em memória das sessões ativas.
    """
    
    def __init__(self):
        self._sessions: Dict[str, WorkflowSession] = {}
        self._workflow = resume_optimizer_workflow
    
    def start_workflow(
        self,
        input_text: str,
        additional_data: Dict[str, Any],
        user_id: Optional[int] = None,
        resume_id: Optional[int] = None,
    ) -> Tuple[WorkflowRunOutput, WorkflowSession]:
        """
        Inicia uma nova execução de workflow.
        
        Args:
            input_text: Input principal do workflow
            additional_data: Dados adicionais (vaga, currículo, info adicional)
            user_id: ID do usuário (opcional)
            resume_id: ID do currículo (opcional)
            
        Returns:
            Tuple (run_response, session)
        """
        # Executa o workflow
        run_response = self._workflow.run(
            input=input_text,
            additional_data=additional_data,
        )
        
        # Cria sessão
        session = WorkflowSession(
            session_id=run_response.session_id if hasattr(run_response, 'session_id') else str(id(run_response)),
            run_id=run_response.run_id if hasattr(run_response, 'run_id') else str(id(run_response)),
            status=self._determine_status(run_response),
            user_id=user_id,
            resume_id=resume_id,
            additional_data=additional_data,
            last_run_response=run_response,
        )
        
        # Armazena sessão
        self._sessions[session.session_id] = session
        
        return run_response, session
    
    def continue_workflow(
        self,
        session_id: str,
        user_input: Dict[str, Any],
        step_requirements: Optional[List[Any]] = None,
    ) -> Tuple[WorkflowRunOutput, WorkflowSession]:
        """
        Continua um workflow pausado com input do usuário.
        
        Args:
            session_id: ID da sessão
            user_input: Dados fornecidos pelo usuário
            step_requirements: Lista de StepRequirements para resolver
            
        Returns:
            Tuple (run_response, session)
            
        Raises:
            ValueError: Se sessão não encontrada ou não estiver pausada
        """
        # Recupera sessão
        session = self._sessions.get(session_id)
        if not session:
            raise ValueError(f"Sessão não encontrada: {session_id}")
        
        if session.status != "paused":
            raise ValueError(f"Sessão não está pausada: {session.status}")
        
        # Recupera run_response anterior
        run_response = session.last_run_response
        if not run_response:
            raise ValueError("Run response não encontrado")
        
        # Resolve os requirements com user_input
        if hasattr(run_response, 'step_requirements') and run_response.step_requirements:
            for requirement in run_response.step_requirements:
                if requirement.requires_user_input and not requirement.is_resolved:
                    requirement.set_user_input(**user_input)
        
        # Continua execução
        continued_response = self._workflow.continue_run(
            run_response=run_response,
            step_requirements=run_response.step_requirements if hasattr(run_response, 'step_requirements') else None,
        )
        
        # Atualiza sessão
        session.status = self._determine_status(continued_response)
        session.updated_at = datetime.now()
        session.last_run_response = continued_response
        
        return continued_response, session
    
    def cancel_workflow(self, session_id: str) -> WorkflowSession:
        """
        Cancela uma sessão de workflow.
        
        Args:
            session_id: ID da sessão
            
        Returns:
            Sessão atualizada
            
        Raises:
            ValueError: Se sessão não encontrada
        """
        session = self._sessions.get(session_id)
        if not session:
            raise ValueError(f"Sessão não encontrada: {session_id}")
        
        session.status = "cancelled"
        session.updated_at = datetime.now()
        
        return session
    
    def get_session(self, session_id: str) -> Optional[WorkflowSession]:
        """
        Recupera uma sessão pelo ID.
        
        Args:
            session_id: ID da sessão
            
        Returns:
            Sessão ou None
        """
        return self._sessions.get(session_id)
    
    def get_user_sessions(self, user_id: int) -> List[WorkflowSession]:
        """
        Recupera todas as sessões de um usuário.
        
        Args:
            user_id: ID do usuário
            
        Returns:
            Lista de sessões
        """
        return [
            session for session in self._sessions.values()
            if session.user_id == user_id
        ]
    
    def _determine_status(self, run_response: WorkflowRunOutput) -> str:
        """Determina o status baseado na run_response."""
        if hasattr(run_response, 'is_paused') and run_response.is_paused:
            return "paused"
        
        if hasattr(run_response, 'status'):
            status = str(run_response.status).lower()
            if 'completed' in status or 'success' in status:
                return "completed"
            if 'cancelled' in status or 'failed' in status:
                return "cancelled"
        
        return "completed"
    
    def get_steps_requiring_input(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Obtém steps que requerem input do usuário.
        
        Args:
            session_id: ID da sessão
            
        Returns:
            Lista de dicts com informações dos steps
        """
        session = self._sessions.get(session_id)
        if not session or not session.last_run_response:
            return []
        
        run_response = session.last_run_response
        steps = []
        
        if hasattr(run_response, 'steps_requiring_user_input'):
            for req in run_response.steps_requiring_user_input:
                steps.append({
                    "step_id": req.step_id,
                    "step_name": req.step_name,
                    "user_input_message": req.user_input_message,
                    "user_input_schema": self._convert_schema(req.user_input_schema),
                    "is_resolved": req.is_resolved,
                })
        
        return steps
    
    def _convert_schema(self, schema: Optional[List[Any]]) -> List[Dict[str, Any]]:
        """Converte schema para lista de dicts serializável."""
        if not schema:
            return []
        
        result = []
        for item in schema:
            if hasattr(item, '__dict__'):
                # É um objeto UserInputField
                result.append({
                    "name": getattr(item, 'name', None),
                    "field_type": getattr(item, 'field_type', 'str'),
                    "description": getattr(item, 'description', None),
                    "required": getattr(item, 'required', True),
                })
            elif isinstance(item, dict):
                result.append(item)
        
        return result


# Instância global do gerenciador
workflow_session_manager = WorkflowSessionManager()
