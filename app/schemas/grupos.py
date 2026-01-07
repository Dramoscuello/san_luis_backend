from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.grados import GradoResponse


class GrupoBase(BaseModel):
    """Campos comunes para grupos."""
    nombre: str = Field(..., min_length=1, max_length=50)
    codigo: Optional[str] = Field(None, max_length=20)


class GrupoCreate(GrupoBase):
    """Schema para crear un grupo."""
    grado_id: int


class GrupoUpdate(BaseModel):
    """Schema para actualizar un grupo."""
    nombre: Optional[str] = Field(None, min_length=1, max_length=50)
    codigo: Optional[str] = Field(None, max_length=20)
    grado_id: Optional[int] = None

    class Config:
        from_attributes = True


class GrupoResponse(BaseModel):
    """Schema de respuesta para grupos."""
    id: int
    grado_id: int
    nombre: str
    codigo: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    cantidad_estudiantes: int = 0
    
    # Campo anidado opcional
    grado: Optional[GradoResponse] = None

    class Config:
        from_attributes = True


class AsignarDirectorRequest(BaseModel):
    """Schema para asignar un director de grupo."""
    docente_id: int
