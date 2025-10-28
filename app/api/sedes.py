from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.config import get_db
from typing import Annotated, List
from app.models.user import User as UserModel
from app.schemas.sedes import SedesResponse, UpdateSedes, Sedes
from app.models.sedes import Sedes as SedesModel
from app.services.auth import Auth


router = APIRouter(
    prefix="/sedes",
    tags=["sedes"],
)


@router.get("/", response_model=List[SedesResponse])
def read_sedes(current_user: Annotated[UserModel, Depends(Auth.get_current_user)], db: Session = Depends(get_db)):
    sedes  = db.query(SedesModel).all()
    if not sedes:
        raise HTTPException(status_code=404, detail="Sedes not found")
    return sedes

@router.patch("/{sede_id}")
def update_sedes(current_user: Annotated[UserModel, Depends(Auth.get_current_user)], sede_id:int, sede:UpdateSedes, db: Session = Depends(get_db)):
    sede_update = db.query(SedesModel).filter(SedesModel.id == sede_id)
    if not sede_update.first():
        raise HTTPException(status_code=404, detail="Sedes not found")

    sede_update.update(sede.model_dump(exclude_unset=True))
    db.commit()

    return {'mensaje':'Sede actualizada correctamente'}

@router.delete("/{sede_id}")
def delete_sede(current_user: Annotated[UserModel, Depends(Auth.get_current_user)], sede_id:int, db: Session = Depends(get_db)):
    sede_delete = db.query(SedesModel).filter(SedesModel.id == sede_id)
    if not sede_delete.first():
        raise HTTPException(status_code=404, detail="Sedes not found")

    sede_delete.delete(synchronize_session=False)
    db.commit()
    return {'mensaje':'Sede eliminada correctamente'}

@router.post("/", response_model=SedesResponse)
def create_sede(current_user: Annotated[UserModel, Depends(Auth.get_current_user)], sede: Sedes, db: Session = Depends(get_db)):

    sede_new = sede.model_dump()
    sede_new = SedesModel(**sede_new)

    db.add(sede_new)
    db.commit()
    db.refresh(sede_new)

    return sede_new


