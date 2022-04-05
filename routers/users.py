from fastapi import APIRouter
from tortoise.transactions import in_transaction

from models.db import Users
from random import randrange
from starlette.exceptions import HTTPException as StarletteHTTPException

router = APIRouter()


# register a new user
@router.post('/register')
async def register(username: str, password: int, name: str, auth: int):
    try:
        async with in_transaction() as conn:
            new = Users(username=username, password=password, name=name, auth=auth)
            await new.save(using_db=conn)
        return {
            "success": True,
        }
    except:
        raise StarletteHTTPException(500, "internal Server Error")


# login route
@router.post('/login')
async def login(username: str, password: int):
    try:
        query = await Users.filter(username=username).first()
        if query.username == username and query.password == password:
            return {
                "success": True,
                "token": randrange(999999999, 1000000000000000),
                "id": query.id,
                "name": query.name,
                "username": query.username,
                "password": query.password,
                "auth": query.auth
            }
    except:
        raise StarletteHTTPException(401, "Unauthorized")


# to get users
@router.get('/users')
async def users():
    try:
        return {
            "users": await Users.all()
        }
    except:
        raise StarletteHTTPException(404, "Not Found")


# to modify user
@router.patch('/user')
async def user(user_id: int, name: str, username: str, password: int, auth: int):
    try:
        await Users.filter(id=user_id).update(name=name, username=username, password=password, auth=auth)
        return {
            "success": True
        }
    except:
        raise StarletteHTTPException(500, "internal Server Error")
