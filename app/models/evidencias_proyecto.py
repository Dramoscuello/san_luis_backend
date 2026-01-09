from datetime import datetime, date

from sqlalchemy.orm import relationship

from app.database.config import Base
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Index, CheckConstraint, Date


class EvidenciaProyecto(Base):
    """
    Documentación del progreso/avance de un proyecto pedagógico.
    Cada evidencia representa un hito o avance documentado con archivo obligatorio.
    """
    __tablename__ = 'evidencias_proyecto'

    id = Column(Integer, primary_key=True, autoincrement=True)
    proyecto_id = Column(Integer, ForeignKey('proyectos.id', ondelete='CASCADE'), nullable=False)

    titulo = Column(String(255), nullable=False)
    descripcion = Column(Text, nullable=True)
    fecha_evidencia = Column(Date, nullable=True)

    # Google Drive (obligatorio)
    drive_file_id = Column(String(255), nullable=False, unique=True)
    drive_view_link = Column(Text, nullable=True)
    drive_embed_link = Column(Text, nullable=True)
    drive_download_link = Column(Text, nullable=True)
    nombre_archivo_original = Column(String(255), nullable=True)
    tipo_archivo = Column(String(20), nullable=True)  # pdf, docx, jpg, png, mp4, xlsx
    tamano_bytes = Column(Integer, nullable=True)

    subido_por = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)

    created_at = Column(DateTime, nullable=False, default=datetime.now)

    # Constraints e índices
    __table_args__ = (
        CheckConstraint("LENGTH(titulo) >= 5", name='chk_evidencia_proyecto_titulo_min'),
        Index('idx_evidencias_proyecto_proyecto', 'proyecto_id'),
        Index('idx_evidencias_proyecto_fecha', 'fecha_evidencia'),
        Index('idx_evidencias_proyecto_tipo', 'tipo_archivo'),
        Index('idx_evidencias_proyecto_created', 'created_at'),
    )

    # Relaciones
    proyecto = relationship("Proyecto", back_populates="evidencias")
    usuario = relationship("User", backref="evidencias_proyecto_subidas")
    comentarios = relationship("ComentarioProyecto", back_populates="evidencia", cascade="all, delete-orphan")
