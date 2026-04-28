from pydantic import BaseModel
from typing import Optional

class CheckoutSessionRequest(BaseModel):
    plan_id: str  # 'pro', 'premium', etc.
    success_url: str
    cancel_url: str

class CheckoutSessionResponse(BaseModel):
    checkout_url: str
    session_id: str

class StripeConfigResponse(BaseModel):
    public_key: str
    pro_plan_price_id: str
