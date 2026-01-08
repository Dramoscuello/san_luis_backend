from datetime import datetime

from sqlalchemy.orm import relationship

from app.database.config import Base
from sqlalchemy import Column, Integer, DateTime, Text, ForeignKey, Index, CheckConstraint, Boolean


class PlaneacionDestacada(Base):
    """
    Planeaciones marcadas como referentes institucionales.
    Solo coordinadores y rector pueden destacar planeaciones.
    Sirve para crear un banco de mejores prácticas institucionales.
    Visible para TODOS los docentes independiente del área.
    """
    __tablename__ = 'planeaciones_destacadas'

    id = Column(Integer, primary_key=True, autoincrement=True)
    planeacion_id = Column(Integer, ForeignKey('planeaciones.id', ondelete='CASCADE'), nullable=False, unique=True)
    coordinador_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    razon = Column(Text, nullable=False)  # Por qué es destacada (mínimo 20 caracteres)
    activa = Column(Boolean, nullable=False, default=True)
    visualizaciones = Column(Integer, nullable=False, default=0)  # Gamificación
    fecha_destacado = Column(DateTime, nullable=False, default=datetime.now)
    created_at = Column(DateTime, nullable=False, default=datetime.now)

    # Constraints e índices
    __table_args__ = (
        CheckConstraint('LENGTH(razon) >= 20', name='chk_destacada_razon_min'),
        Index('idx_destacadas_planeacion', 'planeacion_id'),
        Index('idx_destacadas_activa', 'activa'),
        Index('idx_destacadas_fecha', 'fecha_destacado'),
        Index('idx_destacadas_visualizaciones', 'visualizaciones'),
    )

    # Relaciones
    planeacion = relationship("Planeacion", backref="destacada")
    coordinador = relationship("User", backref="planeaciones_destacadas")
