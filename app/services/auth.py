import os
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Annotated
import jwt
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt import InvalidTokenError
from app.schemas.user import TokenData

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='auth')
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

class Auth:
    SECRET_KEY = os.getenv('SECRET_KEY')
    ALGORITHM = os.getenv('ALGORITHM')
    ACCESS_TOKEN_EXPIRE_MINUTES = float(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES'))

    @classmethod
    def create_access_token(cls, data: dict):
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + timedelta(minutes=cls.ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, cls.SECRET_KEY, algorithm=cls.ALGORITHM)
        return encoded_jwt


    @classmethod
    async def get_current_user(cls, token: Annotated[str, Depends(oauth2_scheme)]):
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

        try:
            payload = jwt.decode(token, cls.SECRET_KEY, algorithms=[cls.ALGORITHM])
            cedula = payload.get("sub")
            if cedula is None:
                raise credentials_exception
            token_data = TokenData(cedula=cedula)
        except InvalidTokenError:
            raise credentials_exception