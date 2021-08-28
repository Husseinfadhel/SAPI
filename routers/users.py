from fastapi import APIRouter
from models import session, Users
from random import randrange
from starlette.exceptions import HTTPException as StarletteHTTPException

router = APIRouter()


# register a new user
@router.post('/register')
def register(username, password, name):
    try:
        new = Users(username=username, password=password, name=name)
        Users.insert(new)
        return {
            "success": True
        }
    except:
        raise StarletteHTTPException(500, "internal Server Error")


# login route
@router.post('/login')
def login(username: str, password: int):
    try:
        query = session.query(Users).all()
        for record in [user.format() for user in query]:
            if record['user'] == username and record['pass'] == password:
                return {
                    "success": True,
                    "token": randrange(999999999, 1000000000000000),
                    "name": record['name']
                }
            else:
                return {
                    "success": False,
                }
    except:
        raise StarletteHTTPException(401, "Unauthorized")


# to get users
@router.get('/users')
def users():
    try:
        query = session.query(Users).all()
        return {
            "users": [record.format() for record in query]
        }
    except:
        raise StarletteHTTPException(404, "Not Found")


# to modify user
@router.patch('/user')
def user(_id, name, username, password):
    try:
        query = session.query(Users).get(_id)
        query.name = name
        query.username = username
        query.password = password
        Users.update(query)
        return {
            "success": True
        }
    except:
        raise StarletteHTTPException(500, "internal Server Error")
