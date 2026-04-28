from typing import Optional
from sqlmodel import Field, SQLModel

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True, min_length=3, max_length=50)
    email: str = Field(index=True, unique=True)
    hashed_password: str
    is_active: bool = Field(default=True)
    
    # Campos para Pagamento/Stripe
    stripe_customer_id: Optional[str] = Field(default=None, index=True)
    subscription_id: Optional[str] = Field(default=None)
    plan_type: str = Field(default="free")  # 'free', 'pro', 'premium'
    subscription_status: Optional[str] = Field(default=None) # 'active', 'canceled', 'past_due'
