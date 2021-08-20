from fastapi import APIRouter
from models import session, Institute, Student, Student_Installment, Installment, Batch
from typing import Optional
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


# To get Institutes
@router.get('/institute')
def get_institute():
    query = session.query(Institute).all()
    return {'success': True,
            "institutes": [inst.format() for inst in query]}


# To insert Batch
@router.post("/batch")
def post_batch(batch_num):
    new = Batch(batch_num=batch_num)
    Batch.insert(new)
    return {"success": True}


# To get batch
@router.get('/batch')
def get_batch():
    query = session.query(Batch).all()
    return {"success": True, 'batchs': [batch.format() for batch in query]}


# To insert Student
@router.post("/student")
def post_student(name: str, batch_id: int, dob: Optional[str], institute_id: int, phone: Optional[int],
                 note: Optional[str] = "لا يوجد"):
    newstudent = Student(name=name, dob=dob, institute_id=institute_id, phone=phone, note=note,
                         batch_id=batch_id)
    Student.insert(newstudent)
    query = session.query(Student).get(newstudent.id)
    qr = qr_gen(query.id, name)
    query.qr = qr['qrpath']
    Student.update(query)
    installment = session.query(Installment).filter_by(institute_id=institute_id, batch_id=batch_id).all()
    for _ in installment:
        new_install = Student_Installment(student_id=query.id, institute_id=institute_id,
                                          installment_id=_.format()['id'])
        Student_Installment.insert(new_install)
    return {"success": True}


# To get students info by institute and batch
@router.get("/student-info")
def student_info(institute_id, batch_id):
    student_join = session.query(Student).join(Institute, Student.institute_id == Institute.id).filter(
        Student.institute_id == institute_id, Student.batch_id == batch_id).all()

    students = [stu.format() for stu in student_join]

    return students


# To get students by institute
@router.get("/students-institute")
def student_institute(institute_id):
    student_join = session.query(Student).join(Institute, Student.institute_id == Institute.id).filter(
        Student.institute_id == institute_id).all()

    students = [stu.format() for stu in student_join]

    return students


# to get installment of students by student id and install id
@router.get("/student-installment-bid")
def install_student(student_id, install_id):
    installstudent = session.query(Student_Installment).join(Student,
                                                             Student_Installment.student_id == Student.id).join(
        Installment, Student_Installment.installment_id == Installment.id)
    query = installstudent.filter(Student_Installment.student_id ==
                                  student_id, Student_Installment.installment_id == install_id).all()
    liststudentinstall = [inst.format() for inst in query]
    return liststudentinstall


# To insert Installment

@router.post("/installment")
def post_installment(name: str, date: str, institute_id: int, batch_id):
    new = Installment(name=name, date=date, institute_id=institute_id, batch_id=batch_id)
    Installment.insert(new)
    query = session.query(Student).filter_by(batch_id=batch_id, institute_id=institute_id).all()
    students = [record.students() for record in query]
    for stu in students:
        student_instal = Student_Installment(installment_id=new.id, student_id=stu['id'],
                                             institute_id=stu['institute_id'])
        Student_Installment.insert(student_instal)
    return {"success": True}


# To insert student Installment

@router.post("/student-installment")
def student_installment(student_id: int, install_id: int, received: int, institute_id):
    new = Student_Installment(
        student_id=student_id, installment_id=install_id, received=received, institute_id=institute_id)
    Student_Installment.insert(new)
    return {
        "success": True
    }


# To get students installments bulky


@router.get("/student-install")
def student_install():
    query = session.query(Student).join(Installment,
                                        Installment.id == Student_Installment.installment_id).join(
        Institute, Institute.id == Student_Installment.institute_id).join(Student_Installment,
                                                                          Student.id == Student_Installment.student_id).join(
        Batch, Batch.id == Student.batch_id).all()
    query2 = session.query(Installment).join(Batch, Batch.id == Installment.batch_id).join(Institute, Institute.id ==
                                                                                           Installment.institute_id)
    result = {'students': [record.students() for record in query],
              "installments": [record.installment() for record in query2.all()]}

    for stu in result["students"]:
        query = session.query(Student_Installment).filter_by(student_id=stu['id']).all()
        dicto = {}
        newlist = []
        stu['installment_received'] = {}
        for record in [record1.received() for record1 in query]:
            dicto.update({"id": record['id'],
                          "received": record['received'],
                          "installment_id": record['installment_id']})
            newlist.append(dicto)
            dicto = {}

        stu['installment_received'] = newlist

    return result


# To get student installments by id student
@router.get('/student-install-bid')
def get_student_installment(student_id):
    query2 = session.query(Student).filter_by(id=student_id)
    result = {'students': [record.students() for record in query2]}
    for stu in result["students"]:
        query = session.query(Student_Installment).filter_by(student_id=stu['id']).all()
        dicto = {}
        newlist = []
        stu['installment_received'] = {}
        for record in [record1.received() for record1 in query]:
            dicto.update({"id": record['id'],
                          "received": record['received'],
                          "installment_id": record['installment_id']})
            newlist.append(dicto)
            dicto = {}

        stu['installment_received'] = newlist
    return result


# get students installments by institute id
@router.get("/student-install-institute-bid")
def student_installments_by_institute_id(institute_id):
    query2 = session.query(Student).filter_by(institute_id=institute_id)
    result = {'students': [record.students() for record in query2]}
    for stu in result["students"]:
        query = session.query(Student_Installment).filter_by(student_id=stu['id']).all()
        dicto = {}
        newlist = []
        stu['installment_received'] = {}
        for record in [record1.received() for record1 in query]:
            dicto.update({"id": record['id'],
                          "received": record['received'],
                          "installment_id": record['installment_id']})
            newlist.append(dicto)
            dicto = {}
        stu['installment_received'] = newlist
    return result


# to get installments by institute id and batch id

# Function to generate qr image with student id and name embedded in it
def qr_gen(id_num, name):
    id_num = str(id_num)
    arabic = name
    name = arabic_reshaper.reshape(arabic)
    name = get_display(name, upper_is_rtl=True)
    img = qrcode.make(id_num + "|" + "besmarty")
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
