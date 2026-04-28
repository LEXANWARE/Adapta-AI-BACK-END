import os
from fastapi import APIRouter, Depends, HTTPException, Request, Header
from sqlmodel import Session
from typing import Dict, Any

from app.db.session import get_session
from app.models.user import User
from app.core.security import get_current_user
from app.services.payment_service import payment_service
from app.api.v1.endpoints.schemas.payments import (
    CheckoutSessionRequest, 
    CheckoutSessionResponse,
    StripeConfigResponse
)

router = APIRouter()

@router.get("/config", response_model=StripeConfigResponse)
def get_stripe_config():
    """Retorna as configurações públicas do Stripe."""
    return StripeConfigResponse(
        public_key=os.getenv("STRIPE_PUBLIC_KEY", ""),
        pro_plan_price_id=os.getenv("STRIPE_PRO_PLAN_ID", "")
    )

@router.post("/create-checkout-session", response_model=CheckoutSessionResponse)
def create_checkout_session(
    request_data: CheckoutSessionRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Cria uma sessão de checkout para assinatura."""
    price_id = ""
    if request_data.plan_id == "pro":
        price_id = os.getenv("STRIPE_PRO_PLAN_ID")
    else:
        raise HTTPException(status_code=400, detail="Plano inválido.")

    if not price_id:
        raise HTTPException(status_code=500, detail="Configuração de preço não encontrada no servidor.")

    try:
        result = payment_service.create_checkout_session(
            user=current_user,
            price_id=price_id,
            success_url=request_data.success_url,
            cancel_url=request_data.cancel_url
        )
        return CheckoutSessionResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None),
    session: Session = Depends(get_session)
):
    """Endpoint para receber notificações de eventos do Stripe."""
    payload = await request.body()
    
    if not stripe_signature:
        raise HTTPException(status_code=400, detail="Faltando assinatura do Stripe")

    success = payment_service.handle_webhook(
        payload=payload,
        sig_header=stripe_signature,
        session_db=session
    )

    if not success:
        raise HTTPException(status_code=400, detail="Erro ao processar webhook")

    return {"status": "success"}
