from fastapi import APIRouter
from models import session, engine, Base, Institute, Student
from typing import Optional


router = APIRouter()


# insert attendance
