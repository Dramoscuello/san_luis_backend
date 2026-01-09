from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel, Field

# --- Shared Models ---

class DocenteBasico(BaseModel):
    id: int
    nombre_completo: str
    email: str
    class Config:
        from_attributes = True


# --- Evidencias ---

class EvidenciaBase(BaseModel):
    comentario_docente: Optional[str] = None

class EvidenciaCreate(EvidenciaBase):
    actividad_id: int

class EvidenciaResponse(EvidenciaBase):
    id: int
    actividad_id: int
    drive_file_id: str
    drive_view_link: Optional[str] = None
    drive_download_link: Optional[str] = None
    nombre_archivo: Optional[str] = None
    tipo_archivo: Optional[str] = None
    fecha_subida: datetime
    
    class Config:
        from_attributes = True


# --- Actividades ---

class ActividadBase(BaseModel):
    titulo: str = Field(..., min_length=3, max_length=150)
    descripcion: Optional[str] = None
    fecha_programada: date
    estado: Optional[str] = "pendiente"

class ActividadCreate(ActividadBase):
    cronograma_id: int

class ActividadUpdate(BaseModel):
    titulo: Optional[str] = Field(None, min_length=3, max_length=150)
    descripcion: Optional[str] = None
    fecha_programada: Optional[date] = None
    estado: Optional[str] = None

class ActividadResponse(ActividadBase):
    id: int
    cronograma_id: int
    created_at: datetime
    updated_at: datetime
    evidencias: List[EvidenciaResponse] = []
    
    class Config:
        from_attributes = True


# --- Cronogramas ---

class CronogramaBase(BaseModel):
    titulo: str = Field(..., min_length=5, max_length=255)
    descripcion: Optional[str] = None

class CronogramaCreate(CronogramaBase):
    pass 
    # anio_escolar automático

class CronogramaUpdate(BaseModel):
    titulo: Optional[str] = Field(None, min_length=5, max_length=255)
    descripcion: Optional[str] = None
    estado: Optional[str] = None

class CronogramaResponse(CronogramaBase):
    id: int
    docente_id: int
    anio_escolar: int
    estado: str
    created_at: datetime
    updated_at: datetime
    docente: Optional[DocenteBasico] = None
    
    class Config:
        from_attributes = True

class CronogramaDetailResponse(CronogramaResponse):
    """Respuesta completa con todas las actividades flat (para vista calendario)"""
    actividades: List[ActividadResponse] = []
