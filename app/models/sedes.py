from datetime import datetime

from app.database.config import Base
from sqlalchemy import Column, Integer, String, DateTime, Boolean


class Sedes(Base):
    __tablename__ = 'sedes'
    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String, nullable=False, unique=True)
    codigo = Column(String, nullable=False, unique=True)
    direccion = Column(String, nullable=False)
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now())
    updated_at = Column(DateTime, nullable=False, default=datetime.now(), onupdate=datetime.now())