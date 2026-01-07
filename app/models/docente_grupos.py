from datetime import datetime

from app.database.config import Base
from sqlalchemy import Column, Integer, Boolean, ForeignKey, Date, Index, UniqueConstraint


class DocenteGrupo(Base):
    """
    Tabla intermedia para asignar directores de grupo.
    Relación N:M entre Docentes y Grupos.
    Generalmente es 1 grupo por docente, pero el modelo permite flexibilidad.
    """
    __tablename__ = 'docente_grupos'

    id = Column(Integer, primary_key=True, autoincrement=True)
    docente_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    grupo_id = Column(Integer, ForeignKey('grupos.id', ondelete='CASCADE'), nullable=False)
    
    fecha_asignacion = Column(Date, default=datetime.now().date, nullable=False)
    activa = Column(Boolean, default=True, nullable=False)

    # Constraints e Índices
    __table_args__ = (
        UniqueConstraint('docente_id', 'grupo_id', name='uq_docente_grupo'),
        Index('idx_docente_grupos_docente', 'docente_id'),
        Index('idx_docente_grupos_grupo', 'grupo_id'),
    )
