from datetime import datetime
from typing import Optional

from pydantic import BaseModel

class User(BaseModel):
    email: str
    nombre_completo : str
    cedula :str
    password :str
    rol :str
    sede_id : Optional[int] = None
    activo : bool
    telefono : str
    created_at : datetime = datetime.now()
    updated_at : datetime = datetime.now()

class UserResponse(BaseModel):
    email: str
    nombre_completo: str
    cedula : str
    rol: str
    activo: bool
    telefono: str

    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    email: Optional[str] = None
    nombre_completo: Optional[str] = None
    cedula : Optional[str] = None
    password : Optional[str] = None
    rol: Optional[str] = None
    sede_id: Optional[int] = None
    activo : Optional[bool] = None
    telefono: Optional[str] = None
    updated_at : datetime = datetime.now()

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    cedula: str | None = None


class ChangePassword(BaseModel):
    password_actual: str
    password_nuevo: str
