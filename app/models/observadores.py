from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, UniqueConstraint, CheckConstraint, Index
from sqlalchemy.orm import relationship
from app.database.config import Base

class Observador(Base):
    __tablename__ = 'observadores'

    id = Column(Integer, primary_key=True, autoincrement=True)
    estudiante_id = Column(Integer, ForeignKey('estudiantes.id', ondelete='CASCADE'), nullable=False)
    docente_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    periodo = Column(Integer, nullable=False)
    fortalezas = Column(Text, nullable=True)
    dificultades = Column(Text, nullable=True)
    compromisos = Column(Text, nullable=True)
    
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    # Constraints e Índices
    __table_args__ = (
        CheckConstraint('periodo >= 1 AND periodo <= 4', name='check_periodo_valido'),
        UniqueConstraint('estudiante_id', 'docente_id', 'periodo', name='uq_observador_estudiante_docente_periodo'),
        Index('idx_observadores_estudiante', 'estudiante_id'),
        Index('idx_observadores_docente', 'docente_id'),
        Index('idx_observadores_periodo', 'periodo'),
        Index('idx_observadores_updated', 'updated_at'),
    )

    # Relaciones
    estudiante = relationship("Estudiante", back_populates="observadores")
    docente = relationship("User", backref="observadores_creados")
