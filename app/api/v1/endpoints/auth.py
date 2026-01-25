from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm 

from sqlmodel import Session, select
from pydantic import BaseModel, EmailStr
from app.db.session import get_session
from app.core.security import create_access_token, verify_password, get_password_hash
from app.models.user import User

router = APIRouter()

class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str

@router.post("/login")
def login_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), 

    session: Session = Depends(get_session)
):

    statement = select(User).where(User.username == form_data.username)
    user = session.exec(statement).first()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(subject=user.id)
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/register")
def register_user(
    register_data: RegisterRequest, 
    session: Session = Depends(get_session)
):

    if session.exec(select(User).where(User.username == register_data.username)).first():
        raise HTTPException(status_code=400, detail="Este usuário já existe.")

    if session.exec(select(User).where(User.email == register_data.email)).first():
        raise HTTPException(status_code=400, detail="Este e-mail já está cadastrado.")

    user = User(
        username=register_data.username, 
        email=register_data.email, 
        hashed_password=get_password_hash(register_data.password)
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    return {"msg": "Usuário criado com sucesso", "id": user.id}