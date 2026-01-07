from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class EstudianteBase(BaseModel):
    """Campos comunes para estudiantes."""
    numero_documento: str = Field(..., min_length=5, max_length=20)
    nombres: str = Field(..., min_length=2, max_length=150)
    apellidos: str = Field(..., min_length=2, max_length=150)


class EstudianteCreate(EstudianteBase):
    """Schema para crear un estudiante."""
    grupo_id: int


class EstudianteUpdate(BaseModel):
    """Schema para actualizar un estudiante."""
    numero_documento: Optional[str] = Field(None, min_length=5, max_length=20)
    nombres: Optional[str] = Field(None, min_length=2, max_length=150)
    apellidos: Optional[str] = Field(None, min_length=2, max_length=150)
    grupo_id: Optional[int] = None

    class Config:
        from_attributes = True


class GrupoSimpleResponse(BaseModel):
    """Schema simple de respuesta para grupos (sin anidamiento profundo)."""
    id: int
    nombre: str
    codigo: Optional[str] = None

    class Config:
        from_attributes = True


class EstudianteResponse(BaseModel):
    """Schema de respuesta para estudiantes."""
    id: int
    grupo_id: int
    numero_documento: str
    nombres: str
    apellidos: str
    created_at: datetime
    updated_at: datetime
    
    # Campo anidado opcional
    grupo: Optional[GrupoSimpleResponse] = None

    class Config:
        from_attributes = True
