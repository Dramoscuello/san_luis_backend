from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.config import get_db
from typing import Annotated, List
from app.models.user import User as UserModel
from app.models.areas import Area as AreaModel
from app.schemas.areas import AreaCreate, AreaUpdate, AreaResponse
from app.services.auth import Auth


router = APIRouter(
    prefix="/areas",
    tags=["areas"],
)


@router.get("/", response_model=List[AreaResponse])
def get_areas(
    current_user: Annotated[UserModel, Depends(Auth.get_current_user)],
    db: Session = Depends(get_db),
):
    areas = db.query(AreaModel).all()
    if not areas:
        raise HTTPException(status_code=404, detail="No se encontraron áreas")
    return areas


@router.get("/{area_id}", response_model=AreaResponse)
def get_area(
    area_id: int,
    current_user: Annotated[UserModel, Depends(Auth.get_current_user)],
    db: Session = Depends(get_db),
):
    area = db.query(AreaModel).filter(AreaModel.id == area_id).first()
    if not area:
        raise HTTPException(status_code=404, detail="Área no encontrada")
    return area


@router.post("/", response_model=AreaResponse, status_code=201)
def create_area(
    area: AreaCreate,
    current_user: Annotated[UserModel, Depends(Auth.get_current_user)],
    db: Session = Depends(get_db),
):
    # Verificar si ya existe un área con ese nombre
    area_existente = db.query(AreaModel).filter(AreaModel.nombre == area.nombre).first()
    if area_existente:
        raise HTTPException(status_code=400, detail="Ya existe un área con ese nombre")

    area_new = AreaModel(**area.model_dump())
    db.add(area_new)
    db.commit()
    db.refresh(area_new)
    return area_new


@router.patch("/{area_id}", response_model=AreaResponse)
def update_area(
    area_id: int,
    area: AreaUpdate,
    current_user: Annotated[UserModel, Depends(Auth.get_current_user)],
    db: Session = Depends(get_db),
):
    area_update = db.query(AreaModel).filter(AreaModel.id == area_id)
    if not area_update.first():
        raise HTTPException(status_code=404, detail="Área no encontrada")

    area_update.update(area.model_dump(exclude_unset=True))
    db.commit()
    return area_update.first()


@router.delete("/{area_id}")
def delete_area(
    area_id: int,
    current_user: Annotated[UserModel, Depends(Auth.get_current_user)],
    db: Session = Depends(get_db),
):
    area_delete = db.query(AreaModel).filter(AreaModel.id == area_id)
    if not area_delete.first():
        raise HTTPException(status_code=404, detail="Área no encontrada")

    area_delete.delete(synchronize_session=False)
    db.commit()
    return {'mensaje': 'Área eliminada correctamente'}
