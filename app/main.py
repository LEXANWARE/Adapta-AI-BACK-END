from sqlmodel import SQLModel
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db.session import engine
from app.api.v1.endpoints import auth, resumes, payments

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield

app = FastAPI(
    title="AdaptaAi API",
    description="API para otimização de currículos com análise ATS e Quality",
    version="1.0.0",
    lifespan=lifespan
)

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

@app.get("/")
def read_root():
    return {"message": "AdaptaAi Backend Online 🚀"}