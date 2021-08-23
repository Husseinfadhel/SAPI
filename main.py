from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from models import session, engine, Base
from routers import students, insitute_attendance, users

Base.metadata.create_all(engine)


def create_app(test_config=None):
    app = FastAPI()

    origins = [
        "http://localhost",
        "http://localhost:8080",
    ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(students.router)
    app.include_router(insitute_attendance.router)
    app.include_router(users.router)
    return app


app = create_app()

