from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class CoordinadorBasico(BaseModel):
    """Datos básicos del coordinador para mostrar en respuestas."""
    id: int
    nombre_completo: str
    rol: str

    class Config:
        from_attributes = True


class ComentarioCreate(BaseModel):
    """Schema para crear un comentario sobre una planeación."""
    planeacion_id: int
    contenido: str = Field(..., min_length=10, description="Contenido del comentario (mínimo 10 caracteres)")


class ComentarioUpdate(BaseModel):
    """Schema para actualizar un comentario."""
    contenido: str = Field(..., min_length=10, description="Nuevo contenido del comentario")

    class Config:
        from_attributes = True


class ComentarioResponse(BaseModel):
    """Schema de respuesta para comentarios."""
    id: int
    planeacion_id: int
    coordinador_id: int
    contenido: str
    created_at: datetime

    # Relación
    coordinador: Optional[CoordinadorBasico] = None

    class Config:
        from_attributes = True


class ComentarioConPlaneacion(ComentarioResponse):
    """Schema de comentario con información básica de la planeación."""
    planeacion_titulo: Optional[str] = None
    planeacion_docente: Optional[str] = None

    class Config:
        from_attributes = True
