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

@router.get("/estudiante/{estudiante_id}/historial")
def get_observadores_estudiante_historial(
    estudiante_id: int,
    current_user: Annotated[UserModel, Depends(Auth.get_current_user)],
    db: Session = Depends(get_db)
):
    """
    Obtener TODAS las observaciones históricas de un estudiante (todos los periodos).
    Uso: Generación de reportes PDF completos.
    La edad se calcula dinámicamente a partir de la fecha de nacimiento.
    """
    from datetime import date
    
    observadores = db.query(ObservadorModel).options(
        joinedload(ObservadorModel.estudiante),
        joinedload(ObservadorModel.docente)
    ).filter(
        ObservadorModel.estudiante_id == estudiante_id
    ).order_by(ObservadorModel.periodo.asc()).all()
    
    # Función para calcular edad
    def calcular_edad(fecha_nacimiento):
        if not fecha_nacimiento:
            return None
        hoy = date.today()
        edad = hoy.year - fecha_nacimiento.year
        if (hoy.month, hoy.day) < (fecha_nacimiento.month, fecha_nacimiento.day):
            edad -= 1
        return edad
    
    # Construir respuesta con edad calculada
    resultado = []
    for obs in observadores:
        estudiante_data = None
        if obs.estudiante:
            estudiante_data = {
                "id": obs.estudiante.id,
                "nombres": obs.estudiante.nombres,
                "apellidos": obs.estudiante.apellidos,
                "numero_documento": obs.estudiante.numero_documento,
                "edad": calcular_edad(obs.estudiante.fecha_nacimiento),
                "fecha_nacimiento": obs.estudiante.fecha_nacimiento,
                "lugar_nacimiento": obs.estudiante.lugar_nacimiento,
                "tipo_documento": obs.estudiante.tipo_documento,
                "rh": obs.estudiante.rh,
                "eps": obs.estudiante.eps,
                "nombre_padre": obs.estudiante.nombre_padre,
                "ocupacion_padre": obs.estudiante.ocupacion_padre,
                "celular_padre": obs.estudiante.celular_padre,
                "nombre_madre": obs.estudiante.nombre_madre,
                "ocupacion_madre": obs.estudiante.ocupacion_madre,
                "celular_madre": obs.estudiante.celular_madre,
                "nombre_acudiente": obs.estudiante.nombre_acudiente,
                "celular_acudiente": obs.estudiante.celular_acudiente
            }
        
        docente_data = None
        if obs.docente:
            docente_data = {
                "id": obs.docente.id,
                "nombre_completo": obs.docente.nombre_completo
            }
        
        resultado.append({
            "id": obs.id,
            "periodo": obs.periodo,
            "estudiante_id": obs.estudiante_id,
            "docente_id": obs.docente_id,
            "fortalezas": obs.fortalezas,
            "dificultades": obs.dificultades,
            "compromisos": obs.compromisos,
            "created_at": obs.created_at,
            "updated_at": obs.updated_at,
            "estudiante": estudiante_data,
            "docente": docente_data
        })
    
    return resultado

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
