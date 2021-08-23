from fastapi import APIRouter
from models import session, engine, Base, Users
from random import randrange

router = APIRouter()


# register a new user
@router.post('/register')
def register(username, password):
    new = Users(username=username, password=password)
    Users.insert(new)
    return {
        "success": True
    }


# login route
@router.get('/login')
def login(username: str, password: int):
    query = session.query(Users).all()
    for record in [user.format() for user in query]:
        if record['user'] == username and record['pass'] == password:
            return {
                "success": True,
                "token": randrange(999999999, 1000000000000000)
            }
        else:
            return {
                "success": False,
            }
