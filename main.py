import signal
import time
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from models import session, engine, Base
from routers import students, insitute_attendance, users
from fastapi.responses import PlainTextResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
import uvicorn
from multiprocessing import Process
import os

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

    @app.exception_handler(StarletteHTTPException)
    async def my_exception_handler(request, exception):
        return PlainTextResponse(str(exception.detail), status_code=exception.status_code)

    return app


app = create_app()


# @app.on_event('shutdown')
# async def shut():
# service = app.state.service
# service.restart()
# os.system('python restart.py')

@app.get('/shutdown')
def shut():
    pid = os.getpid()
    print(pid)
    os.kill(pid, signal.CTRL_C_EVENT)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)


