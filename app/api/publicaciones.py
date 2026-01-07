from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session, joinedload
from app.database.config import get_db
from typing import Annotated, List, Optional
from app.models.user import User as UserModel
from app.models.publicaciones import Publicacion as PublicacionModel
from app.schemas.publicaciones import (
    PublicacionUpdate,
    PublicacionResponse,
)
from app.services.auth import Auth
from app.services.google_drive import drive_service


router = APIRouter(
    prefix="/publicaciones",
    tags=["publicaciones"],
)

# Roles permitidos para crear/editar/eliminar publicaciones
ROLES_PERMITIDOS = ["coordinador", "rector"]

# Tipos de archivo permitidos
ALLOWED_MIME_TYPES = {
    'application/pdf': 'pdf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'docx',
    'application/msword': 'doc',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': 'xlsx',
    'application/vnd.ms-excel': 'xls',
    'image/jpeg': 'jpg',
    'image/png': 'png',
}

# Tamaño máximo: 10 MB
MAX_FILE_SIZE = 10 * 1024 * 1024


@router.get("/", response_model=List[PublicacionResponse])
def listar_publicaciones(
    current_user: Annotated[UserModel, Depends(Auth.get_current_user)],
    db: Session = Depends(get_db),
):
    """
    Listar todas las publicaciones.
    Todos los usuarios autenticados pueden ver las publicaciones.
    Ordenadas por fecha de creación (más reciente primero).
    """
    publicaciones = (
        db.query(PublicacionModel)
        .options(joinedload(PublicacionModel.autor))
        .order_by(PublicacionModel.created_at.desc())
        .all()
    )
    return publicaciones


@router.get("/{publicacion_id}", response_model=PublicacionResponse)
def obtener_publicacion(
    publicacion_id: int,
    current_user: Annotated[UserModel, Depends(Auth.get_current_user)],
    db: Session = Depends(get_db),
):
    """
    Obtener una publicación por ID.
    Todos los usuarios autenticados pueden ver.
    """
    publicacion = (
        db.query(PublicacionModel)
        .options(joinedload(PublicacionModel.autor))
        .filter(PublicacionModel.id == publicacion_id)
        .first()
    )
    if not publicacion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Publicación no encontrada",
        )
    return publicacion


@router.post("/", response_model=PublicacionResponse, status_code=status.HTTP_201_CREATED)
async def crear_publicacion(
    current_user: Annotated[UserModel, Depends(Auth.get_current_user)],
    db: Session = Depends(get_db),
    titulo: str = Form(..., min_length=5, max_length=255, description="Título de la publicación"),
    contenido: str = Form(..., min_length=10, description="Contenido de la publicación"),
    archivo: Optional[UploadFile] = File(default=None, description="Archivo adjunto (opcional): PDF, DOCX, imágenes"),
):
    """
    Crear una nueva publicación con archivo adjunto opcional.
    
    - **titulo**: Título de la publicación (mínimo 5 caracteres)
    - **contenido**: Contenido/cuerpo de la publicación (mínimo 10 caracteres)
    - **archivo**: Archivo adjunto opcional (PDF, DOCX, DOC, XLSX, XLS, JPG, PNG)
    
    Solo coordinadores y rector pueden crear publicaciones.
    El archivo se sube automáticamente a Google Drive.
    """
    # Validar rol del usuario
    if current_user.rol not in ROLES_PERMITIDOS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo coordinadores y rector pueden crear publicaciones",
        )

    # Variables para datos del archivo
    drive_file_id = None
    drive_view_link = None
    drive_embed_link = None
    drive_download_link = None
    nombre_archivo_original = None
    tipo_archivo = None
    tamano_bytes = None

    # Procesar archivo si se envió
    if archivo and archivo.filename:
        # Verificar que Google Drive esté configurado
        if not drive_service.is_configured():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Google Drive no está configurado. Contacte al administrador."
            )
        
        # Validar tipo de archivo
        if archivo.content_type not in ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Tipo de archivo no permitido: {archivo.content_type}. "
                       f"Tipos permitidos: PDF, DOCX, DOC, XLSX, XLS, JPG, PNG"
            )
        
        # Leer contenido
        file_content = await archivo.read()
        
        # Validar tamaño
        if len(file_content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El archivo excede el tamaño máximo de {MAX_FILE_SIZE // (1024*1024)} MB"
            )
        
        # Validar que no esté vacío
        if len(file_content) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El archivo está vacío"
            )
        
        try:
            # Subir a Google Drive
            result = drive_service.upload_file(
                file_content=file_content,
                filename=archivo.filename,
                mime_type=archivo.content_type,
                subfolder="publicaciones"
            )
            
            # Guardar datos del archivo
            drive_file_id = result['file_id']
            drive_view_link = result['view_link']
            drive_embed_link = result['embed_link']
            drive_download_link = result['download_link']
            nombre_archivo_original = result['filename']
            tipo_archivo = ALLOWED_MIME_TYPES.get(archivo.content_type, 'otro')
            tamano_bytes = result['size_bytes']
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al subir archivo a Google Drive: {str(e)}"
            )

    # Crear la publicación
    nueva_publicacion = PublicacionModel(
        autor_id=current_user.id,
        titulo=titulo,
        contenido=contenido,
        drive_file_id=drive_file_id,
        drive_view_link=drive_view_link,
        drive_embed_link=drive_embed_link,
        drive_download_link=drive_download_link,
        nombre_archivo_original=nombre_archivo_original,
        tipo_archivo=tipo_archivo,
        tamano_bytes=tamano_bytes,
    )

    db.add(nueva_publicacion)
    db.commit()
    db.refresh(nueva_publicacion)

    # Cargar relación del autor para la respuesta
    db.refresh(nueva_publicacion, ["autor"])

    return nueva_publicacion


@router.patch("/{publicacion_id}", response_model=PublicacionResponse)
async def actualizar_publicacion(
    publicacion_id: int,
    current_user: Annotated[UserModel, Depends(Auth.get_current_user)],
    db: Session = Depends(get_db),
    titulo: Optional[str] = Form(default=None, min_length=5, max_length=255),
    contenido: Optional[str] = Form(default=None, min_length=10),
    archivo: Optional[UploadFile] = File(default=None, description="Nuevo archivo (reemplaza el anterior)"),
    eliminar_archivo: bool = Form(default=False, description="Eliminar archivo adjunto actual"),
):
    """
    Actualizar una publicación existente.
    
    - **titulo**: Nuevo título (opcional)
    - **contenido**: Nuevo contenido (opcional)
    - **archivo**: Nuevo archivo adjunto (reemplaza el anterior si existe)
    - **eliminar_archivo**: True para eliminar el archivo sin reemplazarlo
    
    Solo el autor de la publicación puede actualizarla.
    """
    publicacion_db = (
        db.query(PublicacionModel)
        .filter(PublicacionModel.id == publicacion_id)
        .first()
    )

    if not publicacion_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Publicación no encontrada",
        )

    # Validar que el usuario sea el autor
    if publicacion_db.autor_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo el autor puede actualizar esta publicación",
        )

    # Actualizar título si se proporciona
    if titulo is not None:
        publicacion_db.titulo = titulo
    
    # Actualizar contenido si se proporciona
    if contenido is not None:
        publicacion_db.contenido = contenido

    # Manejar eliminación de archivo
    if eliminar_archivo and publicacion_db.drive_file_id:
        try:
            if drive_service.is_configured():
                drive_service.delete_file(publicacion_db.drive_file_id)
        except Exception:
            pass  # Si falla la eliminación en Drive, continuar
        
        # Limpiar campos de archivo en la base de datos
        publicacion_db.drive_file_id = None
        publicacion_db.drive_view_link = None
        publicacion_db.drive_embed_link = None
        publicacion_db.drive_download_link = None
        publicacion_db.nombre_archivo_original = None
        publicacion_db.tipo_archivo = None
        publicacion_db.tamano_bytes = None

    # Manejar nuevo archivo (reemplaza el anterior)
    if archivo and archivo.filename:
        if not drive_service.is_configured():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Google Drive no está configurado"
            )
        
        if archivo.content_type not in ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Tipo de archivo no permitido: {archivo.content_type}"
            )
        
        file_content = await archivo.read()
        
        if len(file_content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El archivo excede el tamaño máximo de {MAX_FILE_SIZE // (1024*1024)} MB"
            )
        
        # Eliminar archivo anterior si existe
        if publicacion_db.drive_file_id:
            try:
                drive_service.delete_file(publicacion_db.drive_file_id)
            except Exception:
                pass
        
        try:
            result = drive_service.upload_file(
                file_content=file_content,
                filename=archivo.filename,
                mime_type=archivo.content_type,
                subfolder="publicaciones"
            )
            
            publicacion_db.drive_file_id = result['file_id']
            publicacion_db.drive_view_link = result['view_link']
            publicacion_db.drive_embed_link = result['embed_link']
            publicacion_db.drive_download_link = result['download_link']
            publicacion_db.nombre_archivo_original = result['filename']
            publicacion_db.tipo_archivo = ALLOWED_MIME_TYPES.get(archivo.content_type, 'otro')
            publicacion_db.tamano_bytes = result['size_bytes']
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al subir archivo: {str(e)}"
            )

    db.commit()
    db.refresh(publicacion_db, ["autor"])

    return publicacion_db


@router.delete("/{publicacion_id}")
def eliminar_publicacion(
    publicacion_id: int,
    current_user: Annotated[UserModel, Depends(Auth.get_current_user)],
    db: Session = Depends(get_db),
):
    """
    Eliminar una publicación.
    También elimina el archivo de Google Drive si existe.
    Solo el autor de la publicación puede eliminarla.
    """
    publicacion_db = (
        db.query(PublicacionModel)
        .filter(PublicacionModel.id == publicacion_id)
        .first()
    )

    if not publicacion_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Publicación no encontrada",
        )

    # Validar que el usuario sea el autor
    if publicacion_db.autor_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo el autor puede eliminar esta publicación",
        )

    # Eliminar archivo de Google Drive si existe
    if publicacion_db.drive_file_id and drive_service.is_configured():
        try:
            drive_service.delete_file(publicacion_db.drive_file_id)
        except Exception:
            pass  # Continuar aunque falle

    db.delete(publicacion_db)
    db.commit()

    return {"mensaje": "Publicación eliminada correctamente"}

