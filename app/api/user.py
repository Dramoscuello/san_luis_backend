from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from app.database.config import get_db
from app.models.user import User as UserModel
from typing import Annotated

from app.schemas.user import User, UserResponse, UserUpdate, ChangePassword
from app.services.auth import Auth

router = APIRouter(
    prefix="/user",
    tags=["user"]
)

@router.post('/', status_code=200)
def create_user(current_user: Annotated[UserModel, Depends(Auth.get_current_user)], user: User, db: Session = Depends(get_db)):
    try:
        # Validar que si es docente tenga sede asignada
        if user.rol == "docente" and not user.sede_id:
            raise HTTPException(status_code=400, detail="El docente debe tener una sede asignada")
            
        usuario = user.model_dump()
        usuario_new = UserModel(**usuario)
        db.add(usuario_new)
        db.commit()
        db.refresh(usuario_new)
        del usuario_new.password
        del usuario_new.created_at
        del usuario_new.updated_at
        return usuario_new
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
    usuarios = db.query(UserModel).options(joinedload(UserModel.asignaturas)).filter(UserModel.id != current_user.id).all()

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
            "sede_nombre": usuario.sede.nombre if usuario.sede else None,
            "asignaturas": [
                {"id": asig.id, "nombre": asig.nombre} 
                for asig in usuario.asignaturas
            ]
        }
        for usuario in usuarios
    ]
    return resultado


@router.post("/change-password", status_code=200)
def change_password(
    current_user: Annotated[UserModel, Depends(Auth.get_current_user)],
    passwords: ChangePassword,
    db: Session = Depends(get_db),
):
    """
    Cambiar contraseña del usuario autenticado.
    Requiere la contraseña actual para validar.
    """
    # Verificar que la contraseña actual sea correcta
    if current_user.password != passwords.password_actual:
        raise HTTPException(
            status_code=400,
            detail="La contraseña actual es incorrecta"
        )

    # Verificar que la nueva contraseña sea diferente
    if passwords.password_actual == passwords.password_nuevo:
        raise HTTPException(
            status_code=400,
            detail="La nueva contraseña debe ser diferente a la actual"
        )

    # Actualizar contraseña
    current_user.password = passwords.password_nuevo
    db.commit()

    return {'mensaje': 'Contraseña actualizada correctamente'}


@router.patch("/{id}", status_code=200)
def update_user(current_user: Annotated[UserModel, Depends(Auth.get_current_user)], id: int, user:UserUpdate, db: Session = Depends(get_db)):
    user_db = db.query(UserModel).filter(UserModel.id == id).first()
    if not user_db:
        raise HTTPException(status_code=404, detail="User not found")
        
    datos = user.model_dump(exclude_unset=True)
    
    # Validaciones de cambio de rol
    nuevo_rol = datos.get('rol', user_db.rol)
    nueva_sede_id = datos.get('sede_id', user_db.sede_id)
    
    if nuevo_rol == 'docente' and not nueva_sede_id:
        raise HTTPException(
            status_code=400, 
            detail="No se puede asignar rol de docente sin una sede. Por favor asigne una sede."
        )
    
    for key, value in datos.items():
        setattr(user_db, key, value)
        
    db.commit()
    return {'mensaje': 'Usuario actualizado correctamente'}


@router.delete("/{id}", status_code=200)
def delete_user(current_user: Annotated[UserModel, Depends(Auth.get_current_user)], id: int, db: Session = Depends(get_db)):
    usuario = db.query(UserModel).filter(UserModel.id == id)
    if not usuario.first():
        raise HTTPException(status_code=404, detail="User not found")
    usuario.delete(synchronize_session=False)
    db.commit()
    return {'mensaje': 'Usuario eliminado correctamente'}
