from fastapi import APIRouter
from Models import session, engine, Base, Insitute, Student, Student_Installment, Installment
from typing import Optional
import json

router = APIRouter()


# To get Insitutes Number , Students
@router.get("/insituteStudenNum")
def insituteStudentNum():
    num = session.query(Insitute).count()
    num2 = session.query(Student).count()
    return {
        "Response": "OK", "Number of Insitutes": num, "Number of Students": num2
    }


# To insert Insitute
@router.post("/insitute")
def insituteInsert(name: str):
    new = Insitute(name=name)
    Insitute.insert(new)

    return {"Response": "Done"}


# To insert Student
@router.post("/studentInsert")
def studentInsert(name: str, batch: int, dob: Optional[str], insitute_id: int, phone: Optional[int], qr: str,
                  picture: Optional[str], note: Optional[str] = "لا يوجد"):
    newstudent = Student(name=name, dob=dob, insitute_id=insitute_id, phone=phone, qr=qr, note=note,
                         picture=picture, batch=batch)
    Student.insert(newstudent)
    return {"Response": "Done"}


# To get students info by insitute and batch
@router.get("/studentInfo/<int:insitute_id>/<int:batch>")
def studentInfo(insitute_id, batch):
    studentJoin = session.query(Student).join(Insitute, Student.insitute_id == Insitute.id).filter(
        Student.insitute_id == insitute_id, Student.batch == batch).all()

    studentsinfo1 = [stu.format() for stu in studentJoin]

    return studentsinfo1


# to get intallement of students by student id and install id
@router.get("/studentInstallement")
def installStudent(student_id, install_id):
    installstudent = session.query(Student_Installment).join(Student, Student_Installment.student_id == Student.id).join(Installment, Student_Installment.installment_id == Installment.id)
    query = installstudent.filter(Student_Installment.student_id == student_id, Student_Installment.installment_id == install_id).all()
    liststudentinstall = [inst.format() for inst in query]
    return liststudentinstall


# To insert Installment

@router.post("/installmentInsert")
def installmentInsert(name: str, date: str, insitute_id: int):
    new = Installment(name=name, date=date, insitute_id=insitute_id)
    Installment.insert(new)
    return {"Response": "Done"}


# To insert student Installment

@router.post("/studentInstllinsert")
def studentInstallinsert(student_id: int, install_id: int, received: str):
    received = json.loads(received.lower())
    new = Student_Installment(student_id=student_id, installment_id=install_id, received=received)
    Student_Installment.insert(new)
    return {
        "Response": "OK"
    }

