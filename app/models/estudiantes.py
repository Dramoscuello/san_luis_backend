from datetime import datetime, date

from sqlalchemy.orm import relationship

from app.database.config import Base
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Index, UniqueConstraint, Date


class Estudiante(Base):
    """
    Estudiantes ingresados por docentes directores de grupo.
    Datos mínimos para cumplir GDPR/protección de datos de menores.
    """
    __tablename__ = 'estudiantes'

    id = Column(Integer, primary_key=True, autoincrement=True)
    grupo_id = Column(Integer, ForeignKey('grupos.id', ondelete='CASCADE'), nullable=False)
    numero_documento = Column(String(20), nullable=False)
    nombres = Column(String(150), nullable=False)
    apellidos = Column(String(150), nullable=False)
    
    # Datos personales opcionales
    fecha_nacimiento = Column(Date, nullable=True)
    lugar_nacimiento = Column(String(150), nullable=True)
    tipo_documento = Column(String(50), nullable=True)
    rh = Column(String(10), nullable=True)
    eps = Column(String(100), nullable=True)
    
    # Datos del padre
    nombre_padre = Column(String(200), nullable=True)
    ocupacion_padre = Column(String(100), nullable=True)
    celular_padre = Column(String(20), nullable=True)
    
    # Datos de la madre
    nombre_madre = Column(String(200), nullable=True)
    ocupacion_madre = Column(String(100), nullable=True)
    celular_madre = Column(String(20), nullable=True)
    
    # Datos del acudiente
    nombre_acudiente = Column(String(200), nullable=True)
    celular_acudiente = Column(String(20), nullable=True)
    
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    # Constraints e Índices
    __table_args__ = (
        UniqueConstraint('grupo_id', 'numero_documento', name='uq_estudiante_grupo_documento'),
        Index('idx_estudiantes_grupo', 'grupo_id'),
        Index('idx_estudiantes_documento', 'numero_documento'),
        Index('idx_estudiantes_nombres', 'nombres'),
    )

    # Relaciones
    grupo = relationship("Grupo", back_populates="estudiantes")
    observadores = relationship("Observador", back_populates="estudiante", cascade="all, delete-orphan")
