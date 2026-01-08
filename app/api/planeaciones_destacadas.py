from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from app.database.config import get_db
from typing import Annotated, List, Optional
from app.models.user import User as UserModel
from app.models.planeaciones import Planeacion as PlaneacionModel
from app.models.planeaciones_destacadas import PlaneacionDestacada as PlaneacionDestacadaModel
from app.schemas.planeaciones_destacadas import (
    PlaneacionDestacadaCreate,
    PlaneacionDestacadaUpdate,
    PlaneacionDestacadaResponse,
    PlaneacionDestacadaConDetalle,
)
from app.services.auth import Auth


router = APIRouter(
    prefix="/planeaciones-destacadas",
    tags=["planeaciones-destacadas"],
)

# Roles permitidos para destacar/gestionar planeaciones
ROLES_PERMITIDOS = ["coordinador", "rector"]


@router.get("/", response_model=List[PlaneacionDestacadaConDetalle])
def listar_planeaciones_destacadas(
    current_user: Annotated[UserModel, Depends(Auth.get_current_user)],
    db: Session = Depends(get_db),
    solo_activas: bool = Query(True, description="Mostrar solo planeaciones destacadas activas"),
):
    """
    Listar planeaciones destacadas (banco de mejores prácticas).

    Visible para TODOS los usuarios autenticados.
    Ordenadas por visualizaciones (más populares primero).
    """
    query = (
        db.query(PlaneacionDestacadaModel)
        .options(
            joinedload(PlaneacionDestacadaModel.coordinador),
            joinedload(PlaneacionDestacadaModel.planeacion)
            .joinedload(PlaneacionModel.docente),
            joinedload(PlaneacionDestacadaModel.planeacion)
            .joinedload(PlaneacionModel.asignatura),
            joinedload(PlaneacionDestacadaModel.planeacion)
            .joinedload(PlaneacionModel.sede),
        )
    )

    if solo_activas:
        query = query.filter(PlaneacionDestacadaModel.activa == True)

    destacadas = query.order_by(PlaneacionDestacadaModel.fecha_destacado.desc()).all()

    # Transformar a schema con detalle
    resultado = []
    for destacada in destacadas:
        detalle = PlaneacionDestacadaConDetalle(
            id=destacada.id,
            planeacion_id=destacada.planeacion_id,
            coordinador_id=destacada.coordinador_id,
            razon=destacada.razon,
            activa=destacada.activa,
            visualizaciones=destacada.visualizaciones,
            fecha_destacado=destacada.fecha_destacado,
            created_at=destacada.created_at,
            coordinador=destacada.coordinador,
            planeacion_titulo=destacada.planeacion.titulo if destacada.planeacion else None,
            planeacion_archivo=destacada.planeacion.nombre_archivo_original if destacada.planeacion else None,
            planeacion_drive_view_link=destacada.planeacion.drive_view_link if destacada.planeacion else None,
            docente_nombre=destacada.planeacion.docente.nombre_completo if destacada.planeacion and destacada.planeacion.docente else None,
            asignatura_nombre=destacada.planeacion.asignatura.nombre if destacada.planeacion and destacada.planeacion.asignatura else None,
            sede_nombre=destacada.planeacion.sede.nombre if destacada.planeacion and destacada.planeacion.sede else None,
        )
        resultado.append(detalle)

    return resultado


@router.post("/", response_model=PlaneacionDestacadaResponse, status_code=status.HTTP_201_CREATED)
def destacar_planeacion(
    destacada_data: PlaneacionDestacadaCreate,
    current_user: Annotated[UserModel, Depends(Auth.get_current_user)],
    db: Session = Depends(get_db),
):
    """
    Destacar una planeación como referente institucional.

    - **planeacion_id**: ID de la planeación a destacar
    - **razon**: Razón por la cual se destaca (mínimo 20 caracteres)

    Solo coordinadores y rector pueden destacar planeaciones.
    Una planeación solo puede ser destacada una vez.
    """
    # Validar rol
    if current_user.rol not in ROLES_PERMITIDOS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo coordinadores y rector pueden destacar planeaciones",
        )

    # Verificar que la planeación existe
    planeacion = db.query(PlaneacionModel).filter(
        PlaneacionModel.id == destacada_data.planeacion_id
    ).first()

    if not planeacion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Planeación no encontrada",
        )

    # Verificar que no esté ya destacada
    existente = db.query(PlaneacionDestacadaModel).filter(
        PlaneacionDestacadaModel.planeacion_id == destacada_data.planeacion_id
    ).first()

    if existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Esta planeación ya está destacada",
        )

    # Crear la planeación destacada
    nueva_destacada = PlaneacionDestacadaModel(
        planeacion_id=destacada_data.planeacion_id,
        coordinador_id=current_user.id,
        razon=destacada_data.razon,
    )

    db.add(nueva_destacada)
    db.commit()
    db.refresh(nueva_destacada)

    # Cargar relación del coordinador
    db.refresh(nueva_destacada, ["coordinador"])

    return nueva_destacada


@router.patch("/{destacada_id}", response_model=PlaneacionDestacadaResponse)
def actualizar_planeacion_destacada(
    destacada_id: int,
    destacada_data: PlaneacionDestacadaUpdate,
    current_user: Annotated[UserModel, Depends(Auth.get_current_user)],
    db: Session = Depends(get_db),
):
    """
    Actualizar una planeación destacada.

    - **razon**: Nueva razón (opcional)
    - **activa**: Activar/desactivar (opcional)

    Solo el coordinador que destacó o el rector pueden actualizar.
    """
    destacada_db = (
        db.query(PlaneacionDestacadaModel)
        .filter(PlaneacionDestacadaModel.id == destacada_id)
        .first()
    )

    if not destacada_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Planeación destacada no encontrada",
        )

    # Validar permisos
    es_autor = destacada_db.coordinador_id == current_user.id
    es_rector = current_user.rol == "rector"

    if not es_autor and not es_rector:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para actualizar esta planeación destacada",
        )

    # Actualizar campos
    if destacada_data.razon is not None:
        destacada_db.razon = destacada_data.razon

    if destacada_data.activa is not None:
        destacada_db.activa = destacada_data.activa

    db.commit()
    db.refresh(destacada_db, ["coordinador"])

    return destacada_db


@router.patch("/{destacada_id}/visualizaciones", response_model=PlaneacionDestacadaResponse)
def incrementar_visualizaciones(
    destacada_id: int,
    current_user: Annotated[UserModel, Depends(Auth.get_current_user)],
    db: Session = Depends(get_db),
):
    """
    Incrementar el número de visualizaciones de una planeación destacada.

    Incrementa +1 las visualizaciones automáticamente.
    Cualquier usuario autenticado puede incrementar las visualizaciones.
    """
    destacada_db = (
        db.query(PlaneacionDestacadaModel)
        .filter(PlaneacionDestacadaModel.id == destacada_id)
        .first()
    )

    if not destacada_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Planeación destacada no encontrada",
        )

    # Incrementar visualizaciones en +1
    destacada_db.visualizaciones += 1

    db.commit()
    db.refresh(destacada_db, ["coordinador"])

    return destacada_db


@router.delete("/{destacada_id}")
def eliminar_planeacion_destacada(
    destacada_id: int,
    current_user: Annotated[UserModel, Depends(Auth.get_current_user)],
    db: Session = Depends(get_db),
):
    """
    Eliminar una planeación destacada (quitar del banco de mejores prácticas).

    NO elimina la planeación original, solo la quita de destacadas.

    - El coordinador que destacó puede eliminarla
    - El rector puede eliminar cualquiera
    """
    destacada_db = (
        db.query(PlaneacionDestacadaModel)
        .filter(PlaneacionDestacadaModel.id == destacada_id)
        .first()
    )

    if not destacada_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Planeación destacada no encontrada",
        )

    # Validar permisos
    es_autor = destacada_db.coordinador_id == current_user.id
    es_rector = current_user.rol == "rector"

    if not es_autor and not es_rector:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para eliminar esta planeación destacada",
        )

    db.delete(destacada_db)
    db.commit()

    return {"mensaje": "Planeación eliminada del banco de mejores prácticas"}
