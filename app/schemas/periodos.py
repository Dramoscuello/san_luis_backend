from datetime import datetime, date
from typing import Optional

from pydantic import BaseModel


class PeriodoUpdate(BaseModel):
    """Schema para actualizar un período (activar/desactivar, fechas)."""
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None
    activo: Optional[bool] = None

    class Config:
        from_attributes = True


class PeriodoResponse(BaseModel):
    """Schema de respuesta para períodos."""
    id: int
    nombre: str
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None
    activo: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
