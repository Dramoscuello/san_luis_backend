from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.config import get_db
from typing import Annotated, List, Optional
from app.models.user import User as UserModel
from app.models.periodos import Periodo as PeriodoModel
from app.schemas.periodos import PeriodoUpdate, PeriodoResponse
from app.services.auth import Auth


router = APIRouter(
    prefix="/periodos",
    tags=["periodos"],
)


@router.get("/", response_model=List[PeriodoResponse])
def get_periodos(
    current_user: Annotated[UserModel, Depends(Auth.get_current_user)],
    db: Session = Depends(get_db),
):
    """Listar todos los períodos escolares."""
    periodos = db.query(PeriodoModel).order_by(PeriodoModel.nombre).all()
    return periodos


@router.get("/activo", response_model=Optional[PeriodoResponse])
def get_periodo_activo(
    current_user: Annotated[UserModel, Depends(Auth.get_current_user)],
    db: Session = Depends(get_db),
):
    """Obtener el período actualmente activo."""
    periodo = db.query(PeriodoModel).filter(PeriodoModel.activo == True).first()
    if not periodo:
        raise HTTPException(status_code=404, detail="No hay período activo")
    return periodo


@router.get("/{periodo_id}", response_model=PeriodoResponse)
def get_periodo(
    periodo_id: int,
    current_user: Annotated[UserModel, Depends(Auth.get_current_user)],
    db: Session = Depends(get_db),
):
    """Obtener un período por ID."""
    periodo = db.query(PeriodoModel).filter(PeriodoModel.id == periodo_id).first()
    if not periodo:
        raise HTTPException(status_code=404, detail="Período no encontrado")
    return periodo


@router.patch("/{periodo_id}", response_model=PeriodoResponse)
def update_periodo(
    periodo_id: int,
    periodo: PeriodoUpdate,
    current_user: Annotated[UserModel, Depends(Auth.get_current_user)],
    db: Session = Depends(get_db),
):
    """
    Actualizar un período (fechas, activar/desactivar).
    Solo coordinadores y rector pueden modificar períodos.
    Solo puede haber un período activo a la vez. Si se intenta activar
    un período cuando ya hay otro activo, se retorna error 400.
    """
    # Solo coordinadores y rector pueden modificar períodos
    if current_user.rol not in ["coordinador", "rector"]:
        raise HTTPException(
            status_code=403,
            detail="Solo coordinadores y rector pueden modificar períodos"
        )

    periodo_db = db.query(PeriodoModel).filter(PeriodoModel.id == periodo_id).first()
    if not periodo_db:
        raise HTTPException(status_code=404, detail="Período no encontrado")

    datos = periodo.model_dump(exclude_unset=True)

    # Si se está activando este período, verificar que no haya otro activo
    if datos.get('activo') == True:
        periodo_activo = db.query(PeriodoModel).filter(
            PeriodoModel.activo == True,
            PeriodoModel.id != periodo_id
        ).first()
        if periodo_activo:
            raise HTTPException(
                status_code=400,
                detail=f"Ya existe un período activo (Período {periodo_activo.nombre}). "
                       "Debe desactivarlo antes de activar otro."
            )

    # Actualizar campos
    for key, value in datos.items():
        setattr(periodo_db, key, value)

    db.commit()
    db.refresh(periodo_db)
    return periodo_db
