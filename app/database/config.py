from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from app.core.config import Settings


URI = Settings.URI
engine = create_engine(URI)
session_Local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = session_Local()
    try:
        yield db
    finally:
        db.close()