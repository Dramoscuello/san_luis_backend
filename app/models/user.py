from datetime import datetime

from sqlalchemy.orm import relationship

from app.database.config import Base
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, CheckConstraint, Date, Text


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String, unique=True, nullable=False)
    nombre_completo = Column(String, nullable=False)
    cedula = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)
    rol = Column(String, CheckConstraint("rol IN ('docente', 'coordinador', 'rector')"), nullable=False)
    sede_id = Column(Integer, ForeignKey('sedes.id', ondelete='SET NULL'), nullable=True)
    activo = Column(Boolean, nullable=True, default=True)
    telefono = Column(String, nullable=True)
    fecha_ingreso = Column(Date, nullable=True)
    foto_url = Column(Text, nullable=True)
    ultimo_acceso = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, nullable=True, default=datetime.now)
    updated_at = Column(DateTime, nullable=True, default=datetime.now, onupdate=datetime.now)

    # Relaciones
    sede = relationship("Sedes", backref="usuarios")
    asignaturas = relationship("Asignatura", secondary="docente_asignaturas", back_populates="usuarios")
    grupos_a_cargo = relationship("Grupo", secondary="docente_grupos", back_populates="directores")


