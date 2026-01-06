from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os

from app.api import auth
from app.api import sedes
from app.api import user
from app.database.config import Base, engine

from app.models import Sedes, User


def create_tables():
    Base.metadata.create_all(bind=engine)

create_tables()

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", os.getenv("FRONTEND_URL", "")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(sedes.router)
app.include_router(user.router)

if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8000)


