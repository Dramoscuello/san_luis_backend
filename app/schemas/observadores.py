from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

# --- Schemas Anidados Simples ---
class EstudianteSimple(BaseModel):
    id: int
    nombres: str
    apellidos: str
    numero_documento: str

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
    
    estudiante: Optional[EstudianteSimple] = None
    docente: Optional[DocenteSimple] = None

    class Config:
        from_attributes = True

class ObservadorPDFRequest(BaseModel):
    estudiante_id: int
