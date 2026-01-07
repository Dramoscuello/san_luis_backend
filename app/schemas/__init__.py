from app.schemas.user import User, UserResponse, UserUpdate, Token, TokenData, ChangePassword
from app.schemas.sedes import Sedes, SedesResponse, UpdateSedes
from app.schemas.publicaciones import (
    PublicacionCreate,
    PublicacionUpdate,
    PublicacionResponse,
    AutorResponse,
)
from app.schemas.areas import AreaCreate, AreaUpdate, AreaResponse

__all__ = [
    "User",
    "UserResponse",
    "UserUpdate",
    "Token",
    "TokenData",
    "ChangePassword",
    "Sedes",
    "SedesResponse",
    "UpdateSedes",
    "PublicacionCreate",
    "PublicacionUpdate",
    "PublicacionResponse",
    "AutorResponse",
    "AreaCreate",
    "AreaUpdate",
    "AreaResponse",
]
