from fastapi import APIRouter
from Models import session, engine, Base, Insitute, Student

router = APIRouter()


# To get Insitutes Number
@router.get("/insituteNum")
def insituteNum():
    num = session.query(Insitute).all()
    # lo = [n.format() for n in num]
    numinsitute = len(list(num))
    return {
        "Response": "OK", "Number of Insitutes": numinsitute
    }


# To insert Insitute
@router.post("/insitute")
def insituteInsert(name: str):
    new = Insitute(name=name)
    Insitute.insert(new)

    return {"Response": "Done"}


# To get students number

@router.get("/studentNum")
def studentNum():
    num = session.query(Student).all()
    studentnum = len(list(num))
    return {
        "Response": "OK", "Number of Students": studentnum
    }
