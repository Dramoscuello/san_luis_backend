import jwt
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.config import get_db
from app.models.user import User as UserModel
from typing import Annotated
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from app.schemas.user import Token
from app.services.auth import Auth




router = APIRouter(
    prefix='/auth',
    tags=['auth']
)



@router.post('/', status_code=200)
def login(user:Annotated[OAuth2PasswordRequestForm, Depends()], db: Session = Depends(get_db)):
    cedula = user.username
    usuario = db.query(UserModel).filter(UserModel.cedula == cedula).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="User not found")

    if usuario.password != user.password:
        raise HTTPException(status_code=403, detail="Incorrect password")

    if not usuario.activo:
        raise HTTPException(status_code=403, detail="User not active")

    access_token = Auth.create_access_token(data={"sub": usuario.cedula})
    return Token(access_token=access_token, token_type="bearer")


