from datetime import datetime

from sqlalchemy.orm import relationship

from app.database.config import Base
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Index, CheckConstraint


class Planeacion(Base):
    """
    Documentos de planificación de clases subidos por docentes.
    Cada planeación pertenece a un docente, asignatura, sede y período académico.
    El archivo se almacena en Google Drive y aquí solo se guarda la metadata.
    """
    __tablename__ = 'planeaciones'

    id = Column(Integer, primary_key=True, autoincrement=True)
    docente_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    asignatura_id = Column(Integer, ForeignKey('asignaturas.id', ondelete='CASCADE'), nullable=False)
    sede_id = Column(Integer, ForeignKey('sedes.id', ondelete='CASCADE'), nullable=False)
    periodo_id = Column(Integer, ForeignKey('periodos.id', ondelete='CASCADE'), nullable=False)

    titulo = Column(String(255), nullable=False)
    nombre_archivo_original = Column(String(255), nullable=False)

    # Google Drive
    drive_file_id = Column(String(255), nullable=False, unique=True)
    drive_view_link = Column(Text, nullable=True)
    drive_embed_link = Column(Text, nullable=True)
    drive_download_link = Column(Text, nullable=True)

    tamano_bytes = Column(Integer, nullable=True)
    tipo_archivo = Column(String(10), nullable=True)  # pdf, docx

    fecha_subida = Column(DateTime, nullable=False, default=datetime.now)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    # Constraints e índices
    __table_args__ = (
        CheckConstraint("tipo_archivo IN ('pdf', 'docx', 'doc')", name='chk_planeacion_tipo_archivo'),
        Index('idx_planeaciones_docente', 'docente_id'),
        Index('idx_planeaciones_asignatura', 'asignatura_id'),
        Index('idx_planeaciones_sede', 'sede_id'),
        Index('idx_planeaciones_periodo', 'periodo_id'),
        Index('idx_planeaciones_fecha', 'fecha_subida'),
        Index('idx_planeaciones_drive_id', 'drive_file_id'),
    )

    # Relaciones
    docente = relationship("User", backref="planeaciones")
    asignatura = relationship("Asignatura", backref="planeaciones")
    sede = relationship("Sedes", backref="planeaciones")
    periodo = relationship("Periodo", backref="planeaciones")
