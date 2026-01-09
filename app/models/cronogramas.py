from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Date, DateTime, ForeignKey, Index, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import relationship
from app.database.config import Base

class Cronograma(Base):
    """
    Cronograma anual de actividades para cada docente.
    Contenedor principal que agrupa las actividades del año.
    """
    __tablename__ = 'cronogramas'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    docente_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    titulo = Column(String(255), nullable=False)
    descripcion = Column(Text, nullable=True)
    # Se asigna automáticamente al año actual si no se provee
    anio_escolar = Column(Integer, nullable=False, default=lambda: datetime.now().year)
    estado = Column(String(50), default='activo', nullable=False)
    
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
    
    __table_args__ = (
        UniqueConstraint('docente_id', 'anio_escolar', name='uq_cronograma_docente_anio'),
        CheckConstraint("estado IN ('activo', 'archivado')", name='chk_cronograma_estado'),
    )

    # Relaciones
    docente = relationship("User", backref="cronogramas")
    actividades = relationship("ActividadCronograma", back_populates="cronograma", cascade="all, delete-orphan")


class ActividadCronograma(Base):
    """
    Actividad específica planificada para una fecha concreta dentro del cronograma.
    """
    __tablename__ = 'actividades_cronograma'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    cronograma_id = Column(Integer, ForeignKey('cronogramas.id', ondelete='CASCADE'), nullable=False)
    titulo = Column(String(150), nullable=False)
    descripcion = Column(Text, nullable=True)
    fecha_programada = Column(Date, nullable=False)
    estado = Column(String(50), default='pendiente', nullable=False)
    
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
    
    __table_args__ = (
        Index('idx_actividades_fecha', 'cronograma_id', 'fecha_programada'),
        CheckConstraint("estado IN ('pendiente', 'completada', 'retrasada', 'cancelada')", name='chk_actividad_estado'),
    )
    
    # Relaciones
    cronograma = relationship("Cronograma", back_populates="actividades")
    evidencias = relationship("EvidenciaActividad", back_populates="actividad", cascade="all, delete-orphan")


class EvidenciaActividad(Base):
    """
    Soporte (archivo) que demuestra el cumplimiento de una actividad.
    Una actividad puede tener múltiples evidencias.
    """
    __tablename__ = 'evidencias_actividad'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    actividad_id = Column(Integer, ForeignKey('actividades_cronograma.id', ondelete='CASCADE'), nullable=False)
    
    # Metadata de Google Drive
    drive_file_id = Column(String(255), nullable=False)
    drive_view_link = Column(Text, nullable=True)
    drive_download_link = Column(Text, nullable=True)
    
    nombre_archivo = Column(String(255), nullable=True)
    tipo_archivo = Column(String(50), nullable=True)
    
    fecha_subida = Column(DateTime, default=datetime.now, nullable=False)
    comentario_docente = Column(Text, nullable=True)
    
    # Relaciones
    actividad = relationship("ActividadCronograma", back_populates="evidencias")
