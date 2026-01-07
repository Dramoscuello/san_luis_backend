from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class PublicacionBase(BaseModel):
    """Campos comunes para publicaciones."""
    titulo: str = Field(..., min_length=5, max_length=255)
    contenido: str = Field(..., min_length=10)


class PublicacionCreate(PublicacionBase):
    """Schema para crear una publicación."""
    # Documento adjunto OPCIONAL
    drive_file_id: Optional[str] = None
    drive_view_link: Optional[str] = None
    drive_embed_link: Optional[str] = None
    drive_download_link: Optional[str] = None
    nombre_archivo_original: Optional[str] = None
    tipo_archivo: Optional[str] = None
    tamano_bytes: Optional[int] = None


class PublicacionUpdate(BaseModel):
    """Schema para actualizar una publicación (todos los campos opcionales)."""
    titulo: Optional[str] = Field(None, min_length=5, max_length=255)
    contenido: Optional[str] = Field(None, min_length=10)
    drive_file_id: Optional[str] = None
    drive_view_link: Optional[str] = None
    drive_embed_link: Optional[str] = None
    drive_download_link: Optional[str] = None
    nombre_archivo_original: Optional[str] = None
    tipo_archivo: Optional[str] = None
    tamano_bytes: Optional[int] = None

    class Config:
        from_attributes = True


class AutorResponse(BaseModel):
    """Schema para mostrar datos básicos del autor."""
    id: int
    nombre_completo: str
    rol: str

    class Config:
        from_attributes = True


class PublicacionResponse(BaseModel):
    """Schema de respuesta para publicaciones."""
    id: int
    autor_id: int
    titulo: str
    contenido: str
    drive_file_id: Optional[str] = None
    drive_view_link: Optional[str] = None
    drive_embed_link: Optional[str] = None
    drive_download_link: Optional[str] = None
    nombre_archivo_original: Optional[str] = None
    tipo_archivo: Optional[str] = None
    tamano_bytes: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    autor: Optional[AutorResponse] = None

    class Config:
        from_attributes = True
