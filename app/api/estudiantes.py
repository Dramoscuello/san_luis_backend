from typing import List, Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload

from app.database.config import get_db
from app.models.estudiantes import Estudiante as EstudianteModel
from app.models.grupos import Grupo as GrupoModel
from app.models.user import User as UserModel
from app.schemas.estudiantes import (
    EstudianteCreate,
    EstudianteUpdate,
    EstudianteResponse
)
from app.services.auth import Auth

router = APIRouter(
    prefix="/estudiantes",
    tags=["estudiantes"],
)

ROLES_ADMIN = ["coordinador", "rector"]


@router.get("/", response_model=List[EstudianteResponse])
def listar_estudiantes(
    current_user: Annotated[UserModel, Depends(Auth.get_current_user)],
    db: Session = Depends(get_db),
    grupo_id: Optional[int] = Query(None, description="Filtrar por ID de grupo"),
):
    """
    Listar estudiantes.
    Puede filtrar por grupo.
    """
    query = db.query(EstudianteModel).options(joinedload(EstudianteModel.grupo))

    if grupo_id:
        query = query.filter(EstudianteModel.grupo_id == grupo_id)

    return query.order_by(EstudianteModel.apellidos, EstudianteModel.nombres).all()


@router.get("/{estudiante_id}", response_model=EstudianteResponse)
def obtener_estudiante(
    estudiante_id: int,
    current_user: Annotated[UserModel, Depends(Auth.get_current_user)],
    db: Session = Depends(get_db),
):
    """
    Obtener un estudiante por ID.
    """
    estudiante = (
        db.query(EstudianteModel)
        .options(joinedload(EstudianteModel.grupo))
        .filter(EstudianteModel.id == estudiante_id)
        .first()
    )

    if not estudiante:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")

    return estudiante


@router.post("/", response_model=EstudianteResponse, status_code=status.HTTP_201_CREATED)
def crear_estudiante(
    estudiante: EstudianteCreate,
    current_user: Annotated[UserModel, Depends(Auth.get_current_user)],
    db: Session = Depends(get_db),
):
    """
    Crear un nuevo estudiante.
    Solo docentes directores de grupo, coordinadores y rector.
    """
    # Validar Grupo
    grupo = db.query(GrupoModel).filter(GrupoModel.id == estudiante.grupo_id).first()
    if not grupo:
        raise HTTPException(status_code=404, detail=f"Grupo {estudiante.grupo_id} no encontrado")

    # Verificar permisos: debe ser admin o director del grupo
    es_admin = current_user.rol in ROLES_ADMIN
    es_director = any(g.id == estudiante.grupo_id for g in current_user.grupos_a_cargo)
    
    if not es_admin and not es_director:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para agregar estudiantes a este grupo"
        )

    # Validar duplicado (documento en mismo grupo)
    existe = db.query(EstudianteModel).filter(
        EstudianteModel.grupo_id == estudiante.grupo_id,
        EstudianteModel.numero_documento == estudiante.numero_documento
    ).first()
    
    if existe:
        raise HTTPException(status_code=400, detail="Ya existe un estudiante con ese documento en el grupo")

    nuevo_estudiante = EstudianteModel(**estudiante.model_dump())
    db.add(nuevo_estudiante)
    db.commit()
    db.refresh(nuevo_estudiante)
    db.refresh(nuevo_estudiante, ["grupo"])
    
    return nuevo_estudiante


@router.patch("/{estudiante_id}", response_model=EstudianteResponse)
def actualizar_estudiante(
    estudiante_id: int,
    estudiante_update: EstudianteUpdate,
    current_user: Annotated[UserModel, Depends(Auth.get_current_user)],
    db: Session = Depends(get_db),
):
    """
    Actualizar un estudiante.
    Solo docentes directores de grupo, coordinadores y rector.
    """
    estudiante_db = db.query(EstudianteModel).filter(EstudianteModel.id == estudiante_id).first()
    if not estudiante_db:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")

    # Verificar permisos
    es_admin = current_user.rol in ROLES_ADMIN
    es_director = any(g.id == estudiante_db.grupo_id for g in current_user.grupos_a_cargo)
    
    if not es_admin and not es_director:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para modificar estudiantes de este grupo"
        )
    
    datos = estudiante_update.model_dump(exclude_unset=True)
    
    # Validar unicidad si cambian documento o grupo
    nuevo_documento = datos.get('numero_documento', estudiante_db.numero_documento)
    nuevo_grupo_id = datos.get('grupo_id', estudiante_db.grupo_id)
    
    if 'numero_documento' in datos or 'grupo_id' in datos:
        # Validar si grupo existe
        if 'grupo_id' in datos:
            grupo = db.query(GrupoModel).filter(GrupoModel.id == nuevo_grupo_id).first()
            if not grupo:
                raise HTTPException(status_code=404, detail=f"Grupo {nuevo_grupo_id} no encontrado")

        existe = db.query(EstudianteModel).filter(
            EstudianteModel.grupo_id == nuevo_grupo_id,
            EstudianteModel.numero_documento == nuevo_documento,
            EstudianteModel.id != estudiante_id
        ).first()
        
        if existe:
            raise HTTPException(status_code=400, detail="Ya existe un estudiante con ese documento en ese grupo")
    
    for key, value in datos.items():
        setattr(estudiante_db, key, value)
        
    db.commit()
    db.refresh(estudiante_db)
    
    return estudiante_db


@router.delete("/{estudiante_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_estudiante(
    estudiante_id: int,
    current_user: Annotated[UserModel, Depends(Auth.get_current_user)],
    db: Session = Depends(get_db),
):
    """
    Eliminar un estudiante.
    Solo docentes directores de grupo, coordinadores y rector.
    """
    estudiante_db = db.query(EstudianteModel).filter(EstudianteModel.id == estudiante_id).first()
    if not estudiante_db:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")

    # Verificar permisos
    es_admin = current_user.rol in ROLES_ADMIN
    es_director = any(g.id == estudiante_db.grupo_id for g in current_user.grupos_a_cargo)
    
    if not es_admin and not es_director:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para eliminar estudiantes de este grupo"
        )
    
    db.delete(estudiante_db)
    db.commit()
    
    return None
