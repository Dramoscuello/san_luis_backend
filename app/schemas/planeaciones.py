from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class DocenteBasico(BaseModel):
    """Datos básicos del docente para mostrar en respuestas."""
    id: int
    nombre_completo: str
    email: str

    class Config:
        from_attributes = True


class AsignaturaBasica(BaseModel):
    """Datos básicos de la asignatura para mostrar en respuestas."""
    id: int
    nombre: str
    codigo: Optional[str] = None

    class Config:
        from_attributes = True


class SedeBasica(BaseModel):
    """Datos básicos de la sede para mostrar en respuestas."""
    id: int
    nombre: str
    codigo: Optional[str] = None

    class Config:
        from_attributes = True


class PeriodoBasico(BaseModel):
    """Datos básicos del período para mostrar en respuestas."""
    id: int
    nombre: str
    activo: bool

    class Config:
        from_attributes = True


class PlaneacionBase(BaseModel):
    """Campos comunes para planeaciones."""
    titulo: str = Field(..., min_length=5, max_length=255)
    asignatura_id: int
    sede_id: int
    periodo_id: int


class PlaneacionCreate(PlaneacionBase):
    """
    Schema para crear una planeación.
    El archivo se envía como UploadFile en el endpoint.
    """
    pass


class PlaneacionUpdate(BaseModel):
    """Schema para actualizar una planeación (todos los campos opcionales)."""
    titulo: Optional[str] = Field(None, max_length=255)
    asignatura_id: Optional[int] = None
    periodo_id: Optional[int] = None

    class Config:
        from_attributes = True


class PlaneacionResponse(BaseModel):
    """Schema de respuesta para planeaciones."""
    id: int
    docente_id: int
    asignatura_id: int
    sede_id: int
    periodo_id: int
    titulo: str
    nombre_archivo_original: str
    drive_file_id: str
    drive_view_link: Optional[str] = None
    drive_embed_link: Optional[str] = None
    drive_download_link: Optional[str] = None
    tamano_bytes: Optional[int] = None
    tipo_archivo: Optional[str] = None
    fecha_subida: datetime
    created_at: datetime
    updated_at: datetime

    # Relaciones
    docente: Optional[DocenteBasico] = None
    asignatura: Optional[AsignaturaBasica] = None
    sede: Optional[SedeBasica] = None
    periodo: Optional[PeriodoBasico] = None

    class Config:
        from_attributes = True


class PlaneacionListResponse(BaseModel):
    """Schema simplificado para listados de planeaciones."""
    id: int
    titulo: str
    nombre_archivo_original: str
    tipo_archivo: Optional[str] = None
    fecha_subida: datetime
    drive_view_link: Optional[str] = None
    sede_id: int

    docente: Optional[DocenteBasico] = None
    asignatura: Optional[AsignaturaBasica] = None
    periodo: Optional[PeriodoBasico] = None

    class Config:
        from_attributes = True
