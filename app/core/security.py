import bcrypt
import jwt
from jwt import PyJWKClient
from sqlmodel import Session
from typing import Any, Union
from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.models.user import User
from app.db.session import get_session
from app.core.plans import check_permission

SECRET_KEY = "adaptaai"
LOCAL_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

SUPABASE_URL = "https://gazidqznxtoaadrbsqfl.supabase.co"
JWKS_URL = f"{SUPABASE_URL}/auth/v1/.well-known/jwks.json"
SUPABASE_ALGORITHM = "RS256"

jwks_client = PyJWKClient(JWKS_URL)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/login")

def create_access_token(subject: Union[str, Any], expires_delta: timedelta = None) -> str:
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=LOCAL_ALGORITHM)
    return encoded_jwt

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def get_current_user(
    token: str = Depends(oauth2_scheme), 
    session: Session = Depends(get_session)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Não foi possível validar as credenciais",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    print(f"--- INICIANDO VALIDAÇÃO DO TOKEN ---")
    
    try:
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        print(f"Chave de assinatura obtida com sucesso.")
        
        payload = jwt.decode(
            token, 
            signing_key.key, 
            algorithms=[SUPABASE_ALGORITHM],
            options={
                "verify_aud": False,
                "verify_iss": False
            }
        )
        print(f"Token decodificado com sucesso. Payload: {payload}")
        
        supabase_user_id = payload.get("sub")
        if supabase_user_id is None:
            print("Erro: O token não possui o campo 'sub' (User ID).")
            raise credentials_exception
            
        user = session.get(User, 1)
        if user is None:
            print("Criando usuário de fallback ID 1.")
            user = User(
                id=1,
                username="usuario_sistema",
                email=payload.get("email", "usuario@exemplo.com"),
                hashed_password="...",
                is_active=True,
                plan_type="free"
            )
            session.add(user)
            session.commit()
            session.refresh(user)
            
        print("Usuário validado e retornado com sucesso.")
        return user
        
    except Exception as e:
        print(f"!!! ERRO FATAL NA VALIDAÇÃO DO TOKEN: {str(e)} !!!")
        raise credentials_exception

def plan_required(permission: str):
    def dependency(current_user: User = Depends(get_current_user)):
        if not check_permission(current_user.plan_type, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Seu plano não permite esta ação"
            )
        return current_user
    return dependency