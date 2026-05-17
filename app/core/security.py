import os
import re
import bcrypt
import jwt
from jwt import PyJWKClient
from sqlmodel import Session, select
from typing import Any, Union
from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.models.user import User
from app.db.session import get_session
from app.core.plans import check_permission
from app.core.supabase_profile import fetch_profile_plan

SECRET_KEY = "adaptaai"
LOCAL_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

SUPABASE_URL = os.getenv(
    "SUPABASE_URL",
    "https://gazidqznxtoaadrbsqfl.supabase.co",
)
JWKS_URL = f"{SUPABASE_URL}/auth/v1/.well-known/jwks.json"

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

def _unique_username(session: Session, email: str, supabase_id: str) -> str:
    base = re.sub(r"[^a-zA-Z0-9_]", "_", email.split("@")[0])[:40]
    candidate = base if len(base) >= 3 else f"user_{supabase_id[:8]}"
    if not session.exec(select(User).where(User.username == candidate)).first():
        return candidate
    suffix = supabase_id.replace("-", "")[:8]
    return f"{candidate[:42]}_{suffix}"


def _sync_plan_from_supabase(session: Session, user: User, supabase_id: str, token: str) -> User:
    plan = fetch_profile_plan(supabase_id, token)
    if plan and user.plan_type != plan:
        user.plan_type = plan
        session.add(user)
        session.commit()
        session.refresh(user)
    return user


def _get_or_create_supabase_user(
    session: Session,
    payload: dict,
    token: str,
) -> User:
    supabase_id = payload.get("sub")
    email = payload.get("email")
    if not supabase_id or not email:
        raise ValueError("Token Supabase sem sub ou email")

    user = session.exec(select(User).where(User.supabase_id == supabase_id)).first()
    if user is None:
        user = session.exec(select(User).where(User.email == email)).first()
        if user is not None:
            user.supabase_id = supabase_id
            session.add(user)
            session.commit()
            session.refresh(user)
        else:
            user = User(
                supabase_id=supabase_id,
                username=_unique_username(session, email, supabase_id),
                email=email,
                hashed_password="supabase_oauth",
                is_active=True,
                plan_type="free",
            )
            session.add(user)
            session.commit()
            session.refresh(user)

    return _sync_plan_from_supabase(session, user, supabase_id, token)


def _get_user_from_local_token(session: Session, token: str) -> User:
    payload = jwt.decode(token, SECRET_KEY, algorithms=[LOCAL_ALGORITHM])
    user_id = payload.get("sub")
    if user_id is None:
        raise ValueError("Token local sem sub")
    user = session.get(User, int(user_id))
    if user is None:
        raise ValueError("Usuário não encontrado")
    return user


def get_current_user(
    token: str = Depends(oauth2_scheme), 
    session: Session = Depends(get_session)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Não foi possível validar as credenciais",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        unverified_header = jwt.get_unverified_header(token)
        token_alg = unverified_header.get("alg")

        if token_alg == LOCAL_ALGORITHM:
            return _get_user_from_local_token(session, token)

        signing_key = jwks_client.get_signing_key_from_jwt(token)
        payload = jwt.decode(
            token, 
            signing_key.key, 
            algorithms=[token_alg],
            options={
                "verify_aud": False,
                "verify_iss": False
            }
        )
        return _get_or_create_supabase_user(session, payload, token)
        
    except HTTPException:
        raise
    except Exception:
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