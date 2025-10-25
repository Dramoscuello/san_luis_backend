from datetime import datetime

from pydantic import BaseModel




class User(BaseModel):
    email: str
    nombre_completo : str
    cedula :str
    password :str
    rol :str
    #sede_id : int
    activo : bool
    telefono : str
    created_at : datetime = datetime.now()
    updated_at : datetime = datetime.now()


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    cedula: str | None = None
