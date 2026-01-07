from datetime import datetime

from app.database.config import Base
from sqlalchemy import Column, Integer, Boolean, ForeignKey, Date, Index, UniqueConstraint


class DocenteAsignatura(Base):
    """
    Tabla intermedia para la relación N:M entre Docentes y Asignaturas.
    Un docente puede dictar múltiples asignaturas.
    Una asignatura puede ser dictada por múltiples docentes (en diferentes grupos).
    """
    __tablename__ = 'docente_asignaturas'

    id = Column(Integer, primary_key=True, autoincrement=True)
    docente_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    asignatura_id = Column(Integer, ForeignKey('asignaturas.id', ondelete='CASCADE'), nullable=False)
    
    fecha_asignacion = Column(Date, default=datetime.now().date, nullable=False)
    activa = Column(Boolean, default=True, nullable=False)

    # Constraints e Índices
    __table_args__ = (
        UniqueConstraint('docente_id', 'asignatura_id', name='uq_docente_asignatura'),
        Index('idx_docente_asignaturas_docente', 'docente_id'),
        Index('idx_docente_asignaturas_asignatura', 'asignatura_id'),
    )
