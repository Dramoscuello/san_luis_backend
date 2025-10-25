import os
from pathlib import Path
from dotenv import load_dotenv



env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

class Settings:
    POSTGRES_USER:str = os.getenv("USER_POSTGRES")
    POSTGRES_PASSWORD:str = os.getenv("PASS_POSTGRES")
    POSTGRES_DB:str = os.getenv("DB_POSTGRES")
    POSTGRES_HOST:str = os.getenv("HOST_POSTGRES")
    POSTGRES_PORT:str = os.getenv("PORT_POSTGRES", '5432')
    URI:str = f'postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}'

Settings = Settings()
    