from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.config import get_db
from app.models.user import User as UserModel
from typing import Annotated

from app.schemas.user import User, UserResponse, UserUpdate
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

@router.get('/whoami/{username}', status_code=200, response_model=UserResponse)
def read_user(current_user: Annotated[UserModel, Depends(Auth.get_current_user)],username: str, db: Session = Depends(get_db)):
    user = db.query(UserModel).filter(UserModel.cedula == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get("/all")
def get_usuarios(current_user: Annotated[UserModel, Depends(Auth.get_current_user)], db: Session = Depends(get_db)):
    usuarios = db.query(UserModel).filter(UserModel.rol == "docente").all()

    resultado = [
        {
            "id": usuario.id,
            "nombre_completo": usuario.nombre_completo,
            "email": usuario.email,
            "cedula":usuario.cedula,
            "rol":usuario.rol,
            "telefono":usuario.telefono,
            "activo":usuario.activo,
            "sede_id":usuario.sede_id,
            "sede_nombre": usuario.sede.nombre if usuario.sede else None
        }
        for usuario in usuarios
    ]
    return resultado

@router.patch("/{id}", status_code=200)
def update_user(current_user: Annotated[UserModel, Depends(Auth.get_current_user)], id: int, user:UserUpdate, db: Session = Depends(get_db)):
    user_update = db.query(UserModel).filter(UserModel.id == id)
    if not user_update.first():
        raise HTTPException(status_code=404, detail="User not found")
    user_update.update(user.model_dump(exclude_unset=True))
    db.commit()
    return {'mensaje': 'Usuario actualizado correctamente'}