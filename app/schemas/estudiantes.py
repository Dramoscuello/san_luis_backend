from datetime import datetime, date
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
    # Campos originales
    numero_documento: Optional[str] = Field(None, min_length=5, max_length=20)
    nombres: Optional[str] = Field(None, min_length=2, max_length=150)
    apellidos: Optional[str] = Field(None, min_length=2, max_length=150)
    grupo_id: Optional[int] = None
    
    # Datos personales opcionales
    fecha_nacimiento: Optional[date] = None
    lugar_nacimiento: Optional[str] = Field(None, max_length=150)
    tipo_documento: Optional[str] = Field(None, max_length=50)
    rh: Optional[str] = Field(None, max_length=10)
    eps: Optional[str] = Field(None, max_length=100)
    
    # Datos del padre
    nombre_padre: Optional[str] = Field(None, max_length=200)
    ocupacion_padre: Optional[str] = Field(None, max_length=100)
    celular_padre: Optional[str] = Field(None, max_length=20)
    
    # Datos de la madre
    nombre_madre: Optional[str] = Field(None, max_length=200)
    ocupacion_madre: Optional[str] = Field(None, max_length=100)
    celular_madre: Optional[str] = Field(None, max_length=20)
    
    # Datos del acudiente
    nombre_acudiente: Optional[str] = Field(None, max_length=200)
    celular_acudiente: Optional[str] = Field(None, max_length=20)

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
    
    # Datos personales opcionales
    fecha_nacimiento: Optional[date] = None
    lugar_nacimiento: Optional[str] = None
    tipo_documento: Optional[str] = None
    rh: Optional[str] = None
    eps: Optional[str] = None
    
    # Datos del padre
    nombre_padre: Optional[str] = None
    ocupacion_padre: Optional[str] = None
    celular_padre: Optional[str] = None
    
    # Datos de la madre
    nombre_madre: Optional[str] = None
    ocupacion_madre: Optional[str] = None
    celular_madre: Optional[str] = None
    
    # Datos del acudiente
    nombre_acudiente: Optional[str] = None
    celular_acudiente: Optional[str] = None
    
    created_at: datetime
    updated_at: datetime
    
    # Campo anidado opcional
    grupo: Optional[GrupoSimpleResponse] = None

    class Config:
        from_attributes = True
