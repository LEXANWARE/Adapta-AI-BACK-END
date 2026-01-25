from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from pydantic import BaseModel, EmailStr
from app.db.session import get_session
from app.core.security import create_access_token, verify_password, get_password_hash
from app.models.user import User

router = APIRouter()

# --- 1. DEFINIÇÃO DOS SCHEMAS (Isso estava faltando!) ---
class LoginRequest(BaseModel):
    username: str
    password: str

class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str

# --- 2. ROTA DE LOGIN (JSON) ---
@router.post("/login")
def login_access_token(
    login_data: LoginRequest,
    session: Session = Depends(get_session)
):
    # Busca usuário pelo username
    statement = select(User).where(User.username == login_data.username)
    user = session.exec(statement).first()

    # Valida senha
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Gera token
    access_token = create_access_token(subject=user.id)
    return {"access_token": access_token, "token_type": "bearer"}

# --- 3. ROTA DE REGISTRO (JSON) ---
@router.post("/register")
def register_user(
    register_data: RegisterRequest, 
    session: Session = Depends(get_session)
):
    # Verifica Username Duplicado
    if session.exec(select(User).where(User.username == register_data.username)).first():
        raise HTTPException(status_code=400, detail="Este usuário já existe.")

    # Verifica E-mail Duplicado
    if session.exec(select(User).where(User.email == register_data.email)).first():
        raise HTTPException(status_code=400, detail="Este e-mail já está cadastrado.")

    # Cria usuário
    user = User(
        username=register_data.username, 
        email=register_data.email, 
        hashed_password=get_password_hash(register_data.password)
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    
    return {"msg": "Usuário criado com sucesso", "id": user.id}