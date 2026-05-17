from sqlalchemy import inspect, text
from sqlmodel import SQLModel
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db.session import engine
from app.api.v1.endpoints import auth, resumes, payments
from app.models.user import User
from app.models.resume import Resume

def _migrate_user_supabase_id():
  inspector = inspect(engine)
  if "user" not in inspector.get_table_names():
    return
  columns = {col["name"] for col in inspector.get_columns("user")}
  if "supabase_id" not in columns:
    with engine.begin() as conn:
      conn.execute(text("ALTER TABLE user ADD COLUMN supabase_id VARCHAR"))

# Cria as tabelas
def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
    _migrate_user_supabase_id()

# Lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield

# App
app = FastAPI(
    title="AdaptaAi API",
    description="API para otimização de currículos com análise ATS e Quality",
    version="1.0.0",
    lifespan=lifespan
)

# 🔥 CORS CORRETO
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://adapta-ai-curriculo.lovable.app"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],   # MUITO IMPORTANTE
    allow_headers=["*"],   # MUITO IMPORTANTE
)

# Rotas
app.include_router(auth.router, prefix="/api/v1")
app.include_router(
    resumes.router,
    prefix="/api/v1/resumes",
    tags=["currículos"]
)
app.include_router(
    payments.router,
    prefix="/api/v1/payments",
    tags=["pagamentos"]
)

# Health check
@app.get("/")
def read_root():
    return {"message": "AdaptaAi Backend Online 🚀"}