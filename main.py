import signal
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
# from routers import students, insitute_attendance, users
from fastapi.responses import PlainTextResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
import uvicorn
import os
from tortoise.contrib.fastapi import register_tortoise

from routers import students, insitute_attendance, users


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
    register_tortoise(
        app,
        db_url='sqlite://sapi.db',
        modules={'models': ["models.db"]},
        generate_schemas=True,
        add_exception_handlers=True,
    )
    app.include_router(students.router)
    app.include_router(insitute_attendance.router)
    app.include_router(users.router)

    @app.exception_handler(StarletteHTTPException)
    async def my_exception_handler(request, exception):
        return PlainTextResponse(str(exception.detail), status_code=exception.status_code)

    return app


TORTOISE_ORM = {
    "connections": {
        "default": 'sqlite://sapi.db'
    },
    "apps": {
        "models": {
            "models": [
                "models.db", "aerich.models"
            ],
            "default_connection": "default",
        },
    },
}
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
