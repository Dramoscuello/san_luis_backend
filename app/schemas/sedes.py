from datetime import datetime
from typing import Optional

from pydantic import BaseModel

class Sedes(BaseModel):
    nombre :str
    codigo :str
    direccion :str
    active : bool
    created_at :datetime = datetime.now()
    updated_at :datetime = datetime.now()


class SedesResponse(BaseModel):
    id: int
    nombre :str
    codigo :str
    direccion :str
    active : bool

    class Config:
        from_attributes = True

class UpdateSedes(BaseModel):
    nombre : Optional[str] = None
    codigo : Optional[str] = None
    direccion : Optional[str] = None
    active : Optional[bool] = None
    updated_at : datetime = datetime.now()

    class Config:
        from_attributes = True