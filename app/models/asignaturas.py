from datetime import datetime

from sqlalchemy.orm import relationship

from app.database.config import Base
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Index, UniqueConstraint


class Asignatura(Base):
    """
    Materias que se dictan en la institución.
    Ejemplo: Álgebra, Geometría, Biología, etc.
    """
    __tablename__ = 'asignaturas'

    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(100), nullable=False)
    area_id = Column(Integer, ForeignKey('areas.id', ondelete='CASCADE'), nullable=False)
    codigo = Column(String(20), unique=True, nullable=True)
    descripcion = Column(Text, nullable=True)
    grados = Column(String(100), nullable=True, comment="Lista separada por comas de los grados donde se dicta (ej: 6,7,8)")
    activa = Column(Boolean, nullable=False, default=True)
    
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    # Constraints e Índices
    __table_args__ = (
        UniqueConstraint('nombre', 'area_id', name='uq_asignatura_nombre_area'),
        Index('idx_asignaturas_area', 'area_id'),
        Index('idx_asignaturas_activa', 'activa'),
    )

    # Relaciones
    area = relationship("Area", back_populates="asignaturas")
    usuarios = relationship("User", secondary="docente_asignaturas", back_populates="asignaturas")
