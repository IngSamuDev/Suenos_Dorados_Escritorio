from fastapi import FastAPI

from database import Base, engine
from models import *  # noqa: F401,F403 - registra mapeos SQLAlchemy
from routes import api_routers

app = FastAPI(
    title="Suenos Dorados Admin API",
    version="1.0.0",
)

Base.metadata.create_all(bind=engine)

for router in api_routers:
    app.include_router(router)


@app.get("/")
def root():
    return {"app": "Suenos Dorados Admin API", "docs": "/docs"}


