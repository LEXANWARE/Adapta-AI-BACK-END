import logging
import os
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

SUPABASE_URL = (
    os.getenv("SUPABASE_URL")
    or os.getenv("VITE_SUPABASE_URL")
    or "https://gazidqznxtoaadrbsqfl.supabase.co"
)


def _get_supabase_anon_key() -> Optional[str]:
    return (
        os.getenv("SUPABASE_ANON_KEY")
        or os.getenv("SUPABASE_PUBLISHABLE_KEY")
        or os.getenv("VITE_SUPABASE_PUBLISHABLE_KEY")
    )


def fetch_profile_plan(supabase_user_id: str, access_token: str) -> Optional[str]:
    """Busca o plano do usuário na tabela profiles do Supabase."""
    anon_key = _get_supabase_anon_key()
    if not anon_key:
        logger.warning(
            "Chave Supabase não configurada (SUPABASE_ANON_KEY, SUPABASE_PUBLISHABLE_KEY "
            "ou VITE_SUPABASE_PUBLISHABLE_KEY); plano não será sincronizado."
        )
        return None

    url = f"{SUPABASE_URL}/rest/v1/profiles"
    params = {"id": f"eq.{supabase_user_id}", "select": "plan"}
    headers = {
        "Authorization": f"Bearer {access_token}",
        "apikey": anon_key,
    }

    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(url, params=params, headers=headers)
            if response.status_code != 200:
                logger.warning("Falha ao buscar profile no Supabase: %s", response.status_code)
                return None
            rows = response.json()
            if rows and isinstance(rows, list):
                plan = rows[0].get("plan")
                if plan in ("free", "pro", "premium"):
                    return plan
    except Exception as exc:
        logger.warning("Erro ao consultar plano no Supabase: %s", exc)

    return None
