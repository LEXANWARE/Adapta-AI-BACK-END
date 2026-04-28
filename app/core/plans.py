from enum import Enum
from typing import Dict, List, Any

class PlanType(str, Enum):
    FREE = "free"
    PRO = "pro"
    PREMIUM = "premium"

# Definição das permissões por plano
PLAN_PERMISSIONS: Dict[PlanType, Dict[str, Any]] = {
    PlanType.FREE: {
        "max_resumes": 2,
        "can_optimize": True,
        "can_analyze_quality": False,
        "can_check_ats": False,
        "can_use_full_pipeline": False,
        "can_use_adapt_full": False,
    },
    PlanType.PRO: {
        "max_resumes": 10,
        "can_optimize": True,
        "can_analyze_quality": True,
        "can_check_ats": True,
        "can_use_full_pipeline": False,
        "can_use_adapt_full": False,
    },
    PlanType.PREMIUM: {
        "max_resumes": 100,
        "can_optimize": True,
        "can_analyze_quality": True,
        "can_check_ats": True,
        "can_use_full_pipeline": True,
        "can_use_adapt_full": True,
    }
}

def check_permission(user_plan: str, permission: str) -> bool:
    """Verifica se o plano possui uma permissão específica."""
    plan = PLAN_PERMISSIONS.get(PlanType(user_plan), PLAN_PERMISSIONS[PlanType.FREE])
    return plan.get(permission, False)
