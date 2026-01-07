from datetime import datetime

from app.database.config import Base
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Date, Index, event


class Periodo(Base):
    """
    Períodos escolares del año.
    Por defecto son 4 períodos (1, 2, 3, 4).
    Solo un período puede estar activo a la vez.
    Se usa para asignar planeaciones, observadores y otros módulos al período activo.
    """
    __tablename__ = 'periodos'

    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(10), nullable=False, unique=True)  # "1", "2", "3", "4"
    fecha_inicio = Column(Date, nullable=True)
    fecha_fin = Column(Date, nullable=True)
    activo = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    # Índices
    __table_args__ = (
        Index('idx_periodos_activo', 'activo'),
        Index('idx_periodos_nombre', 'nombre'),
    )


def crear_periodos_iniciales(target, connection, **kw):
    """Crear los 4 períodos por defecto después de crear la tabla."""
    from sqlalchemy.orm import Session
    session = Session(bind=connection)

    # Verificar si ya existen periodos
    existe = session.query(Periodo).first()
    if not existe:
        for i in range(1, 5):
            periodo = Periodo(nombre=str(i), activo=False)
            session.add(periodo)
        session.commit()
    session.close()


# Evento para crear periodos después de crear la tabla
event.listen(Periodo.__table__, 'after_create', crear_periodos_iniciales)
