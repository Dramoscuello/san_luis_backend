from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from sqlalchemy.orm import Session, joinedload
from app.database.config import get_db
from typing import Annotated, List, Optional
from datetime import date
from app.models.user import User as UserModel
from app.models.proyectos import Proyecto as ProyectoModel
from app.models.evidencias_proyecto import EvidenciaProyecto as EvidenciaProyectoModel
from app.models.comentarios_proyecto import ComentarioProyecto as ComentarioProyectoModel
from app.schemas.proyectos import (
    ProyectoCreate,
    ProyectoUpdate,
    ProyectoResponse,
    ProyectoListResponse,
    EvidenciaProyectoResponse,
    ComentarioProyectoCreate,
    ComentarioProyectoResponse,
    ComentarioProyectoUpdate,
)
from app.services.auth import Auth
from app.services.google_drive import drive_service


router = APIRouter(
    prefix="/proyectos",
    tags=["proyectos"],
)

# Roles permitidos para comentar proyectos
ROLES_PERMITIDOS = ["coordinador", "rector"]

# Tipos de archivo permitidos para evidencias
ALLOWED_MIME_TYPES = {
    'application/pdf': 'pdf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'docx',
    'application/msword': 'doc',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': 'xlsx',
    'application/vnd.ms-excel': 'xls',
    'image/jpeg': 'jpg',
    'image/png': 'png',
    'video/mp4': 'mp4',
}

# Tamaño máximo: 10 MB
MAX_FILE_SIZE = 10 * 1024 * 1024


# ==================== PROYECTOS ====================

@router.get("/", response_model=List[ProyectoListResponse])
def listar_proyectos(
    current_user: Annotated[UserModel, Depends(Auth.get_current_user)],
    db: Session = Depends(get_db),
    docente_id: Optional[int] = Query(None, description="Filtrar por docente (solo coordinadores/rector)"),
    estado: Optional[str] = Query(None, description="Filtrar por estado"),
):
    """
    Listar proyectos.

    - **Docentes:** Solo ven sus propios proyectos
    - **Coordinadores/Rector:** Ven todos los proyectos

    Ordenados por fecha de creación (más reciente primero).
    """
    query = (
        db.query(ProyectoModel)
        .options(joinedload(ProyectoModel.docente))
    )

    # Restricción por rol: docentes solo ven sus propios proyectos
    if current_user.rol == "docente":
        query = query.filter(ProyectoModel.docente_id == current_user.id)
    else:
        # Coordinadores y rector pueden filtrar por docente
        if docente_id:
            query = query.filter(ProyectoModel.docente_id == docente_id)

    # Filtrar por estado
    if estado:
        query = query.filter(ProyectoModel.estado == estado)

    proyectos = query.order_by(ProyectoModel.created_at.desc()).all()
    return proyectos


@router.get("/{proyecto_id}", response_model=ProyectoResponse)
def obtener_proyecto(
    proyecto_id: int,
    current_user: Annotated[UserModel, Depends(Auth.get_current_user)],
    db: Session = Depends(get_db),
):
    """
    Obtener un proyecto por ID con todos sus detalles.
    """
    proyecto = (
        db.query(ProyectoModel)
        .options(joinedload(ProyectoModel.docente))
        .filter(ProyectoModel.id == proyecto_id)
        .first()
    )

    if not proyecto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Proyecto no encontrado",
        )

    # Docentes solo pueden ver sus propios proyectos
    if current_user.rol == "docente" and proyecto.docente_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para ver este proyecto",
        )

    return proyecto


@router.post("/", response_model=ProyectoResponse, status_code=status.HTTP_201_CREATED)
async def crear_proyecto(
    current_user: Annotated[UserModel, Depends(Auth.get_current_user)],
    db: Session = Depends(get_db),
    titulo: str = Form(..., min_length=5, max_length=255, description="Título del proyecto"),
    descripcion: str = Form(..., min_length=20, description="Descripción del proyecto"),
    fecha_inicio: date = Form(..., description="Fecha de inicio"),
    objetivos: Optional[str] = Form(None, description="Objetivos del proyecto"),
    fecha_fin_estimada: Optional[date] = Form(None, description="Fecha de fin estimada"),
    archivo: Optional[UploadFile] = File(None, description="Documento base opcional"),
):
    """
    Crear un nuevo proyecto pedagógico.

    - **titulo**: Título del proyecto (mínimo 5 caracteres)
    - **descripcion**: Descripción detallada (mínimo 20 caracteres)
    - **fecha_inicio**: Fecha de inicio del proyecto
    - **objetivos**: Objetivos del proyecto (opcional)
    - **fecha_fin_estimada**: Fecha estimada de finalización (opcional)
    - **archivo**: Documento base opcional (PDF, DOCX, etc.)

    Solo docentes pueden crear proyectos.
    """
    # Validar que sea docente
    if current_user.rol != "docente":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los docentes pueden crear proyectos",
        )

    # Variables para datos del archivo
    drive_file_id = None
    drive_view_link = None
    drive_embed_link = None
    drive_download_link = None
    nombre_archivo_original = None

    # Procesar archivo si se envió
    if archivo and archivo.filename:
        if not drive_service.is_configured():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Google Drive no está configurado. Contacte al administrador.",
            )

        if archivo.content_type not in ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Tipo de archivo no permitido: {archivo.content_type}",
            )

        file_content = await archivo.read()

        if len(file_content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El archivo excede el tamaño máximo de {MAX_FILE_SIZE // (1024*1024)} MB",
            )

        if len(file_content) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El archivo está vacío",
            )

        try:
            result = drive_service.upload_file(
                file_content=file_content,
                filename=archivo.filename,
                mime_type=archivo.content_type,
                subfolder="proyectos"
            )

            drive_file_id = result['file_id']
            drive_view_link = result['view_link']
            drive_embed_link = result['embed_link']
            drive_download_link = result['download_link']
            nombre_archivo_original = result['filename']

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al subir archivo a Google Drive: {str(e)}",
            )

    # Crear el proyecto
    nuevo_proyecto = ProyectoModel(
        docente_id=current_user.id,
        titulo=titulo,
        descripcion=descripcion,
        objetivos=objetivos,
        fecha_inicio=fecha_inicio,
        fecha_fin_estimada=fecha_fin_estimada,
        drive_file_id=drive_file_id,
        drive_view_link=drive_view_link,
        drive_embed_link=drive_embed_link,
        drive_download_link=drive_download_link,
        nombre_archivo_original=nombre_archivo_original,
    )

    db.add(nuevo_proyecto)
    db.commit()
    db.refresh(nuevo_proyecto)
    db.refresh(nuevo_proyecto, ["docente"])

    return nuevo_proyecto


@router.patch("/{proyecto_id}", response_model=ProyectoResponse)
async def actualizar_proyecto(
    proyecto_id: int,
    current_user: Annotated[UserModel, Depends(Auth.get_current_user)],
    db: Session = Depends(get_db),
    titulo: Optional[str] = Form(None, min_length=5, max_length=255),
    descripcion: Optional[str] = Form(None, min_length=20),
    objetivos: Optional[str] = Form(None),
    fecha_inicio: Optional[date] = Form(None),
    fecha_fin_estimada: Optional[date] = Form(None),
    estado: Optional[str] = Form(None),
    archivo: Optional[UploadFile] = File(None, description="Nuevo documento base"),
    eliminar_archivo: bool = Form(False, description="Eliminar documento base actual"),
):
    """
    Actualizar un proyecto existente.

    Solo el docente dueño puede actualizar su proyecto.
    """
    proyecto_db = (
        db.query(ProyectoModel)
        .filter(ProyectoModel.id == proyecto_id)
        .first()
    )

    if not proyecto_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Proyecto no encontrado",
        )

    # Validar que el usuario sea el dueño
    if proyecto_db.docente_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo el docente dueño puede actualizar este proyecto",
        )

    # Actualizar campos si se proporcionan
    if titulo is not None:
        proyecto_db.titulo = titulo
    if descripcion is not None:
        proyecto_db.descripcion = descripcion
    if objetivos is not None:
        proyecto_db.objetivos = objetivos
    if fecha_inicio is not None:
        proyecto_db.fecha_inicio = fecha_inicio
    if fecha_fin_estimada is not None:
        proyecto_db.fecha_fin_estimada = fecha_fin_estimada
    if estado is not None:
        if estado not in ['activo', 'pausado', 'completado', 'cancelado']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Estado inválido. Valores permitidos: activo, pausado, completado, cancelado",
            )
        proyecto_db.estado = estado

    # Manejar eliminación de archivo
    if eliminar_archivo and proyecto_db.drive_file_id:
        try:
            if drive_service.is_configured():
                drive_service.delete_file(proyecto_db.drive_file_id)
        except Exception:
            pass

        proyecto_db.drive_file_id = None
        proyecto_db.drive_view_link = None
        proyecto_db.drive_embed_link = None
        proyecto_db.drive_download_link = None
        proyecto_db.nombre_archivo_original = None

    # Manejar nuevo archivo
    if archivo and archivo.filename:
        if not drive_service.is_configured():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Google Drive no está configurado",
            )

        if archivo.content_type not in ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Tipo de archivo no permitido: {archivo.content_type}",
            )

        file_content = await archivo.read()

        if len(file_content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El archivo excede el tamaño máximo de {MAX_FILE_SIZE // (1024*1024)} MB",
            )

        # Eliminar archivo anterior si existe
        if proyecto_db.drive_file_id:
            try:
                drive_service.delete_file(proyecto_db.drive_file_id)
            except Exception:
                pass

        try:
            result = drive_service.upload_file(
                file_content=file_content,
                filename=archivo.filename,
                mime_type=archivo.content_type,
                subfolder="proyectos"
            )

            proyecto_db.drive_file_id = result['file_id']
            proyecto_db.drive_view_link = result['view_link']
            proyecto_db.drive_embed_link = result['embed_link']
            proyecto_db.drive_download_link = result['download_link']
            proyecto_db.nombre_archivo_original = result['filename']

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al subir archivo: {str(e)}",
            )

    db.commit()
    db.refresh(proyecto_db, ["docente"])

    return proyecto_db


@router.delete("/{proyecto_id}")
def eliminar_proyecto(
    proyecto_id: int,
    current_user: Annotated[UserModel, Depends(Auth.get_current_user)],
    db: Session = Depends(get_db),
):
    """
    Eliminar un proyecto y todas sus evidencias.

    - **Docentes:** Solo pueden eliminar sus propios proyectos
    - **Coordinadores/Rector:** Pueden eliminar cualquier proyecto
    """
    proyecto_db = (
        db.query(ProyectoModel)
        .filter(ProyectoModel.id == proyecto_id)
        .first()
    )

    if not proyecto_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Proyecto no encontrado",
        )

    # Validar permisos
    es_dueno = proyecto_db.docente_id == current_user.id
    es_admin = current_user.rol in ROLES_PERMITIDOS

    if not es_dueno and not es_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para eliminar este proyecto",
        )

    # Eliminar archivo del proyecto de Google Drive
    if proyecto_db.drive_file_id and drive_service.is_configured():
        try:
            drive_service.delete_file(proyecto_db.drive_file_id)
        except Exception:
            pass

    # Eliminar archivos de evidencias de Google Drive
    evidencias = db.query(EvidenciaProyectoModel).filter(
        EvidenciaProyectoModel.proyecto_id == proyecto_id
    ).all()

    for evidencia in evidencias:
        if evidencia.drive_file_id and drive_service.is_configured():
            try:
                drive_service.delete_file(evidencia.drive_file_id)
            except Exception:
                pass

    db.delete(proyecto_db)
    db.commit()

    return {"mensaje": "Proyecto eliminado correctamente"}


# ==================== EVIDENCIAS ====================

@router.get("/{proyecto_id}/evidencias", response_model=List[EvidenciaProyectoResponse])
def listar_evidencias(
    proyecto_id: int,
    current_user: Annotated[UserModel, Depends(Auth.get_current_user)],
    db: Session = Depends(get_db),
):
    """
    Listar evidencias de un proyecto.
    Ordenadas por fecha de evidencia (timeline cronológico).
    """
    # Verificar que el proyecto existe
    proyecto = db.query(ProyectoModel).filter(ProyectoModel.id == proyecto_id).first()
    if not proyecto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Proyecto no encontrado",
        )

    # Docentes solo pueden ver evidencias de sus propios proyectos
    if current_user.rol == "docente" and proyecto.docente_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para ver las evidencias de este proyecto",
        )

    evidencias = (
        db.query(EvidenciaProyectoModel)
        .filter(EvidenciaProyectoModel.proyecto_id == proyecto_id)
        .order_by(EvidenciaProyectoModel.fecha_evidencia.desc())
        .all()
    )

    return evidencias


@router.post("/{proyecto_id}/evidencias", response_model=EvidenciaProyectoResponse, status_code=status.HTTP_201_CREATED)
async def crear_evidencia(
    proyecto_id: int,
    current_user: Annotated[UserModel, Depends(Auth.get_current_user)],
    db: Session = Depends(get_db),
    archivo: UploadFile = File(..., description="Archivo de evidencia (obligatorio)"),
    titulo: str = Form(..., min_length=5, max_length=255, description="Título de la evidencia"),
    fecha_evidencia: date = Form(None, description="Fecha del avance"),
    descripcion: Optional[str] = Form(None, description="Descripción de la evidencia"),
):
    """
    Crear una nueva evidencia de proyecto.

    - **archivo**: Archivo obligatorio (PDF, DOCX, imágenes, video, Excel)
    - **titulo**: Título de la evidencia (mínimo 5 caracteres)
    - **fecha_evidencia**: Fecha del avance/hito (Opcional, automática si no se envía)
    - **descripcion**: Descripción opcional

    Solo el docente dueño del proyecto puede agregar evidencias.
    """
    # Verificar que el proyecto existe
    proyecto = db.query(ProyectoModel).filter(ProyectoModel.id == proyecto_id).first()
    if not proyecto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Proyecto no encontrado",
        )

    # Si no se envía fecha, usar la fecha actual
    if not fecha_evidencia:
        fecha_evidencia = date.today()

    # Validar que sea el dueño del proyecto
    if proyecto.docente_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo el docente dueño puede agregar evidencias a este proyecto",
        )

    # Validar Google Drive
    if not drive_service.is_configured():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google Drive no está configurado. Contacte al administrador.",
        )

    # Validar tipo de archivo
    if archivo.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tipo de archivo no permitido: {archivo.content_type}",
        )

    file_content = await archivo.read()

    if len(file_content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El archivo excede el tamaño máximo de {MAX_FILE_SIZE // (1024*1024)} MB",
        )

    if len(file_content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El archivo está vacío",
        )

    try:
        result = drive_service.upload_file(
            file_content=file_content,
            filename=archivo.filename,
            mime_type=archivo.content_type,
            subfolder="proyectos/evidencias"
        )

        nueva_evidencia = EvidenciaProyectoModel(
            proyecto_id=proyecto_id,
            titulo=titulo,
            descripcion=descripcion,
            fecha_evidencia=fecha_evidencia,
            drive_file_id=result['file_id'],
            drive_view_link=result['view_link'],
            drive_embed_link=result['embed_link'],
            drive_download_link=result['download_link'],
            nombre_archivo_original=result['filename'],
            tipo_archivo=ALLOWED_MIME_TYPES.get(archivo.content_type, 'otro'),
            tamano_bytes=result['size_bytes'],
            subido_por=current_user.id,
        )

        db.add(nueva_evidencia)
        db.commit()
        db.refresh(nueva_evidencia)

        return nueva_evidencia

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al subir archivo a Google Drive: {str(e)}",
        )


@router.delete("/{proyecto_id}/evidencias/{evidencia_id}")
def eliminar_evidencia(
    proyecto_id: int,
    evidencia_id: int,
    current_user: Annotated[UserModel, Depends(Auth.get_current_user)],
    db: Session = Depends(get_db),
):
    """
    Eliminar una evidencia de proyecto.

    Solo el docente dueño del proyecto puede eliminar evidencias.
    """
    evidencia = (
        db.query(EvidenciaProyectoModel)
        .filter(
            EvidenciaProyectoModel.id == evidencia_id,
            EvidenciaProyectoModel.proyecto_id == proyecto_id
        )
        .first()
    )

    if not evidencia:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evidencia no encontrada",
        )

    # Verificar que el proyecto pertenece al usuario
    proyecto = db.query(ProyectoModel).filter(ProyectoModel.id == proyecto_id).first()
    
    es_dueno = proyecto.docente_id == current_user.id
    es_admin = current_user.rol in ROLES_PERMITIDOS

    if not es_dueno and not es_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para eliminar esta evidencia",
        )

    # Eliminar archivo de Google Drive
    if evidencia.drive_file_id and drive_service.is_configured():
        try:
            drive_service.delete_file(evidencia.drive_file_id)
        except Exception:
            pass

    db.delete(evidencia)
    db.commit()

    return {"mensaje": "Evidencia eliminada correctamente"}


# ==================== COMENTARIOS ====================

@router.get("/{proyecto_id}/comentarios", response_model=List[ComentarioProyectoResponse])
def listar_comentarios_proyecto(
    proyecto_id: int,
    current_user: Annotated[UserModel, Depends(Auth.get_current_user)],
    db: Session = Depends(get_db),
):
    """
    Listar comentarios de un proyecto (comentarios generales, no de evidencias).
    """
    # Verificar que el proyecto existe
    proyecto = db.query(ProyectoModel).filter(ProyectoModel.id == proyecto_id).first()
    if not proyecto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Proyecto no encontrado",
        )

    # Docentes solo pueden ver comentarios de sus propios proyectos
    if current_user.rol == "docente" and proyecto.docente_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para ver los comentarios de este proyecto",
        )

    comentarios = (
        db.query(ComentarioProyectoModel)
        .options(joinedload(ComentarioProyectoModel.coordinador))
        .filter(ComentarioProyectoModel.proyecto_id == proyecto_id)
        .order_by(ComentarioProyectoModel.created_at.desc())
        .all()
    )

    return comentarios


@router.post("/{proyecto_id}/comentarios", response_model=ComentarioProyectoResponse, status_code=status.HTTP_201_CREATED)
def crear_comentario_proyecto(
    proyecto_id: int,
    comentario_data: ComentarioProyectoCreate,
    current_user: Annotated[UserModel, Depends(Auth.get_current_user)],
    db: Session = Depends(get_db),
):
    """
    Crear un comentario sobre un proyecto o una evidencia.

    - **proyecto_id**: Se toma de la URL para comentario general
    - **evidencia_id**: ID de la evidencia (si es comentario sobre evidencia específica)
    - **contenido**: Contenido del comentario (mínimo 10 caracteres)

    Solo coordinadores y rector pueden comentar.
    """
    # Validar rol
    if current_user.rol not in ROLES_PERMITIDOS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo coordinadores y rector pueden comentar proyectos",
        )

    # Verificar que el proyecto existe
    proyecto = db.query(ProyectoModel).filter(ProyectoModel.id == proyecto_id).first()
    if not proyecto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Proyecto no encontrado",
        )

    # Determinar si es comentario sobre proyecto o evidencia
    if comentario_data.evidencia_id:
        # Verificar que la evidencia existe y pertenece al proyecto
        evidencia = db.query(EvidenciaProyectoModel).filter(
            EvidenciaProyectoModel.id == comentario_data.evidencia_id,
            EvidenciaProyectoModel.proyecto_id == proyecto_id
        ).first()
        
        if not evidencia:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Evidencia no encontrada en este proyecto",
            )
        
        nuevo_comentario = ComentarioProyectoModel(
            proyecto_id=None,
            evidencia_id=comentario_data.evidencia_id,
            coordinador_id=current_user.id,
            contenido=comentario_data.contenido,
        )
    else:
        # Comentario sobre el proyecto general
        nuevo_comentario = ComentarioProyectoModel(
            proyecto_id=proyecto_id,
            evidencia_id=None,
            coordinador_id=current_user.id,
            contenido=comentario_data.contenido,
        )

    db.add(nuevo_comentario)
    db.commit()
    db.refresh(nuevo_comentario)
    db.refresh(nuevo_comentario, ["coordinador"])

    return nuevo_comentario


@router.get("/evidencias/{evidencia_id}/comentarios", response_model=List[ComentarioProyectoResponse])
def listar_comentarios_evidencia(
    evidencia_id: int,
    current_user: Annotated[UserModel, Depends(Auth.get_current_user)],
    db: Session = Depends(get_db),
):
    """
    Listar comentarios de una evidencia específica.
    """
    # Verificar que la evidencia existe
    evidencia = db.query(EvidenciaProyectoModel).filter(
        EvidenciaProyectoModel.id == evidencia_id
    ).first()
    
    if not evidencia:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evidencia no encontrada",
        )

    # Verificar permisos
    proyecto = db.query(ProyectoModel).filter(ProyectoModel.id == evidencia.proyecto_id).first()
    if current_user.rol == "docente" and proyecto.docente_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para ver los comentarios de esta evidencia",
        )

    comentarios = (
        db.query(ComentarioProyectoModel)
        .options(joinedload(ComentarioProyectoModel.coordinador))
        .filter(ComentarioProyectoModel.evidencia_id == evidencia_id)
        .order_by(ComentarioProyectoModel.created_at.desc())
        .all()
    )

    return comentarios


@router.patch("/comentarios/{comentario_id}", response_model=ComentarioProyectoResponse)
def actualizar_comentario_proyecto(
    comentario_id: int,
    comentario_data: ComentarioProyectoUpdate,
    current_user: Annotated[UserModel, Depends(Auth.get_current_user)],
    db: Session = Depends(get_db),
):
    """
    Actualizar un comentario.

    Solo el autor del comentario o el rector pueden actualizar.
    """
    comentario = (
        db.query(ComentarioProyectoModel)
        .filter(ComentarioProyectoModel.id == comentario_id)
        .first()
    )

    if not comentario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comentario no encontrado",
        )

    # Validar permisos
    es_autor = comentario.coordinador_id == current_user.id
    es_rector = current_user.rol == "rector"

    if not es_autor and not es_rector:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para actualizar este comentario",
        )

    comentario.contenido = comentario_data.contenido

    db.commit()
    db.refresh(comentario, ["coordinador"])

    return comentario


@router.delete("/comentarios/{comentario_id}")
def eliminar_comentario_proyecto(
    comentario_id: int,
    current_user: Annotated[UserModel, Depends(Auth.get_current_user)],
    db: Session = Depends(get_db),
):
    """
    Eliminar un comentario.

    Solo el autor del comentario o el rector pueden eliminar.
    """
    comentario = (
        db.query(ComentarioProyectoModel)
        .filter(ComentarioProyectoModel.id == comentario_id)
        .first()
    )

    if not comentario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comentario no encontrado",
        )

    # Validar permisos
    es_autor = comentario.coordinador_id == current_user.id
    es_rector = current_user.rol == "rector"

    if not es_autor and not es_rector:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para eliminar este comentario",
        )

    db.delete(comentario)
    db.commit()

    return {"mensaje": "Comentario eliminado correctamente"}
