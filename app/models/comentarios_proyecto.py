from datetime import datetime

from sqlalchemy.orm import relationship

from app.database.config import Base
from sqlalchemy import Column, Integer, DateTime, Text, ForeignKey, Index, CheckConstraint


class ComentarioProyecto(Base):
    """
    Retroalimentación de coordinadores sobre proyectos o evidencias específicas.
    Un comentario es sobre el proyecto general O sobre una evidencia, nunca ambos.
    """
    __tablename__ = 'comentarios_proyecto'

    id = Column(Integer, primary_key=True, autoincrement=True)
    proyecto_id = Column(Integer, ForeignKey('proyectos.id', ondelete='CASCADE'), nullable=True)
    evidencia_id = Column(Integer, ForeignKey('evidencias_proyecto.id', ondelete='CASCADE'), nullable=True)
    coordinador_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)

    contenido = Column(Text, nullable=False)

    created_at = Column(DateTime, nullable=False, default=datetime.now)

    # Constraints e índices
    __table_args__ = (
        CheckConstraint(
            "(proyecto_id IS NOT NULL AND evidencia_id IS NULL) OR (proyecto_id IS NULL AND evidencia_id IS NOT NULL)",
            name='chk_comentario_proyecto_exclusivo'
        ),
        CheckConstraint("LENGTH(contenido) >= 10", name='chk_comentario_proyecto_contenido_min'),
        Index('idx_comentarios_proyecto_proyecto', 'proyecto_id'),
        Index('idx_comentarios_proyecto_evidencia', 'evidencia_id'),
        Index('idx_comentarios_proyecto_coordinador', 'coordinador_id'),
        Index('idx_comentarios_proyecto_fecha', 'created_at'),
    )

    # Relaciones
    proyecto = relationship("Proyecto", back_populates="comentarios")
    evidencia = relationship("EvidenciaProyecto", back_populates="comentarios")
    coordinador = relationship("User", backref="comentarios_proyectos")
