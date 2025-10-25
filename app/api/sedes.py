from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.config import get_db
from typing import Annotated, List
from app.models.user import User as UserModel
from app.schemas.sedes import SedesResponse
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
