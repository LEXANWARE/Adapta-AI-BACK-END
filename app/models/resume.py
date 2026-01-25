from typing import Optional, Dict
from sqlmodel import SQLModel, Field
from datetime import datetime
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSON

STRICT_CONFIG = {"extra": "forbid"}

class Resume(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    raw_text: str = Field(sa_column_kwargs={"nullable": False})
    # Usamos o tipo JSON do SQLAlchemy para garantir compatibilidade com Postgres/SQLite
    parsed_data: Dict = Field(default={}, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)