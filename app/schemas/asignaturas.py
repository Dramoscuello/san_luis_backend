from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.areas import AreaResponse


class AsignaturaBase(BaseModel):
    """Campos comunes para asignaturas."""
    nombre: str = Field(..., min_length=2, max_length=100)
    codigo: Optional[str] = Field(None, max_length=20)
    descripcion: Optional[str] = None
    grados: Optional[str] = Field(None, max_length=100, description="Lista separada por comas, ej: '6,7,8'")


class AsignaturaCreate(AsignaturaBase):
    """Schema para crear una asignatura."""
    area_id: int
    activa: bool = True


class AsignaturaUpdate(BaseModel):
    """Schema para actualizar una asignatura (todos los campos opcionales)."""
    nombre: Optional[str] = Field(None, min_length=2, max_length=100)
    area_id: Optional[int] = None
    codigo: Optional[str] = Field(None, max_length=20)
    descripcion: Optional[str] = None
    grados: Optional[str] = Field(None, max_length=100)
    activa: Optional[bool] = None

    class Config:
        from_attributes = True


class AsignaturaResponse(BaseModel):
    """Schema de respuesta para asignaturas."""
    id: int
    nombre: str
    area_id: int
    codigo: Optional[str] = None
    descripcion: Optional[str] = None
    grados: Optional[str] = None
    activa: bool
    created_at: datetime
    updated_at: datetime
    cantidad_docentes: int = 0
    
    # Relación anidada (opcional, se carga si se solicita)
    area: Optional[AreaResponse] = None

    class Config:
        from_attributes = True


class AsignarDocenteRequest(BaseModel):
    """Schema para asignar un docente a una asignatura."""
    docente_id: int
