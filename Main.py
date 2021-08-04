from fastapi import FastAPI
from Models import session, engine, Base

Base.metadata.create_all(engine)

app = FastAPI()


