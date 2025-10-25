from fastapi import FastAPI
import uvicorn

from app.api import auth
from app.database.config import Base, engine


def create_tables():
    Base.metadata.create_all(bind=engine)

create_tables()

app = FastAPI()
app.include_router(auth.router)

if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8000)


