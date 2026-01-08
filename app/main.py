from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os

from app.api import auth
from app.api import sedes
from app.api import user
from app.api import publicaciones
from app.api import areas
from app.api import asignaturas
from app.api import grados
from app.api import grupos
from app.api import estudiantes
from app.api import periodos
from app.api import planeaciones
from app.api import comentarios
from app.api import planeaciones_destacadas
from app.database.config import Base, engine

from app.models import Sedes, User, Publicacion, Area, Estudiante, Periodo, Planeacion, Comentario, PlaneacionDestacada


def create_tables():
    Base.metadata.create_all(bind=engine)

create_tables()

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", os.getenv("FRONTEND_URL", "")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(sedes.router)
app.include_router(user.router)
app.include_router(publicaciones.router)
app.include_router(areas.router)
app.include_router(asignaturas.router)
app.include_router(grados.router)
app.include_router(grupos.router)
app.include_router(estudiantes.router)
app.include_router(periodos.router)
app.include_router(planeaciones.router)
app.include_router(comentarios.router)
app.include_router(planeaciones_destacadas.router)

if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8000)



