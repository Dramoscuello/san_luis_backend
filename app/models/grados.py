from datetime import datetime

from sqlalchemy.orm import relationship

from app.database.config import Base
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Index, UniqueConstraint


class Grado(Base):
    """
    Niveles académicos dentro de cada sede.
    Ejemplo: 6°, 7°, 8°, etc.
    Un grado pertenece a una Sede.
    """
    __tablename__ = 'grados'

    id = Column(Integer, primary_key=True, autoincrement=True)
    sede_id = Column(Integer, ForeignKey('sedes.id', ondelete='CASCADE'), nullable=False)
    nombre = Column(String(50), nullable=False)
    codigo = Column(String(20), nullable=True)
    
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    # Constraints e Índices
    __table_args__ = (
        UniqueConstraint('sede_id', 'nombre', name='uq_grado_sede_nombre'),
        Index('idx_grados_sede', 'sede_id'),
    )

    # Relaciones
    sede = relationship("Sedes", backref="grados")
    # grupos = relationship("Grupo", back_populates="grado") # Se definirá cuando exista el modelo Grupo
