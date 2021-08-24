from fastapi import APIRouter
from models import session, Users
from random import randrange

router = APIRouter()


# register a new user
@router.post('/register')
def register(username, password, name):
    new = Users(username=username, password=password, name=name)
    Users.insert(new)
    return {
        "success": True
    }


# login route
@router.post('/login')
def login(username: str, password: int):
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


# to get users
@router.get('/users')
def users():
    query = session.query(Users).all()
    return {
        "users": [record.format() for record in query]
    }


# to modify user
@router.patch('/user')
def user(_id, name, username, password):
    query = session.query(Users).get(_id)
    query.name = name
    query.username = username
    query.password = password
    Users.update(query)
    return {
        "success": True
    }
