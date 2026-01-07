from datetime import datetime

from sqlalchemy.orm import relationship

from app.database.config import Base
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Index


class Area(Base):
    """
    Áreas académicas de la institución.
    Ejemplo: Matemáticas, Ciencias Naturales, Humanidades, etc.
    """
    __tablename__ = 'areas'

    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(100), unique=True, nullable=False)
    descripcion = Column(Text, nullable=True)
    activa = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    # Índices
    __table_args__ = (
        Index('idx_areas_activa', 'activa'),
    )

    # Relaciones
    asignaturas = relationship("Asignatura", back_populates="area")
