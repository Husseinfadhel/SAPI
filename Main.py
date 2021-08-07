from fastapi import FastAPI
from Models import session, engine, Base
from routers import students, insitute_attendance

Base.metadata.create_all(engine)

app = FastAPI()

app.include_router(students.router)
app.include_router(insitute_attendance.router)