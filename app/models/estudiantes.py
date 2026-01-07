from datetime import datetime

from sqlalchemy.orm import relationship

from app.database.config import Base
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Index, UniqueConstraint


class Estudiante(Base):
    """
    Estudiantes ingresados por docentes directores de grupo.
    Datos mínimos para cumplir GDPR/protección de datos de menores.
    """
    __tablename__ = 'estudiantes'

    id = Column(Integer, primary_key=True, autoincrement=True)
    grupo_id = Column(Integer, ForeignKey('grupos.id', ondelete='CASCADE'), nullable=False)
    numero_documento = Column(String(20), nullable=False)
    nombres = Column(String(150), nullable=False)
    apellidos = Column(String(150), nullable=False)
    
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    # Constraints e Índices
    __table_args__ = (
        UniqueConstraint('grupo_id', 'numero_documento', name='uq_estudiante_grupo_documento'),
        Index('idx_estudiantes_grupo', 'grupo_id'),
        Index('idx_estudiantes_documento', 'numero_documento'),
        Index('idx_estudiantes_nombres', 'nombres'),
    )

    # Relaciones
    grupo = relationship("Grupo", back_populates="estudiantes")
