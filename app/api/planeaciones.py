from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from sqlalchemy.orm import Session, joinedload
from app.database.config import get_db
from typing import Annotated, List, Optional
from app.models.user import User as UserModel
from app.models.planeaciones import Planeacion as PlaneacionModel
from app.models.asignaturas import Asignatura as AsignaturaModel
from app.models.sedes import Sedes as SedeModel
from app.models.periodos import Periodo as PeriodoModel
from app.schemas.planeaciones import (
    PlaneacionResponse,
    PlaneacionListResponse,
    PlaneacionUpdate,
)
from app.services.auth import Auth
from app.services.google_drive import drive_service


router = APIRouter(
    prefix="/planeaciones",
    tags=["planeaciones"],
)

# Tipos de archivo permitidos para planeaciones
ALLOWED_MIME_TYPES = {
    'application/pdf': 'pdf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'docx',
    'application/msword': 'doc',
}

# Tamaño máximo: 10 MB
MAX_FILE_SIZE = 10 * 1024 * 1024


@router.get("/", response_model=List[PlaneacionListResponse])
def listar_planeaciones(
    current_user: Annotated[UserModel, Depends(Auth.get_current_user)],
    db: Session = Depends(get_db),
    docente_id: Optional[int] = Query(None, description="Filtrar por docente (solo coordinadores/rector)"),
    asignatura_id: Optional[int] = Query(None, description="Filtrar por asignatura"),
    sede_id: Optional[int] = Query(None, description="Filtrar por sede"),
    periodo_id: Optional[int] = Query(None, description="Filtrar por período"),
):
    """
    Listar planeaciones con filtros opcionales.

    - **Docentes:** Solo ven sus propias planeaciones
    - **Coordinadores/Rector:** Ven todas las planeaciones de todos los docentes

    Filtros disponibles (según rol):
    - docente_id: Solo para coordinadores/rector
    - asignatura_id, sede_id, periodo_id: Disponibles para todos
    """
    query = (
        db.query(PlaneacionModel)
        .options(
            joinedload(PlaneacionModel.docente),
            joinedload(PlaneacionModel.asignatura),
            joinedload(PlaneacionModel.periodo),
        )
    )

    # Restricción por rol: docentes solo ven sus propias planeaciones
    if current_user.rol == "docente":
        query = query.filter(PlaneacionModel.docente_id == current_user.id)
        # Ignorar el filtro docente_id si es docente (no puede ver planeaciones de otros)
    else:
        # Coordinadores y rector pueden filtrar por docente
        if docente_id:
            query = query.filter(PlaneacionModel.docente_id == docente_id)

    # Aplicar filtros comunes
    if asignatura_id:
        query = query.filter(PlaneacionModel.asignatura_id == asignatura_id)
    if sede_id:
        query = query.filter(PlaneacionModel.sede_id == sede_id)
    if periodo_id:
        query = query.filter(PlaneacionModel.periodo_id == periodo_id)

    planeaciones = query.order_by(PlaneacionModel.fecha_subida.desc()).all()
    return planeaciones


@router.get("/mis-planeaciones", response_model=List[PlaneacionListResponse])
def listar_mis_planeaciones(
    current_user: Annotated[UserModel, Depends(Auth.get_current_user)],
    db: Session = Depends(get_db),
    periodo_id: Optional[int] = Query(None, description="Filtrar por período"),
):
    """
    Listar las planeaciones del docente autenticado.
    Solo para docentes.
    """
    if current_user.rol != "docente":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Este endpoint es solo para docentes",
        )

    query = (
        db.query(PlaneacionModel)
        .options(
            joinedload(PlaneacionModel.docente),
            joinedload(PlaneacionModel.asignatura),
            joinedload(PlaneacionModel.periodo),
        )
        .filter(PlaneacionModel.docente_id == current_user.id)
    )

    if periodo_id:
        query = query.filter(PlaneacionModel.periodo_id == periodo_id)

    planeaciones = query.order_by(PlaneacionModel.fecha_subida.desc()).all()
    return planeaciones


@router.get("/{planeacion_id}", response_model=PlaneacionResponse)
def obtener_planeacion(
    planeacion_id: int,
    current_user: Annotated[UserModel, Depends(Auth.get_current_user)],
    db: Session = Depends(get_db),
):
    """
    Obtener una planeación por ID con todos sus detalles.
    Todos los usuarios autenticados pueden ver.
    """
    planeacion = (
        db.query(PlaneacionModel)
        .options(
            joinedload(PlaneacionModel.docente),
            joinedload(PlaneacionModel.asignatura),
            joinedload(PlaneacionModel.sede),
            joinedload(PlaneacionModel.periodo),
        )
        .filter(PlaneacionModel.id == planeacion_id)
        .first()
    )

    if not planeacion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Planeación no encontrada",
        )

    return planeacion


@router.post("/", response_model=PlaneacionResponse, status_code=status.HTTP_201_CREATED)
async def crear_planeacion(
    current_user: Annotated[UserModel, Depends(Auth.get_current_user)],
    db: Session = Depends(get_db),
    archivo: UploadFile = File(..., description="Archivo de planeación (PDF o DOCX)"),
    asignatura_id: int = Form(..., description="ID de la asignatura"),
    titulo: str = Form(..., min_length=5, max_length=255, description="Título de la planeación"),
):
    """
    Crear una nueva planeación subiendo un archivo.

    - **archivo**: Archivo PDF o DOCX (obligatorio, máximo 10 MB)
    - **asignatura_id**: ID de la asignatura (obligatorio)
    - **titulo**: Título de la planeación (obligatorio, mínimo 5 caracteres)

    Solo docentes pueden crear planeaciones.
    La sede se toma automáticamente de la sede del docente.
    El período se asigna automáticamente según el período activo.
    El archivo se sube a Google Drive.
    """
    # Validar que sea docente
    if current_user.rol != "docente":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los docentes pueden subir planeaciones",
        )

    # Validar que el docente tenga sede asignada
    if not current_user.sede_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El docente no tiene sede asignada. Contacte al coordinador.",
        )

    # Verificar que la asignatura existe
    asignatura = db.query(AsignaturaModel).filter(AsignaturaModel.id == asignatura_id).first()
    if not asignatura:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asignatura no encontrada",
        )

    # Obtener el período activo automáticamente
    periodo = db.query(PeriodoModel).filter(PeriodoModel.activo == True).first()
    if not periodo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No hay un período académico activo. Contacte al coordinador.",
        )

    # Verificar que Google Drive está configurado
    if not drive_service.is_configured():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google Drive no está configurado. Contacte al administrador.",
        )

    # Validar tipo de archivo
    if archivo.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tipo de archivo no permitido: {archivo.content_type}. Solo se permiten PDF y DOCX.",
        )

    # Leer contenido del archivo
    file_content = await archivo.read()

    # Validar tamaño
    if len(file_content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El archivo excede el tamaño máximo de {MAX_FILE_SIZE // (1024*1024)} MB",
        )

    # Validar que no esté vacío
    if len(file_content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El archivo está vacío",
        )

    try:
        # Subir a Google Drive
        result = drive_service.upload_file(
            file_content=file_content,
            filename=archivo.filename,
            mime_type=archivo.content_type,
            subfolder="planeaciones"
        )

        # Crear la planeación
        nueva_planeacion = PlaneacionModel(
            docente_id=current_user.id,
            asignatura_id=asignatura_id,
            sede_id=current_user.sede_id,
            periodo_id=periodo.id,
            titulo=titulo,
            nombre_archivo_original=result['filename'],
            drive_file_id=result['file_id'],
            drive_view_link=result['view_link'],
            drive_embed_link=result['embed_link'],
            drive_download_link=result['download_link'],
            tamano_bytes=result['size_bytes'],
            tipo_archivo=ALLOWED_MIME_TYPES.get(archivo.content_type, 'pdf'),
        )

        db.add(nueva_planeacion)
        db.commit()
        db.refresh(nueva_planeacion)

        # Cargar relaciones para la respuesta
        db.refresh(nueva_planeacion, ["docente", "asignatura", "sede", "periodo"])

        return nueva_planeacion

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al subir archivo a Google Drive: {str(e)}",
        )


@router.patch("/{planeacion_id}", response_model=PlaneacionResponse)
async def actualizar_planeacion(
    planeacion_id: int,
    current_user: Annotated[UserModel, Depends(Auth.get_current_user)],
    db: Session = Depends(get_db),
    titulo: Optional[str] = Form(None, max_length=255),
    asignatura_id: Optional[int] = Form(None),
    periodo_id: Optional[int] = Form(None),
    archivo: Optional[UploadFile] = File(None, description="Nuevo archivo (reemplaza el anterior)"),
):
    """
    Actualizar una planeación existente.

    - **titulo**: Nuevo título (opcional)
    - **asignatura_id**: Nueva asignatura (opcional)
    - **periodo_id**: Nuevo período (opcional)
    - **archivo**: Nuevo archivo que reemplaza el anterior (opcional)

    Solo el docente dueño de la planeación puede actualizarla.
    """
    planeacion_db = (
        db.query(PlaneacionModel)
        .filter(PlaneacionModel.id == planeacion_id)
        .first()
    )

    if not planeacion_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Planeación no encontrada",
        )

    # Validar que el usuario sea el dueño
    if planeacion_db.docente_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo el docente dueño puede actualizar esta planeación",
        )

    # Actualizar campos si se proporcionan
    if titulo is not None:
        planeacion_db.titulo = titulo

    if asignatura_id is not None:
        asignatura = db.query(AsignaturaModel).filter(AsignaturaModel.id == asignatura_id).first()
        if not asignatura:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Asignatura no encontrada",
            )
        planeacion_db.asignatura_id = asignatura_id

    if periodo_id is not None:
        periodo = db.query(PeriodoModel).filter(PeriodoModel.id == periodo_id).first()
        if not periodo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Período no encontrado",
            )
        planeacion_db.periodo_id = periodo_id

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

        # Eliminar archivo anterior de Google Drive
        if planeacion_db.drive_file_id:
            try:
                drive_service.delete_file(planeacion_db.drive_file_id)
            except Exception:
                pass  # Continuar aunque falle

        try:
            result = drive_service.upload_file(
                file_content=file_content,
                filename=archivo.filename,
                mime_type=archivo.content_type,
                subfolder="planeaciones"
            )

            planeacion_db.nombre_archivo_original = result['filename']
            planeacion_db.drive_file_id = result['file_id']
            planeacion_db.drive_view_link = result['view_link']
            planeacion_db.drive_embed_link = result['embed_link']
            planeacion_db.drive_download_link = result['download_link']
            planeacion_db.tamano_bytes = result['size_bytes']
            planeacion_db.tipo_archivo = ALLOWED_MIME_TYPES.get(archivo.content_type, 'pdf')

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al subir archivo: {str(e)}",
            )

    db.commit()
    db.refresh(planeacion_db, ["docente", "asignatura", "sede", "periodo"])

    return planeacion_db


@router.delete("/{planeacion_id}")
def eliminar_planeacion(
    planeacion_id: int,
    current_user: Annotated[UserModel, Depends(Auth.get_current_user)],
    db: Session = Depends(get_db),
):
    """
    Eliminar una planeación.
    También elimina el archivo de Google Drive.

    - **Docentes:** Solo pueden eliminar sus propias planeaciones
    - **Coordinadores/Rector:** Pueden eliminar cualquier planeación
    """
    planeacion_db = (
        db.query(PlaneacionModel)
        .filter(PlaneacionModel.id == planeacion_id)
        .first()
    )

    if not planeacion_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Planeación no encontrada",
        )

    # Validar permisos
    es_dueno = planeacion_db.docente_id == current_user.id
    es_admin = current_user.rol in ["coordinador", "rector"]

    if not es_dueno and not es_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para eliminar esta planeación",
        )

    # Eliminar archivo de Google Drive
    if planeacion_db.drive_file_id and drive_service.is_configured():
        try:
            drive_service.delete_file(planeacion_db.drive_file_id)
        except Exception:
            pass  # Continuar aunque falle

    db.delete(planeacion_db)
    db.commit()

    return {"mensaje": "Planeación eliminada correctamente"}
