from typing import List, Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload

from app.database.config import get_db
from app.models.grupos import Grupo as GrupoModel
from app.models.grados import Grado as GradoModel
from app.models.docente_grupos import DocenteGrupo
from app.models.user import User as UserModel
from app.schemas.grupos import (
    GrupoCreate,
    GrupoUpdate,
    GrupoResponse,
    AsignarDirectorRequest
)
from app.services.auth import Auth

router = APIRouter(
    prefix="/grupos",
    tags=["grupos"],
)

ROLES_ADMIN = ["coordinador", "rector"]


@router.get("/", response_model=List[GrupoResponse])
def listar_grupos(
    current_user: Annotated[UserModel, Depends(Auth.get_current_user)],
    db: Session = Depends(get_db),
    grado_id: Optional[int] = Query(None, description="Filtrar por ID de grado"),
):
    """
    Listar grupos.
    Puede filtrar por grado.
    """
    query = db.query(GrupoModel).options(joinedload(GrupoModel.grado))

    if grado_id:
        query = query.filter(GrupoModel.grado_id == grado_id)

    return query.order_by(GrupoModel.grado_id, GrupoModel.nombre).all()


@router.get("/{grupo_id}", response_model=GrupoResponse)
def obtener_grupo(
    grupo_id: int,
    current_user: Annotated[UserModel, Depends(Auth.get_current_user)],
    db: Session = Depends(get_db),
):
    """Obtener grupo por ID."""
    grupo = (
        db.query(GrupoModel)
        .options(joinedload(GrupoModel.grado))
        .filter(GrupoModel.id == grupo_id)
        .first()
    )

    if not grupo:
        raise HTTPException(status_code=404, detail="Grupo no encontrado")

    return grupo


@router.post("/", response_model=GrupoResponse, status_code=status.HTTP_201_CREATED)
def crear_grupo(
    grupo: GrupoCreate,
    current_user: Annotated[UserModel, Depends(Auth.get_current_user)],
    db: Session = Depends(get_db),
):
    """Crear grupo. Solo coordinadores y rector."""
    if current_user.rol not in ROLES_ADMIN:
        raise HTTPException(status_code=403, detail="Sin permisos")
    
    # Validar Grado
    grado = db.query(GradoModel).filter(GradoModel.id == grupo.grado_id).first()
    if not grado:
        raise HTTPException(status_code=404, detail=f"Grado {grupo.grado_id} no encontrado")

    # Validar duplicado
    existe = db.query(GrupoModel).filter(
        GrupoModel.grado_id == grupo.grado_id,
        GrupoModel.nombre == grupo.nombre
    ).first()
    
    if existe:
        raise HTTPException(status_code=400, detail="Ya existe este grupo en el grado indicado")

    nuevo_grupo = GrupoModel(**grupo.model_dump())
    db.add(nuevo_grupo)
    db.commit()
    db.refresh(nuevo_grupo)
    db.refresh(nuevo_grupo, ["grado"])
    
    return nuevo_grupo


@router.patch("/{grupo_id}", response_model=GrupoResponse)
def actualizar_grupo(
    grupo_id: int,
    grupo_update: GrupoUpdate,
    current_user: Annotated[UserModel, Depends(Auth.get_current_user)],
    db: Session = Depends(get_db),
):
    """Actualizar grupo. Solo coordinadores y rector."""
    if current_user.rol not in ROLES_ADMIN:
        raise HTTPException(status_code=403, detail="Sin permisos")

    grupo_db = db.query(GrupoModel).filter(GrupoModel.id == grupo_id).first()
    if not grupo_db:
        raise HTTPException(status_code=404, detail="Grupo no encontrado")
    
    datos = grupo_update.model_dump(exclude_unset=True)
    
    # Validar duplicados si cambia nombre o grado
    nuevo_nombre = datos.get('nombre', grupo_db.nombre)
    nuevo_grado_id = datos.get('grado_id', grupo_db.grado_id)
    
    if 'nombre' in datos or 'grado_id' in datos:
        if 'grado_id' in datos:
             grado = db.query(GradoModel).filter(GradoModel.id == nuevo_grado_id).first()
             if not grado:
                 raise HTTPException(status_code=404, detail=f"Grado {nuevo_grado_id} no encontrado")

        existe = db.query(GrupoModel).filter(
            GrupoModel.grado_id == nuevo_grado_id,
            GrupoModel.nombre == nuevo_nombre,
            GrupoModel.id != grupo_id
        ).first()
        
        if existe:
             raise HTTPException(status_code=400, detail="Ya existe un grupo con ese nombre en ese grado")
    
    for key, value in datos.items():
        setattr(grupo_db, key, value)
        
    db.commit()
    db.refresh(grupo_db)
    
    return grupo_db


@router.delete("/{grupo_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_grupo(
    grupo_id: int,
    current_user: Annotated[UserModel, Depends(Auth.get_current_user)],
    db: Session = Depends(get_db),
):
    """Eliminar grupo. Solo coordinadores y rector."""
    if current_user.rol not in ROLES_ADMIN:
        raise HTTPException(status_code=403, detail="Sin permisos")

    grupo_db = db.query(GrupoModel).filter(GrupoModel.id == grupo_id).first()
    if not grupo_db:
        raise HTTPException(status_code=404, detail="Grupo no encontrado")
    
    db.delete(grupo_db)
    db.commit()
    
    return None


# --- Asignación de Directores de Grupo ---

@router.post("/{grupo_id}/directores", status_code=status.HTTP_201_CREATED)
def asignar_director(
    grupo_id: int,
    asignacion: AsignarDirectorRequest,
    current_user: Annotated[UserModel, Depends(Auth.get_current_user)],
    db: Session = Depends(get_db),
):
    """
    Asignar un director de grupo.
    Solo coordinadores y rector.
    """
    if current_user.rol not in ROLES_ADMIN:
        raise HTTPException(status_code=403, detail="Sin permisos")

    # Validar Grupo
    grupo = db.query(GrupoModel).filter(GrupoModel.id == grupo_id).first()
    if not grupo:
        raise HTTPException(status_code=404, detail="Grupo no encontrado")

    # Validar Docente
    docente = db.query(UserModel).filter(UserModel.id == asignacion.docente_id).first()
    if not docente:
        raise HTTPException(status_code=404, detail="Docente no encontrado")
    
    if docente.rol != 'docente':
        raise HTTPException(status_code=400, detail="El usuario seleccionado no es un docente")

    # Verificar existencia
    existe = db.query(DocenteGrupo).filter(
        DocenteGrupo.grupo_id == grupo_id,
        DocenteGrupo.docente_id == asignacion.docente_id
    ).first()

    if existe:
        raise HTTPException(status_code=400, detail="Este docente ya es director de este grupo")

    nueva_asignacion = DocenteGrupo(
        grupo_id=grupo_id,
        docente_id=asignacion.docente_id
    )
    db.add(nueva_asignacion)
    db.commit()

    return {"msg": "Director de grupo asignado correctamente"}


@router.delete("/{grupo_id}/directores/{docente_id}", status_code=status.HTTP_204_NO_CONTENT)
def desasignar_director(
    grupo_id: int,
    docente_id: int,
    current_user: Annotated[UserModel, Depends(Auth.get_current_user)],
    db: Session = Depends(get_db),
):
    """Quitar director de grupo."""
    if current_user.rol not in ROLES_ADMIN:
        raise HTTPException(status_code=403, detail="Sin permisos")

    asignacion = db.query(DocenteGrupo).filter(
        DocenteGrupo.grupo_id == grupo_id,
        DocenteGrupo.docente_id == docente_id
    ).first()

    if not asignacion:
        raise HTTPException(status_code=404, detail="La asignación no existe")

    db.delete(asignacion)
    db.commit()

    return None
