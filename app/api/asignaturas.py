from typing import List, Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload

from app.database.config import get_db
from app.models.asignaturas import Asignatura as AsignaturaModel
from app.models.docente_asignaturas import DocenteAsignatura
from app.models.areas import Area as AreaModel
from app.models.user import User as UserModel
from app.schemas.asignaturas import (
    AsignaturaCreate,
    AsignaturaUpdate,
    AsignaturaResponse,
    AsignarDocenteRequest
)
from app.services.auth import Auth

router = APIRouter(
    prefix="/asignaturas",
    tags=["asignaturas"],
)

# Roles administrativos permitidos
ROLES_ADMIN = ["coordinador", "rector"]


@router.get("/", response_model=List[AsignaturaResponse])
def listar_asignaturas(
    current_user: Annotated[UserModel, Depends(Auth.get_current_user)],
    db: Session = Depends(get_db),
    area_id: Optional[int] = Query(None, description="Filtrar por ID de área"),
    activa: Optional[bool] = Query(True, description="Filtrar por estado activo"),
):
    """
    Listar todas las asignaturas.
    - Se puede filtrar por área.
    - Por defecto solo trae las activas.
    """
    query = db.query(AsignaturaModel).options(joinedload(AsignaturaModel.area))

    if area_id:
        query = query.filter(AsignaturaModel.area_id == area_id)
    
    if activa is not None:
        query = query.filter(AsignaturaModel.activa == activa)

    return query.order_by(AsignaturaModel.nombre).all()


@router.get("/{asignatura_id}", response_model=AsignaturaResponse)
def obtener_asignatura(
    asignatura_id: int,
    current_user: Annotated[UserModel, Depends(Auth.get_current_user)],
    db: Session = Depends(get_db),
):
    """
    Obtener detalle de una asignatura por su ID.
    """
    asignatura = (
        db.query(AsignaturaModel)
        .options(joinedload(AsignaturaModel.area))
        .filter(AsignaturaModel.id == asignatura_id)
        .first()
    )

    if not asignatura:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asignatura no encontrada"
        )

    return asignatura


@router.post("/", response_model=AsignaturaResponse, status_code=status.HTTP_201_CREATED)
def crear_asignatura(
    asignatura: AsignaturaCreate,
    current_user: Annotated[UserModel, Depends(Auth.get_current_user)],
    db: Session = Depends(get_db),
):
    """
    Crear una nueva asignatura.
    Solo coordinadores y rector.
    """
    if current_user.rol not in ROLES_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para realizar esta acción"
        )

    # Validar que el área exista
    area = db.query(AreaModel).filter(AreaModel.id == asignatura.area_id).first()
    if not area:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"El área con id {asignatura.area_id} no existe"
        )

    # Verificar nombre duplicado en la misma área
    existe = db.query(AsignaturaModel).filter(
        AsignaturaModel.nombre == asignatura.nombre,
        AsignaturaModel.area_id == asignatura.area_id
    ).first()
    
    if existe:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe una asignatura con este nombre en esta área"
        )

    nueva_asignatura = AsignaturaModel(**asignatura.model_dump())
    db.add(nueva_asignatura)
    db.commit()
    db.refresh(nueva_asignatura)
    
    # Cargar relación
    db.refresh(nueva_asignatura, ["area"])

    return nueva_asignatura


@router.patch("/{asignatura_id}", response_model=AsignaturaResponse)
def actualizar_asignatura(
    asignatura_id: int,
    asignatura_update: AsignaturaUpdate,
    current_user: Annotated[UserModel, Depends(Auth.get_current_user)],
    db: Session = Depends(get_db),
):
    """
    Actualizar una asignatura.
    Solo coordinadores y rector.
    """
    if current_user.rol not in ROLES_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para realizar esta acción"
        )

    asignatura_db = db.query(AsignaturaModel).filter(AsignaturaModel.id == asignatura_id).first()
    if not asignatura_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asignatura no encontrada"
        )

    datos = asignatura_update.model_dump(exclude_unset=True)
    
    # Si cambia el nombre o área, verificar duplicados
    nuevo_nombre = datos.get('nombre', asignatura_db.nombre)
    nueva_area_id = datos.get('area_id', asignatura_db.area_id)
    
    if 'nombre' in datos or 'area_id' in datos:
        existe = db.query(AsignaturaModel).filter(
            AsignaturaModel.nombre == nuevo_nombre,
            AsignaturaModel.area_id == nueva_area_id,
            AsignaturaModel.id != asignatura_id
        ).first()
        
        if existe:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya existe otra asignatura con este nombre en esta área"
            )

    for key, value in datos.items():
        setattr(asignatura_db, key, value)

    db.commit()
    db.refresh(asignatura_db)
    
    # Cargar relación si es necesario (generalmente update no cambia la instancia en sesión, pero por si acaso)
    # db.refresh(asignatura_db, ["area"]) 

    return asignatura_db


@router.delete("/{asignatura_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_asignatura(
    asignatura_id: int,
    current_user: Annotated[UserModel, Depends(Auth.get_current_user)],
    db: Session = Depends(get_db),
):
    """
    Eliminar una asignatura.
    Solo coordinadores y rector.
    """
    if current_user.rol not in ROLES_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para realizar esta acción"
        )

    asignatura_db = db.query(AsignaturaModel).filter(AsignaturaModel.id == asignatura_id).first()
    if not asignatura_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asignatura no encontrada"
        )

    db.delete(asignatura_db)
    db.commit()
    
    return None


@router.post("/{asignatura_id}/docentes", status_code=status.HTTP_201_CREATED)
def asignar_docente(
    asignatura_id: int,
    asignacion: AsignarDocenteRequest,
    current_user: Annotated[UserModel, Depends(Auth.get_current_user)],
    db: Session = Depends(get_db),
):
    """
    Asignar un docente a una asignatura.
    Solo coordinadores y rector.
    """
    if current_user.rol not in ROLES_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para realizar esta acción"
        )

    # 1. Verificar Asignatura
    asignatura = db.query(AsignaturaModel).filter(AsignaturaModel.id == asignatura_id).first()
    if not asignatura:
        raise HTTPException(status_code=404, detail="Asignatura no encontrada")

    # 2. Verificar Docente
    docente = db.query(UserModel).filter(UserModel.id == asignacion.docente_id).first()
    if not docente:
        raise HTTPException(status_code=404, detail="Docente no encontrado")
    
    if docente.rol != 'docente':
        raise HTTPException(status_code=400, detail="El usuario seleccionado no es un docente")

    # 3. Verificar si ya está asignado
    existe = db.query(DocenteAsignatura).filter(
        DocenteAsignatura.asignatura_id == asignatura_id,
        DocenteAsignatura.docente_id == asignacion.docente_id
    ).first()

    if existe:
        raise HTTPException(status_code=400, detail="El docente ya está asignado a esta asignatura")

    # 4. Asignar
    nueva_asignacion = DocenteAsignatura(
        asignatura_id=asignatura_id,
        docente_id=asignacion.docente_id
    )
    db.add(nueva_asignacion)
    db.commit()

    return {"msg": "Docente asignado correctamente"}


@router.delete("/{asignatura_id}/docentes/{docente_id}", status_code=status.HTTP_204_NO_CONTENT)
def desasignar_docente(
    asignatura_id: int,
    docente_id: int,
    current_user: Annotated[UserModel, Depends(Auth.get_current_user)],
    db: Session = Depends(get_db),
):
    """
    Quitar un docente de una asignatura.
    Solo coordinadores y rector.
    """
    if current_user.rol not in ROLES_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para realizar esta acción"
        )

    asignacion = db.query(DocenteAsignatura).filter(
        DocenteAsignatura.asignatura_id == asignatura_id,
        DocenteAsignatura.docente_id == docente_id
    ).first()

    if not asignacion:
        raise HTTPException(status_code=404, detail="La asignación no existe")

    db.delete(asignacion)
    db.commit()

    return None
