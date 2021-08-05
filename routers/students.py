from fastapi import APIRouter
from Models import session, engine, Base, Insitute, Student

router = APIRouter()


# To get Insitutes Number , Students
@router.get("/insituteNum")
def insituteStudentNum():
    num = session.query(Insitute).all()
    num = session.query(Student).all()
    studentnum = len(list(num))
    # lo = [n.format() for n in num]
    numinsitute = len(list(num))
    return {
        "Response": "OK", "Number of Insitutes": numinsitute, "Number of Students": studentnum
    }


# To insert Insitute
@router.post("/insitute")
def insituteInsert(name: str):
    new = Insitute(name=name)
    Insitute.insert(new)

    return {"Response": "Done"}
