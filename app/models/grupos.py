from datetime import datetime

from sqlalchemy.orm import relationship

from app.database.config import Base
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Index, UniqueConstraint


class Grupo(Base):
    """
    Secciones dentro de cada grado.
    Ejemplo: 6°1, 6°2, 7°A, 7°B, etc.
    """
    __tablename__ = 'grupos'

    id = Column(Integer, primary_key=True, autoincrement=True)
    grado_id = Column(Integer, ForeignKey('grados.id', ondelete='CASCADE'), nullable=False)
    nombre = Column(String(50), nullable=False)
    codigo = Column(String(20), nullable=True)
    
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    # Constraints e Índices
    __table_args__ = (
        UniqueConstraint('grado_id', 'nombre', name='uq_grupo_grado_nombre'),
        Index('idx_grupos_grado', 'grado_id'),
    )

    # Relaciones
    grado = relationship("Grado", backref="grupos")
    
    # Directores de grupo (Docentes)
    directores = relationship("User", secondary="docente_grupos", back_populates="grupos_a_cargo")
    
    # Estudiantes (se definirá cuando exista el modelo Estudiante)
    # estudiantes = relationship("Estudiante", back_populates="grupo")
