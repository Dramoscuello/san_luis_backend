from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, Field

# --- Schemas Anidados Simples ---
class EstudianteCompleto(BaseModel):
    id: int
    nombres: str
    apellidos: str
    numero_documento: str
    
    # Datos personales opcionales
    edad: Optional[int] = None
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

    class Config:
        from_attributes = True

class DocenteSimple(BaseModel):
    id: int
    nombre_completo: str

    class Config:
        from_attributes = True

# --- Schemas de Observador ---

# Campos de contenido de la observación
class ObservadorContent(BaseModel):
    fortalezas: Optional[str] = None
    dificultades: Optional[str] = None
    compromisos: Optional[str] = None

class ObservadorCreate(ObservadorContent):
    estudiante_id: int

class ObservadorUpdate(ObservadorContent):
    pass

class ObservadorResponse(ObservadorContent):
    id: int
    periodo: int
    estudiante_id: int
    docente_id: int
    created_at: datetime
    updated_at: datetime
    
    estudiante: Optional[EstudianteCompleto] = None
    docente: Optional[DocenteSimple] = None

    class Config:
        from_attributes = True

class ObservadorPDFRequest(BaseModel):
    estudiante_id: int
