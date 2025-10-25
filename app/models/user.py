from datetime import datetime

from app.database.config import Base
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, CheckConstraint


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String, unique=True, nullable=False)
    nombre_completo = Column(String, nullable=False)
    cedula = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)
    rol = Column(String, CheckConstraint("rol IN ('docente', 'coordinador', 'rector')"), nullable=False)
    #sede_id = Column(Integer, ForeignKey('sedes.id', ondelete='SET NULL'), nullable=True)
    activo = Column(Boolean, nullable=False, default=True)
    telefono = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now())
    updated_at = Column(DateTime, nullable=False, default=datetime.now(), onupdate=datetime.now())

