from datetime import datetime

from sqlalchemy.orm import relationship

from app.database.config import Base
from sqlalchemy import Column, Integer, DateTime, Text, ForeignKey, Index, CheckConstraint


class Comentario(Base):
    """
    Retroalimentación de coordinadores sobre planeaciones.
    Solo coordinadores y rector pueden crear comentarios.
    Los docentes reciben notificación cuando reciben un comentario.
    """
    __tablename__ = 'comentarios'

    id = Column(Integer, primary_key=True, autoincrement=True)
    planeacion_id = Column(Integer, ForeignKey('planeaciones.id', ondelete='CASCADE'), nullable=False)
    coordinador_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    contenido = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now)

    # Constraints e índices
    __table_args__ = (
        CheckConstraint('LENGTH(contenido) >= 10', name='chk_comentario_contenido_min'),
        Index('idx_comentarios_planeacion', 'planeacion_id'),
        Index('idx_comentarios_coordinador', 'coordinador_id'),
        Index('idx_comentarios_fecha', 'created_at'),
    )

    # Relaciones
    planeacion = relationship("Planeacion", backref="comentarios")
    coordinador = relationship("User", backref="comentarios_realizados")
