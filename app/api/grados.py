from typing import List, Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload

from app.database.config import get_db
from app.models.grados import Grado as GradoModel
from app.models.sedes import Sedes as SedesModel
from app.models.user import User as UserModel
from app.schemas.grados import (
    GradoCreate,
    GradoUpdate,
    GradoResponse
)
from app.services.auth import Auth

router = APIRouter(
    prefix="/grados",
    tags=["grados"],
)

ROLES_ADMIN = ["coordinador", "rector"]


@router.get("/", response_model=List[GradoResponse])
def listar_grados(
    current_user: Annotated[UserModel, Depends(Auth.get_current_user)],
    db: Session = Depends(get_db),
    sede_id: Optional[int] = Query(None, description="Filtrar por ID de sede"),
):
    """
    Listar grados.
    Puede filtrar por sede.
    """
    query = db.query(GradoModel).options(
        joinedload(GradoModel.sede),
        joinedload(GradoModel.grupos)
    )

    if sede_id:
        query = query.filter(GradoModel.sede_id == sede_id)

    grados = query.order_by(GradoModel.sede_id, GradoModel.nombre).all()
    
    # Agregar cantidad de grupos a cada grado
    result = []
    for grado in grados:
        grado_dict = {
            "id": grado.id,
            "sede_id": grado.sede_id,
            "nombre": grado.nombre,
            "codigo": grado.codigo,
            "created_at": grado.created_at,
            "updated_at": grado.updated_at,
            "cantidad_grupos": len(grado.grupos) if grado.grupos else 0,
            "sede": grado.sede
        }
        result.append(grado_dict)
    
    return result


@router.get("/{grado_id}", response_model=GradoResponse)
def obtener_grado(
    grado_id: int,
    current_user: Annotated[UserModel, Depends(Auth.get_current_user)],
    db: Session = Depends(get_db),
):
    """
    Obtener un grado por ID.
    """
    grado = (
        db.query(GradoModel)
        .options(
            joinedload(GradoModel.sede),
            joinedload(GradoModel.grupos)
        )
        .filter(GradoModel.id == grado_id)
        .first()
    )

    if not grado:
        raise HTTPException(status_code=404, detail="Grado no encontrado")

    return {
        "id": grado.id,
        "sede_id": grado.sede_id,
        "nombre": grado.nombre,
        "codigo": grado.codigo,
        "created_at": grado.created_at,
        "updated_at": grado.updated_at,
        "cantidad_grupos": len(grado.grupos) if grado.grupos else 0,
        "sede": grado.sede
    }


@router.post("/", response_model=GradoResponse, status_code=status.HTTP_201_CREATED)
def crear_grado(
    grado: GradoCreate,
    current_user: Annotated[UserModel, Depends(Auth.get_current_user)],
    db: Session = Depends(get_db),
):
    """
    Crear un nuevo grado.
    Solo coordinadores y rector.
    """
    if current_user.rol not in ROLES_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para realizar esta acción"
        )
    
    # Validar Sede
    sede = db.query(SedesModel).filter(SedesModel.id == grado.sede_id).first()
    if not sede:
        raise HTTPException(status_code=404, detail=f"Sede {grado.sede_id} no encontrada")

    # Validar duplicado (nombre en misma sede)
    existe = db.query(GradoModel).filter(
        GradoModel.sede_id == grado.sede_id,
        GradoModel.nombre == grado.nombre
    ).first()
    
    if existe:
        raise HTTPException(status_code=400, detail="Ya existe este grado en la sede indicada")

    nuevo_grado = GradoModel(**grado.model_dump())
    db.add(nuevo_grado)
    db.commit()
    db.refresh(nuevo_grado)
    db.refresh(nuevo_grado, ["sede"])
    
    return nuevo_grado


@router.patch("/{grado_id}", response_model=GradoResponse)
def actualizar_grado(
    grado_id: int,
    grado_update: GradoUpdate,
    current_user: Annotated[UserModel, Depends(Auth.get_current_user)],
    db: Session = Depends(get_db),
):
    """
    Actualizar un grado.
    Solo coordinadores y rector.
    """
    if current_user.rol not in ROLES_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para realizar esta acción"
        )

    grado_db = db.query(GradoModel).filter(GradoModel.id == grado_id).first()
    if not grado_db:
        raise HTTPException(status_code=404, detail="Grado no encontrado")
    
    datos = grado_update.model_dump(exclude_unset=True)
    
    # Validar unicidad si cambian nombre o sede
    nuevo_nombre = datos.get('nombre', grado_db.nombre)
    nueva_sede_id = datos.get('sede_id', grado_db.sede_id)
    
    if 'nombre' in datos or 'sede_id' in datos:
        # Validar si sede existe
        if 'sede_id' in datos:
             sede = db.query(SedesModel).filter(SedesModel.id == nueva_sede_id).first()
             if not sede:
                 raise HTTPException(status_code=404, detail=f"Sede {nueva_sede_id} no encontrada")

        existe = db.query(GradoModel).filter(
            GradoModel.sede_id == nueva_sede_id,
            GradoModel.nombre == nuevo_nombre,
            GradoModel.id != grado_id
        ).first()
        
        if existe:
             raise HTTPException(status_code=400, detail="Ya existe un grado con ese nombre en esa sede")
    
    for key, value in datos.items():
        setattr(grado_db, key, value)
        
    db.commit()
    db.refresh(grado_db)
    
    return grado_db


@router.delete("/{grado_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_grado(
    grado_id: int,
    current_user: Annotated[UserModel, Depends(Auth.get_current_user)],
    db: Session = Depends(get_db),
):
    """
    Eliminar un grado.
    Solo coordinadores y rector.
    """
    if current_user.rol not in ROLES_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para realizar esta acción"
        )

    grado_db = db.query(GradoModel).filter(GradoModel.id == grado_id).first()
    if not grado_db:
        raise HTTPException(status_code=404, detail="Grado no encontrado")
    
    db.delete(grado_db)
    db.commit()
    
    return None
