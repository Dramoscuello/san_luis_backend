from datetime import datetime, date
from typing import Optional, List

from pydantic import BaseModel, Field


class DocenteBasico(BaseModel):
    """Datos básicos del docente."""
    id: int
    nombre_completo: str
    email: str

    class Config:
        from_attributes = True


# ==================== PROYECTO ====================

class ProyectoCreate(BaseModel):
    """Schema para crear un proyecto."""
    titulo: str = Field(..., min_length=5, max_length=255, description="Título del proyecto")
    descripcion: str = Field(..., min_length=20, description="Descripción del proyecto")
    objetivos: Optional[str] = Field(None, description="Objetivos del proyecto")
    fecha_inicio: date = Field(..., description="Fecha de inicio del proyecto")
    fecha_fin_estimada: Optional[date] = Field(None, description="Fecha de fin estimada")


class ProyectoUpdate(BaseModel):
    """Schema para actualizar un proyecto."""
    titulo: Optional[str] = Field(None, min_length=5, max_length=255)
    descripcion: Optional[str] = Field(None, min_length=20)
    objetivos: Optional[str] = None
    fecha_inicio: Optional[date] = None
    fecha_fin_estimada: Optional[date] = None
    estado: Optional[str] = Field(None, pattern="^(activo|pausado|completado|cancelado)$")

    class Config:
        from_attributes = True


class ProyectoResponse(BaseModel):
    """Schema de respuesta para proyectos."""
    id: int
    docente_id: int
    titulo: str
    descripcion: str
    objetivos: Optional[str] = None
    fecha_inicio: date
    fecha_fin_estimada: Optional[date] = None
    
    # Documento base (opcional)
    drive_file_id: Optional[str] = None
    drive_view_link: Optional[str] = None
    drive_embed_link: Optional[str] = None
    drive_download_link: Optional[str] = None
    nombre_archivo_original: Optional[str] = None
    
    estado: str
    created_at: datetime
    updated_at: datetime

    # Relaciones
    docente: Optional[DocenteBasico] = None

    class Config:
        from_attributes = True


class ProyectoListResponse(BaseModel):
    """Schema de respuesta para listar proyectos (resumido)."""
    id: int
    docente_id: int
    titulo: str
    descripcion: str
    fecha_inicio: date
    fecha_fin_estimada: Optional[date] = None
    estado: str
    nombre_archivo_original: Optional[str] = None
    created_at: datetime

    # Relaciones
    docente: Optional[DocenteBasico] = None

    class Config:
        from_attributes = True


# ==================== EVIDENCIA PROYECTO ====================

class EvidenciaProyectoCreate(BaseModel):
    """Schema para crear una evidencia (el archivo se envía como Form)."""
    titulo: str = Field(..., min_length=5, max_length=255, description="Título de la evidencia")
    descripcion: Optional[str] = Field(None, description="Descripción de la evidencia")
    fecha_evidencia: date = Field(..., description="Fecha del avance/evidencia")


class EvidenciaProyectoResponse(BaseModel):
    """Schema de respuesta para evidencias de proyecto."""
    id: int
    proyecto_id: int
    titulo: str
    descripcion: Optional[str] = None
    fecha_evidencia: date

    # Google Drive
    drive_file_id: str
    drive_view_link: Optional[str] = None
    drive_embed_link: Optional[str] = None
    drive_download_link: Optional[str] = None
    nombre_archivo_original: Optional[str] = None
    tipo_archivo: Optional[str] = None
    tamano_bytes: Optional[int] = None

    subido_por: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== COMENTARIO PROYECTO ====================

class ComentarioProyectoCreate(BaseModel):
    """Schema para crear un comentario sobre proyecto o evidencia."""
    proyecto_id: Optional[int] = Field(None, description="ID del proyecto (si es comentario general)")
    evidencia_id: Optional[int] = Field(None, description="ID de la evidencia (si es comentario sobre evidencia)")
    contenido: str = Field(..., min_length=10, description="Contenido del comentario")


class CoordinadorBasico(BaseModel):
    """Datos básicos del coordinador que comenta."""
    id: int
    nombre_completo: str
    rol: str

    class Config:
        from_attributes = True


class ComentarioProyectoResponse(BaseModel):
    """Schema de respuesta para comentarios de proyecto."""
    id: int
    proyecto_id: Optional[int] = None
    evidencia_id: Optional[int] = None
    coordinador_id: int
    contenido: str
    created_at: datetime

    # Relaciones
    coordinador: Optional[CoordinadorBasico] = None

    class Config:
        from_attributes = True


class ComentarioProyectoUpdate(BaseModel):
    """Schema para actualizar un comentario."""
    contenido: str = Field(..., min_length=10, description="Nuevo contenido del comentario")

    class Config:
        from_attributes = True
