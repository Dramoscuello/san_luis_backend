from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class CoordinadorBasico(BaseModel):
    """Datos básicos del coordinador que destacó la planeación."""
    id: int
    nombre_completo: str
    rol: str

    class Config:
        from_attributes = True


class PlaneacionBasicaDestacada(BaseModel):
    """Datos básicos de la planeación destacada."""
    id: int
    titulo: Optional[str] = None
    nombre_archivo_original: str
    drive_view_link: Optional[str] = None
    docente_nombre: Optional[str] = None
    asignatura_nombre: Optional[str] = None

    class Config:
        from_attributes = True


class PlaneacionDestacadaCreate(BaseModel):
    """Schema para destacar una planeación."""
    planeacion_id: int
    razon: str = Field(..., min_length=20, description="Razón por la cual se destaca (mínimo 20 caracteres)")


class PlaneacionDestacadaUpdate(BaseModel):
    """Schema para actualizar una planeación destacada (solo coordinador/rector)."""
    razon: Optional[str] = Field(None, min_length=20, description="Nueva razón")
    activa: Optional[bool] = None

    class Config:
        from_attributes = True


class PlaneacionDestacadaResponse(BaseModel):
    """Schema de respuesta para planeaciones destacadas."""
    id: int
    planeacion_id: int
    coordinador_id: int
    razon: str
    activa: bool
    visualizaciones: int
    fecha_destacado: datetime
    created_at: datetime

    # Relaciones
    coordinador: Optional[CoordinadorBasico] = None

    class Config:
        from_attributes = True


class PlaneacionDestacadaConDetalle(PlaneacionDestacadaResponse):
    """Schema de respuesta con detalle completo de la planeación."""
    planeacion_titulo: Optional[str] = None
    planeacion_archivo: Optional[str] = None
    planeacion_drive_view_link: Optional[str] = None
    docente_nombre: Optional[str] = None
    asignatura_nombre: Optional[str] = None
    sede_nombre: Optional[str] = None

    class Config:
        from_attributes = True
