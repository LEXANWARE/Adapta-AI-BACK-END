from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel
from app.db.session import engine
from app.api.v1.endpoints import auth

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

app = FastAPI(title="AdaptaAi API")

origins = [
    "http://localhost:5173", 
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1")

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

@app.get("/")
def read_root():
    return {"message": "AdaptaAi Backend Online 🚀"}