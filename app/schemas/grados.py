from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.sedes import SedesResponse


class GradoBase(BaseModel):
    """Campos comunes para grados."""
    nombre: str = Field(..., min_length=1, max_length=50)
    codigo: Optional[str] = Field(None, max_length=20)


class GradoCreate(GradoBase):
    """Schema para crear un grado."""
    sede_id: int


class GradoUpdate(BaseModel):
    """Schema para actualizar un grado."""
    nombre: Optional[str] = Field(None, min_length=1, max_length=50)
    codigo: Optional[str] = Field(None, max_length=20)
    sede_id: Optional[int] = None

    class Config:
        from_attributes = True


class GradoResponse(BaseModel):
    """Schema de respuesta para grados."""
    id: int
    sede_id: int
    nombre: str
    codigo: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    # Campo anidado opcional
    sede: Optional[SedesResponse] = None

    class Config:
        from_attributes = True
