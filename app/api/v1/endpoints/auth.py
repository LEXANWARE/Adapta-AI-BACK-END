from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select
from app.db.session import get_session
from app.core.security import create_access_token, verify_password, get_password_hash
from app.models.user import User

router = APIRouter()

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
def register_user(username: str, password: str, email: str, session: Session = Depends(get_session)):
    user = User(
        username=username, 
        email=email, 
        hashed_password=get_password_hash(password)
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return {"msg": "Usuário criado com sucesso", "id": user.id}