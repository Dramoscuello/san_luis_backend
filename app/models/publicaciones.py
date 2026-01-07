from datetime import datetime

from sqlalchemy.orm import relationship

from app.database.config import Base
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Index, CheckConstraint


class Publicacion(Base):
    """
    Anuncios/comunicados institucionales de coordinadores y rector.
    Solo coordinadores y rector pueden publicar.
    Todos los usuarios pueden ver las publicaciones.
    """
    __tablename__ = 'publicaciones'

    id = Column(Integer, primary_key=True, autoincrement=True)
    autor_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    titulo = Column(String(255), nullable=False)
    contenido = Column(Text, nullable=False)

    # Documento adjunto OPCIONAL (Google Drive)
    drive_file_id = Column(String(255), unique=True, nullable=True)
    drive_view_link = Column(Text, nullable=True)
    drive_embed_link = Column(Text, nullable=True)
    drive_download_link = Column(Text, nullable=True)
    nombre_archivo_original = Column(String(255), nullable=True)
    tipo_archivo = Column(String(20), nullable=True)  # pdf, docx, imagen, excel
    tamano_bytes = Column(Integer, nullable=True)

    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    # Constraints
    __table_args__ = (
        CheckConstraint('LENGTH(titulo) >= 5', name='chk_publicacion_titulo_min'),
        CheckConstraint('LENGTH(contenido) >= 10', name='chk_publicacion_contenido_min'),
        Index('idx_publicaciones_autor', 'autor_id'),
        Index('idx_publicaciones_fecha', 'created_at'),
        Index('idx_publicaciones_updated', 'updated_at'),
    )

    # Relaciones
    autor = relationship("User", backref="publicaciones")
