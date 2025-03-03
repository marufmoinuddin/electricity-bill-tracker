from fastapi import FastAPI
from .database import SessionLocal, engine
from .models import Base

Base.metadata.create_all(bind=engine)

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Welcome to the Bill Tracking API"}