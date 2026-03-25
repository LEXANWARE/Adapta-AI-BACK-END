from datetime import datetime
from typing import Any, Dict, Optional
from dataclasses import dataclass, field
from agno.run.workflow import WorkflowRunOutput

@dataclass
class WorkflowSession:
    """Representa uma sessão de workflow em execução."""
    session_id: str
    run_id: str
    status: str
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    user_id: Optional[int] = None
    resume_id: Optional[int] = None
    additional_data: Dict[str, Any] = field(default_factory=dict)
    last_run_response: Optional[WorkflowRunOutput] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte sessão para dicionário."""
        return {
            "session_id": self.session_id,
            "run_id": self.run_id,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "user_id": self.user_id,
            "resume_id": self.resume_id,
            "additional_data": self.additional_data,
        }