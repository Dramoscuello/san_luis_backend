from typing import List, Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from app.database.config import get_db
from app.models.observadores import Observador as ObservadorModel
from app.models.user import User as UserModel
from app.models.periodos import Periodo as PeriodoModel
from app.schemas.observadores import ObservadorCreate, ObservadorUpdate, ObservadorResponse
from app.services.auth import Auth

router = APIRouter(
    prefix="/observadores",
    tags=["observadores"]
)

@router.post("/", response_model=ObservadorResponse, status_code=status.HTTP_201_CREATED)
def create_observador(
    observador: ObservadorCreate,
    current_user: Annotated[UserModel, Depends(Auth.get_current_user)],
    db: Session = Depends(get_db)
):
    """
    Crear una nueva observación para un estudiante para el periodo ACTUALMENTE activo.
    El periodo se infiere automáticamente del sistema.
    """
    # 1. Obtener Periodo Activo
    periodo_activo = db.query(PeriodoModel).filter(PeriodoModel.activo == True).first()
    
    if not periodo_activo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No hay ningún periodo académico activo en este momento. Contacta a coordinación."
        )
    
    try:
        numero_periodo_activo = int(periodo_activo.nombre)
    except ValueError:
        raise HTTPException(
            status_code=500,
            detail=f"Error de configuración: El nombre del periodo activo '{periodo_activo.nombre}' no es un número válido."
        )

    # 2. Verificar duplicados (docente + estudiante + periodo)
    existe = db.query(ObservadorModel).filter(
        ObservadorModel.estudiante_id == observador.estudiante_id,
        ObservadorModel.docente_id == current_user.id,
        ObservadorModel.periodo == numero_periodo_activo
    ).first()

    if existe:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ya existe una observación tuya para este estudiante en el periodo {numero_periodo_activo}. Usa la opción de editar."
        )

    # 3. Crear
    nuevo_observador = ObservadorModel(
        estudiante_id=observador.estudiante_id,
        docente_id=current_user.id,
        periodo=numero_periodo_activo,
        fortalezas=observador.fortalezas,
        dificultades=observador.dificultades,
        compromisos=observador.compromisos
    )
    
    db.add(nuevo_observador)
    db.commit()
    db.refresh(nuevo_observador)
    
    # 4. Cargar relaciones
    observador_db = db.query(ObservadorModel).options(
        joinedload(ObservadorModel.estudiante),
        joinedload(ObservadorModel.docente)
    ).filter(ObservadorModel.id == nuevo_observador.id).first()
    
    return observador_db

@router.get("/estudiante/{estudiante_id}/actual", response_model=List[ObservadorResponse])
def get_observadores_estudiante_actual(
    estudiante_id: int,
    current_user: Annotated[UserModel, Depends(Auth.get_current_user)],
    db: Session = Depends(get_db)
):
    """
    Obtener las observaciones del estudiante SOLO para el periodo activo.
    Uso: Docentes al entrar a calificar/observar.
    """
    # 1. Obtener periodo activo
    periodo_activo = db.query(PeriodoModel).filter(PeriodoModel.activo == True).first()
    if not periodo_activo:
        return [] # O raise exception, dependiendo UX. Retornar vacío es seguro.

    try:
        numero_periodo_activo = int(periodo_activo.nombre)
    except ValueError:
        return []

    observadores = db.query(ObservadorModel).options(
        joinedload(ObservadorModel.estudiante),
        joinedload(ObservadorModel.docente)
    ).filter(
        ObservadorModel.estudiante_id == estudiante_id,
        ObservadorModel.periodo == numero_periodo_activo
    ).all()
    
    return observadores

@router.get("/estudiante/{estudiante_id}/historial", response_model=List[ObservadorResponse])
def get_observadores_estudiante_historial(
    estudiante_id: int,
    current_user: Annotated[UserModel, Depends(Auth.get_current_user)],
    db: Session = Depends(get_db)
):
    """
    Obtener TODAS las observaciones históricas de un estudiante (todos los periodos).
    Uso: Generación de reportes PDF completos.
    """
    observadores = db.query(ObservadorModel).options(
        joinedload(ObservadorModel.estudiante),
        joinedload(ObservadorModel.docente)
    ).filter(
        ObservadorModel.estudiante_id == estudiante_id
    ).order_by(ObservadorModel.periodo.asc()).all()
    
    return observadores

@router.put("/{id}", response_model=ObservadorResponse)
def update_observador(
    id: int,
    observador_update: ObservadorUpdate,
    current_user: Annotated[UserModel, Depends(Auth.get_current_user)],
    db: Session = Depends(get_db)
):
    """
    Actualizar una observación. Solo el autor puede editarla.
    """
    observacion_db = db.query(ObservadorModel).filter(ObservadorModel.id == id).first()
    
    if not observacion_db:
        raise HTTPException(status_code=404, detail="Observación no encontrada")
    
    if observacion_db.docente_id != current_user.id and current_user.rol == 'docente':
        raise HTTPException(status_code=403, detail="No tienes permiso para editar esta observación")
        
    # Actualizar campos
    if observador_update.fortalezas is not None:
        observacion_db.fortalezas = observador_update.fortalezas
    if observador_update.dificultades is not None:
        observacion_db.dificultades = observador_update.dificultades
    if observador_update.compromisos is not None:
        observacion_db.compromisos = observador_update.compromisos

    db.commit()
    db.refresh(observacion_db)
    
    # Recargar con relaciones
    observacion_db = db.query(ObservadorModel).options(
        joinedload(ObservadorModel.estudiante),
        joinedload(ObservadorModel.docente)
    ).filter(ObservadorModel.id == id).first()
    
    return observacion_db

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_observador(
    id: int,
    current_user: Annotated[UserModel, Depends(Auth.get_current_user)],
    db: Session = Depends(get_db)
):
    """
    Eliminar una observación. Solo el autor puede eliminarla.
    """
    observacion_db = db.query(ObservadorModel).filter(ObservadorModel.id == id).first()
    
    if not observacion_db:
        raise HTTPException(status_code=404, detail="Observación no encontrada")
        
    if observacion_db.docente_id != current_user.id and current_user.rol == 'docente':
         raise HTTPException(status_code=403, detail="No tienes permiso para eliminar esta observación")

    db.delete(observacion_db)
    db.commit()
    return None
