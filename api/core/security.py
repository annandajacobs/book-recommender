from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
import bcrypt
from api.core.config import settings


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def create_acess_token(subject: str) -> str:
    """
    subject: o id ou email do usuário
    """
    expire=datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    playload = {"sub": str(subject), "exp": expire}
    encoded_jwt = jwt.encode(playload, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt

def decode_acess_token(token: str) -> str:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        return payload.get("sub")
    except JWTError:
        return None