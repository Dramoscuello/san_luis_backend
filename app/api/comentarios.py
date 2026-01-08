from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from app.database.config import get_db
from typing import Annotated, List, Optional
from app.models.user import User as UserModel
from app.models.planeaciones import Planeacion as PlaneacionModel
from app.models.comentarios import Comentario as ComentarioModel
from app.schemas.comentarios import (
    ComentarioCreate,
    ComentarioUpdate,
    ComentarioResponse,
)
from app.services.auth import Auth


router = APIRouter(
    prefix="/comentarios",
    tags=["comentarios"],
)

# Roles permitidos para crear/editar comentarios
ROLES_PERMITIDOS = ["coordinador", "rector"]


@router.get("/", response_model=List[ComentarioResponse])
def listar_comentarios(
    current_user: Annotated[UserModel, Depends(Auth.get_current_user)],
    db: Session = Depends(get_db),
    planeacion_id: Optional[int] = Query(None, description="Filtrar por planeación"),
    coordinador_id: Optional[int] = Query(None, description="Filtrar por coordinador"),
):
    """
    Listar comentarios con filtros opcionales.

    - **Docentes:** Solo ven comentarios de sus propias planeaciones
    - **Coordinadores/Rector:** Ven todos los comentarios

    Filtros: planeacion_id, coordinador_id
    """
    query = (
        db.query(ComentarioModel)
        .options(joinedload(ComentarioModel.coordinador))
    )

    # Si es docente, solo ver comentarios de sus planeaciones
    if current_user.rol == "docente":
        query = query.join(PlaneacionModel).filter(
            PlaneacionModel.docente_id == current_user.id
        )

    # Aplicar filtros
    if planeacion_id:
        query = query.filter(ComentarioModel.planeacion_id == planeacion_id)
    if coordinador_id:
        query = query.filter(ComentarioModel.coordinador_id == coordinador_id)

    comentarios = query.order_by(ComentarioModel.created_at.desc()).all()
    return comentarios


@router.get("/planeacion/{planeacion_id}", response_model=List[ComentarioResponse])
def listar_comentarios_planeacion(
    planeacion_id: int,
    current_user: Annotated[UserModel, Depends(Auth.get_current_user)],
    db: Session = Depends(get_db),
):
    """
    Listar todos los comentarios de una planeación específica.
    Todos los usuarios autenticados pueden ver los comentarios.
    """
    # Verificar que la planeación existe
    planeacion = db.query(PlaneacionModel).filter(PlaneacionModel.id == planeacion_id).first()
    if not planeacion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Planeación no encontrada",
        )

    comentarios = (
        db.query(ComentarioModel)
        .options(joinedload(ComentarioModel.coordinador))
        .filter(ComentarioModel.planeacion_id == planeacion_id)
        .order_by(ComentarioModel.created_at.desc())
        .all()
    )

    return comentarios


@router.get("/{comentario_id}", response_model=ComentarioResponse)
def obtener_comentario(
    comentario_id: int,
    current_user: Annotated[UserModel, Depends(Auth.get_current_user)],
    db: Session = Depends(get_db),
):
    """
    Obtener un comentario por ID.
    """
    comentario = (
        db.query(ComentarioModel)
        .options(joinedload(ComentarioModel.coordinador))
        .filter(ComentarioModel.id == comentario_id)
        .first()
    )

    if not comentario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comentario no encontrado",
        )

    return comentario


@router.post("/", response_model=ComentarioResponse, status_code=status.HTTP_201_CREATED)
def crear_comentario(
    comentario_data: ComentarioCreate,
    current_user: Annotated[UserModel, Depends(Auth.get_current_user)],
    db: Session = Depends(get_db),
):
    """
    Crear un nuevo comentario sobre una planeación.

    - **planeacion_id**: ID de la planeación a comentar
    - **contenido**: Texto del comentario (mínimo 10 caracteres)

    Solo coordinadores y rector pueden crear comentarios.
    """
    # Validar rol
    if current_user.rol not in ROLES_PERMITIDOS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo coordinadores y rector pueden crear comentarios",
        )

    # Verificar que la planeación existe
    planeacion = db.query(PlaneacionModel).filter(
        PlaneacionModel.id == comentario_data.planeacion_id
    ).first()

    if not planeacion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Planeación no encontrada",
        )

    # Crear el comentario
    nuevo_comentario = ComentarioModel(
        planeacion_id=comentario_data.planeacion_id,
        coordinador_id=current_user.id,
        contenido=comentario_data.contenido,
    )

    db.add(nuevo_comentario)
    db.commit()
    db.refresh(nuevo_comentario)

    # Cargar relación del coordinador para la respuesta
    db.refresh(nuevo_comentario, ["coordinador"])

    return nuevo_comentario


@router.patch("/{comentario_id}", response_model=ComentarioResponse)
def actualizar_comentario(
    comentario_id: int,
    comentario_data: ComentarioUpdate,
    current_user: Annotated[UserModel, Depends(Auth.get_current_user)],
    db: Session = Depends(get_db),
):
    """
    Actualizar un comentario existente.

    Solo el coordinador que creó el comentario puede actualizarlo.
    """
    comentario_db = (
        db.query(ComentarioModel)
        .filter(ComentarioModel.id == comentario_id)
        .first()
    )

    if not comentario_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comentario no encontrado",
        )

    # Validar que el usuario sea el autor del comentario
    if comentario_db.coordinador_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo el autor puede actualizar este comentario",
        )

    comentario_db.contenido = comentario_data.contenido

    db.commit()
    db.refresh(comentario_db, ["coordinador"])

    return comentario_db


@router.delete("/{comentario_id}")
def eliminar_comentario(
    comentario_id: int,
    current_user: Annotated[UserModel, Depends(Auth.get_current_user)],
    db: Session = Depends(get_db),
):
    """
    Eliminar un comentario.

    - El coordinador autor puede eliminar su propio comentario
    - El rector puede eliminar cualquier comentario
    """
    comentario_db = (
        db.query(ComentarioModel)
        .filter(ComentarioModel.id == comentario_id)
        .first()
    )

    if not comentario_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comentario no encontrado",
        )

    # Validar permisos
    es_autor = comentario_db.coordinador_id == current_user.id
    es_rector = current_user.rol == "rector"

    if not es_autor and not es_rector:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para eliminar este comentario",
        )

    db.delete(comentario_db)
    db.commit()

    return {"mensaje": "Comentario eliminado correctamente"}
