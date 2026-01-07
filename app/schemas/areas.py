from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class AreaBase(BaseModel):
    """Campos comunes para áreas."""
    nombre: str = Field(..., min_length=2, max_length=100)
    descripcion: Optional[str] = None


class AreaCreate(AreaBase):
    """Schema para crear un área."""
    activa: bool = True


class AreaUpdate(BaseModel):
    """Schema para actualizar un área (todos los campos opcionales)."""
    nombre: Optional[str] = Field(None, min_length=2, max_length=100)
    descripcion: Optional[str] = None
    activa: Optional[bool] = None

    class Config:
        from_attributes = True


class AreaResponse(BaseModel):
    """Schema de respuesta para áreas."""
    id: int
    nombre: str
    descripcion: Optional[str] = None
    activa: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
