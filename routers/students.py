from fastapi import APIRouter
from models import session, engine, Base, Institute, Student, Student_Installment, Installment
from typing import Optional
import json
import qrcode
from PIL import ImageDraw, ImageFont
import arabic_reshaper
from bidi.algorithm import get_display
import pathlib

router = APIRouter()


# To get Institutes Number , Students
@router.get("/main-admin")
def main_admin():
    students = session.query(Student)
    institutes = session.query(Institute)

    result = {
        "Response": "OK",
        "students_count": students.count(),
        "institutes_count": institutes.count(),
        "institutes": [institute.format() for institute in institutes.all()]

    }
    for institute in result["institutes"]:
        student_count = students.join(
            Institute, Student.institute_id == Institute.id).filter(institute["id"] == Student.institute_id).count()

        institute.update({'students_institute_count': student_count})
    return result


# To insert Institute
@router.post("/institute")
def instituteInsert(name: str):
    new = Institute(name=name)
    Institute.insert(new)

    return {"Response": "Done"}


# To insert Student
@router.post("/studentInsert")
def studentInsert(name: str, batch: int, dob: Optional[str], institute_id: int, phone: Optional[int],
                  note: Optional[str] = "لا يوجد"):
    newstudent = Student(name=name, dob=dob, institute_id=institute_id, phone=phone, note=note,
                         batch=batch)
    Student.insert(newstudent)
    query = session.query(Student).get(newstudent.id)
    qr = qrgen(query.id, name)
    query.qr = qr['qrpath']
    Student.update(query)
    return {"Response": "Done"}


# To get students info by institute and batch
@router.get("/studentInfo/<int:institute_id>/<int:batch>")
def studentInfo(institute_id, batch):
    studentJoin = session.query(Student).join(Institute, Student.institute_id == Institute.id).filter(
        Student.institute_id == institute_id, Student.batch == batch).all()

    studentsinfo1 = [stu.format() for stu in studentJoin]

    return studentsinfo1


# to get intallement of students by student id and install id
@router.get("/studentInstallementbyid")
def installStudent(student_id, install_id):
    installstudent = session.query(Student_Installment).join(Student,
                                                             Student_Installment.student_id == Student.id).join(
        Installment, Student_Installment.installment_id == Installment.id)
    query = installstudent.filter(Student_Installment.student_id ==
                                  student_id, Student_Installment.installment_id == install_id).all()
    liststudentinstall = [inst.format() for inst in query]
    return liststudentinstall


# To insert Installment

@router.post("/installmentInsert")
def installmentInsert(name: str, date: str, institute_id: int):
    new = Installment(name=name, date=date, institute_id=institute_id)
    Installment.insert(new)
    return {"Response": "Done"}


# To insert student Installment

@router.post("/studentInstllinsert")
def studentInstallinsert(student_id: int, install_id: int, received: str, institute_id):
    received = json.loads(received.lower())
    new = Student_Installment(
        student_id=student_id, installment_id=install_id, received=received, institute_id=institute_id)
    Student_Installment.insert(new)
    return {
        "Response": "OK"
    }


# To get students installements bulky


@router.get("/studentInstall")
def studentInstall():
    # query = session.query(Student_Installment).join(Installment, Installment.id == Student_Installment.installment_id).join(
    #    Institute, Institute.id == Student_Installment.institute_id).join(Student, Student.id == Student_Installment.student_id)
    # query = query.filter(Student_Installment.institute_id == institute_id).all()
    installment = {}
    query = session.query(Student).all()
    query2 = session.query(Student_Installment)
    query3 = session.query(Installment).all()
    studen_json = {
        "Students": [], "Installments": []
    }
    student = {}
    installNum = 1
    installl = {}
    for stu in query:
        student['id'] = stu.format()['id']
        student['name'] = stu.format()['name']
        student["institute_id"] = stu.format()['institute_id']
        student_id = stu.format()['id']
        print()
        for install in query2.filter_by(student_id=student_id):
            if install.received()['received']:
                installl[installNum] = "true"
            else:
                installl[installNum] = "false"
            student["installment_received"] = installl

            installNum += 1
        installl = {}
        studen_json['Students'].append(student)
        student = {}
        installNum = 1
    for install in query3:
        installment['id'] = install.format()['id']
        installment['name'] = install.format()['name']
        installment['institute_id'] = install.format()['institute_id']
        installment['institute_name'] = install.format()['institute_name']
        installment['date'] = install.format()['date']
        studen_json['Installments'].append(installment)
        installment = {}
    return studen_json


# Function to generate qr image with student is and name embedded in it
def qrgen(id, name):
    id = str(id)
    arabic = name
    name = arabic_reshaper.reshape(arabic)
    name = get_display(name, upper_is_rtl=True)
    img = qrcode.make(id + "|" + "besmarty")
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype('arial.ttf', 20)
    draw.text((150, 250), name, font=font, align="right")
    path = pathlib.Path('.')
    full_path = path.absolute()
    my_path = full_path.as_posix()
    imagname = '{}.png'.format(arabic)
    my_path = my_path + '/qr/' + imagname
    img.save(my_path, 'PNG')
    return {
        "qrpath": my_path

    }
