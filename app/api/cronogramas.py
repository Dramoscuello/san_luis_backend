from typing import Annotated, List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query, Body
from sqlalchemy.orm import Session, joinedload
from app.database.config import get_db

from app.models.user import User as UserModel
from app.models.cronogramas import Cronograma, ActividadCronograma, EvidenciaActividad
from app.schemas.cronogramas import (
    CronogramaCreate, CronogramaUpdate, CronogramaResponse, CronogramaDetailResponse,
    ActividadCreate, ActividadUpdate, ActividadResponse,
    EvidenciaResponse
)
from app.services.auth import Auth
from app.services.google_drive import drive_service

router = APIRouter(prefix="/cronogramas", tags=["cronogramas"])

# --- CRONOGRAMAS ---

@router.get("/", response_model=List[CronogramaResponse])
def listar_cronogramas(
    current_user: Annotated[UserModel, Depends(Auth.get_current_user)],
    anio: Optional[int] = Query(None),
    docente_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    """
    Lista todos los cronogramas.
    - Docentes: Solo ven el suyo (filtro docente_id forzado)
    - Directivos: Ven todos, pueden filtrar por docente_id
    """
    if not anio:
        anio = datetime.now().year
        
    query = db.query(Cronograma).options(joinedload(Cronograma.docente))
    
    # Filtro de seguridad
    if current_user.rol == 'docente':
        query = query.filter(Cronograma.docente_id == current_user.id)
    elif docente_id:
        # Si es admin y pide uno específico
        query = query.filter(Cronograma.docente_id == docente_id)
        
    # Filtro de año
    query = query.filter(Cronograma.anio_escolar == anio)
    
    return query.all()

@router.post("/", response_model=CronogramaResponse, status_code=status.HTTP_201_CREATED)
def crear_cronograma(
    cronograma: CronogramaCreate,
    current_user: Annotated[UserModel, Depends(Auth.get_current_user)],
    db: Session = Depends(get_db),
):
    """Crea el contenedor del cronograma anual para el docente actual."""
    if current_user.rol != "docente":
        raise HTTPException(status_code=403, detail="Solo docentes pueden crear cronogramas")
    
    anio_actual = datetime.now().year
    
    # Verificar duplicados
    existe = db.query(Cronograma).filter(
        Cronograma.docente_id == current_user.id,
        Cronograma.anio_escolar == anio_actual
    ).first()
    
    if existe:
        raise HTTPException(
            status_code=400, 
            detail=f"Ya existe un cronograma creado para el año {anio_actual}"
        )
    
    nuevo = Cronograma(
        docente_id=current_user.id,
        titulo=cronograma.titulo,
        descripcion=cronograma.descripcion,
        anio_escolar=anio_actual
    )
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo

@router.get("/me", response_model=CronogramaDetailResponse)
def mi_cronograma_detalle(
    current_user: Annotated[UserModel, Depends(Auth.get_current_user)],
    anio: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    """Retorna el cronograma completo (con actividades) del usuario actual."""
    if not anio:
        anio = datetime.now().year
        
    cronograma = db.query(Cronograma).options(
        joinedload(Cronograma.actividades).joinedload(ActividadCronograma.evidencias),
        joinedload(Cronograma.docente)
    ).filter(
        Cronograma.docente_id == current_user.id,
        Cronograma.anio_escolar == anio
    ).first()
    
    if not cronograma:
        raise HTTPException(
            status_code=404, 
            detail=f"No se encontró cronograma para el año {anio}. Debes crearlo primero."
        )
        
    return cronograma

@router.get("/docente/{docente_id}", response_model=CronogramaDetailResponse)
def cronograma_por_docente(
    docente_id: int,
    current_user: Annotated[UserModel, Depends(Auth.get_current_user)],
    anio: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    """
    Obtiene el cronograma detallado de un docente específico.
    Solo permitido para coordinadores y rector.
    """
    if current_user.rol not in ["coordinador", "rector"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para consultar cronogramas de otros docentes"
        )

    if not anio:
        anio = datetime.now().year

    cronograma = db.query(Cronograma).options(
        joinedload(Cronograma.actividades).joinedload(ActividadCronograma.evidencias),
        joinedload(Cronograma.docente)
    ).filter(
        Cronograma.docente_id == docente_id,
        Cronograma.anio_escolar == anio
    ).first()

    if not cronograma:
        raise HTTPException(
            status_code=404, 
            detail=f"El docente no ha creado un cronograma para el año {anio}"
        )

    return cronograma

@router.get("/{id}", response_model=CronogramaDetailResponse)
def ver_cronograma_detalle(
    id: int,
    current_user: Annotated[UserModel, Depends(Auth.get_current_user)],
    db: Session = Depends(get_db),
):
    """
    Ver detalle completo de un cronograma específico.
    Permitido para el dueño o coordinadores/rector.
    """
    cronograma = db.query(Cronograma).options(
        joinedload(Cronograma.actividades).joinedload(ActividadCronograma.evidencias),
        joinedload(Cronograma.docente)
    ).filter(Cronograma.id == id).first()
    
    if not cronograma:
        raise HTTPException(status_code=404, detail="Cronograma no encontrado")
        
    # Validación de permisos
    if current_user.rol == 'docente' and cronograma.docente_id != current_user.id:
        raise HTTPException(status_code=403, detail="No tienes permiso para ver este cronograma")
        
    return cronograma

# --- ACTIVIDADES ---

@router.post("/actividades", response_model=ActividadResponse)
def agregar_actividad(
    actividad: ActividadCreate,
    current_user: Annotated[UserModel, Depends(Auth.get_current_user)],
    db: Session = Depends(get_db),
):
    """Agrega una actividad puntual al calendario."""
    # Verificar que el cronograma existe y pertenece al usuario
    cronograma = db.query(Cronograma).filter(Cronograma.id == actividad.cronograma_id).first()
    
    if not cronograma:
        raise HTTPException(status_code=404, detail="Cronograma padre no encontrado")
        
    if cronograma.docente_id != current_user.id:
        raise HTTPException(status_code=403, detail="No puedes modificar cronogramas de otros docentes")
        
    nueva_actividad = ActividadCronograma(
        cronograma_id=actividad.cronograma_id,
        titulo=actividad.titulo,
        descripcion=actividad.descripcion,
        fecha_programada=actividad.fecha_programada,
        estado='pendiente'
    )
    db.add(nueva_actividad)
    db.commit()
    db.refresh(nueva_actividad)
    return nueva_actividad

@router.patch("/actividades/{id}", response_model=ActividadResponse)
def actualizar_actividad(
    id: int,
    actividad_update: ActividadUpdate,
    current_user: Annotated[UserModel, Depends(Auth.get_current_user)],
    db: Session = Depends(get_db),
):
    """Actualiza datos de la actividad (mover fecha, cambiar estado, etc)."""
    actividad = db.query(ActividadCronograma).options(
        joinedload(ActividadCronograma.cronograma)
    ).filter(ActividadCronograma.id == id).first()
    
    if not actividad:
        raise HTTPException(status_code=404, detail="Actividad no encontrada")
        
    if actividad.cronograma.docente_id != current_user.id:
        raise HTTPException(status_code=403, detail="No tienes permiso para editar esta actividad")
        
    # Aplicar actualizaciones
    if actividad_update.titulo is not None:
        actividad.titulo = actividad_update.titulo
    if actividad_update.descripcion is not None:
        actividad.descripcion = actividad_update.descripcion
    if actividad_update.fecha_programada is not None:
        actividad.fecha_programada = actividad_update.fecha_programada
    if actividad_update.estado is not None:
        actividad.estado = actividad_update.estado
    
    db.commit()
    db.refresh(actividad)
    return actividad

@router.delete("/actividades/{id}")
def eliminar_actividad(
    id: int,
    current_user: Annotated[UserModel, Depends(Auth.get_current_user)],
    db: Session = Depends(get_db),
):
    """Elimina una actividad (y sus evidencias en cascada DB, OJO: falta borrar evidencias Drive)."""
    actividad = db.query(ActividadCronograma).options(
        joinedload(ActividadCronograma.cronograma)
    ).filter(ActividadCronograma.id == id).first()
    
    if not actividad:
        raise HTTPException(status_code=404, detail="Actividad no encontrada")
        
    if actividad.cronograma.docente_id != current_user.id:
        raise HTTPException(status_code=403, detail="No permisos")
        
    # TODO: Idealmente iterar evidencias y borrar de Drive antes de borrar de DB
    # Por brevedad, se borra de DB. El archivo Drive quedará huérfano (recolección basura futura).
    
    db.delete(actividad)
    db.commit()
    return {"mensaje": "Actividad eliminada"}

# --- EVIDENCIAS ---

@router.post("/evidencias", response_model=EvidenciaResponse)
async def subir_evidencia(
    current_user: Annotated[UserModel, Depends(Auth.get_current_user)],
    db: Session = Depends(get_db),
    actividad_id: int = Form(...),
    comentario: Optional[str] = Form(None),
    archivo: UploadFile = File(...),
):
    """Sube un archivo como evidencia para una actividad."""
    
    # 1. Validar actividad y permisos
    actividad = db.query(ActividadCronograma).options(
        joinedload(ActividadCronograma.cronograma)
    ).filter(ActividadCronograma.id == actividad_id).first()
    
    if not actividad:
        raise HTTPException(status_code=404, detail="Actividad no encontrada")
        
    if actividad.cronograma.docente_id != current_user.id:
        raise HTTPException(status_code=403, detail="No tienes permiso para subir evidencias aquí")

    # 2. Validar Servicio Drive
    if not drive_service.is_configured():
        raise HTTPException(status_code=503, detail="Google Drive no configurado")
        
    # 3. Subir archivo
    try:
        content = await archivo.read()
        if len(content) > 10 * 1024 * 1024: # 10MB limit
             raise HTTPException(status_code=400, detail="Archivo muy grande (>10MB)")

        res = drive_service.upload_file(
            file_content=content,
            filename=archivo.filename,
            mime_type=archivo.content_type,
            subfolder="evidencias_cronograma"
        )
        
        # 4. Crear registro DB
        evidencia = EvidenciaActividad(
            actividad_id=actividad_id,
            drive_file_id=res['file_id'],
            drive_view_link=res.get('view_link'),
            drive_download_link=res.get('download_link'),
            nombre_archivo=res.get('filename'),
            tipo_archivo=archivo.content_type,
            comentario_docente=comentario
        )
        
        # Mágica UX: Si sube evidencia, marcamos completada automáticamente
        if actividad.estado == 'pendiente':
            actividad.estado = 'completada'
            
        db.add(evidencia)
        db.commit()
        db.refresh(evidencia)
        return evidencia
        
    except Exception as e:
        # Si falla Drive, no guardamos en DB
        raise HTTPException(status_code=500, detail=f"Error subiendo archivo: {str(e)}")

@router.delete("/evidencias/{id}")
def eliminar_evidencia(
    id: int,
    current_user: Annotated[UserModel, Depends(Auth.get_current_user)],
    db: Session = Depends(get_db),
):
    """Elimina una evidencia tanto de DB como de Drive."""
    evidencia = db.query(EvidenciaActividad).options(
        joinedload(EvidenciaActividad.actividad).joinedload(ActividadCronograma.cronograma)
    ).filter(EvidenciaActividad.id == id).first()
    
    if not evidencia:
        raise HTTPException(status_code=404, detail="Evidencia no encontrada")
        
    if evidencia.actividad.cronograma.docente_id != current_user.id:
        raise HTTPException(status_code=403, detail="No permisos")
        
    # Borrar de Drive
    try:
        if evidencia.drive_file_id:
            drive_service.delete_file(evidencia.drive_file_id)
    except Exception:
        pass # Ignoramos fallo de Drive, priorizamos limpiar DB

    db.delete(evidencia)
    db.commit()
    return {"mensaje": "Evidencia eliminada"}
