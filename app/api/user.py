from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.config import get_db
from app.models.user import User as UserModel
from typing import Annotated

from app.schemas.user import User
from app.services.auth import Auth

router = APIRouter(
    prefix="/user",
    tags=["user"]
)

@router.post('/', status_code=200)
def create_user(current_user: Annotated[UserModel, Depends(Auth.get_current_user)], user: User, db: Session = Depends(get_db)):
    try:
        usuario = user.model_dump()
        usuario_new = UserModel(**usuario)
        db.add(usuario_new)
        db.commit()
        db.refresh(usuario_new)
        return {'mensaje': 'Usuario creado correctamente'}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))