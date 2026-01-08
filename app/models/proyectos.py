from datetime import datetime, date

from sqlalchemy.orm import relationship

from app.database.config import Base
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Index, CheckConstraint, Date


class Proyecto(Base):
    """
    Proyectos pedagógicos creados por docentes.
    Pueden incluir un documento base opcional almacenado en Google Drive.
    """
    __tablename__ = 'proyectos'

    id = Column(Integer, primary_key=True, autoincrement=True)
    docente_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)

    titulo = Column(String(255), nullable=False)
    descripcion = Column(Text, nullable=False)
    objetivos = Column(Text, nullable=True)
    fecha_inicio = Column(Date, nullable=False)
    fecha_fin_estimada = Column(Date, nullable=True)

    # Documento base (opcional) - Google Drive
    drive_file_id = Column(String(255), nullable=True, unique=True)
    drive_view_link = Column(Text, nullable=True)
    drive_embed_link = Column(Text, nullable=True)
    drive_download_link = Column(Text, nullable=True)
    nombre_archivo_original = Column(String(255), nullable=True)

    estado = Column(String(50), nullable=False, default='activo')

    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    # Constraints e índices
    __table_args__ = (
        CheckConstraint("estado IN ('activo', 'pausado', 'completado', 'cancelado')", name='chk_proyecto_estado'),
        CheckConstraint("LENGTH(titulo) >= 5", name='chk_proyecto_titulo_min'),
        CheckConstraint("LENGTH(descripcion) >= 20", name='chk_proyecto_descripcion_min'),
        Index('idx_proyectos_docente', 'docente_id'),
        Index('idx_proyectos_estado', 'estado'),
        Index('idx_proyectos_fecha_inicio', 'fecha_inicio'),
        Index('idx_proyectos_fecha_fin', 'fecha_fin_estimada'),
    )

    # Relaciones
    docente = relationship("User", backref="proyectos")
    evidencias = relationship("EvidenciaProyecto", back_populates="proyecto", cascade="all, delete-orphan")
    comentarios = relationship("ComentarioProyecto", back_populates="proyecto", cascade="all, delete-orphan")
