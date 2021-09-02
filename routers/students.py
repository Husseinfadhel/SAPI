from fastapi import APIRouter, File, HTTPException, UploadFile, Form, Query
from starlette.responses import StreamingResponse

from models import session, Institute, Student, Student_Installment, Installment
from typing import Optional
import qrcode
from PIL import ImageDraw, ImageFont, Image
import arabic_reshaper
from bidi.algorithm import get_display
import pathlib
import os
from io import BytesIO
from fastapi.responses import FileResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

router = APIRouter()


# Function to get correct path optimized with windows directory
def get_path():
    path = pathlib.Path('.')
    full_path = path.absolute()
    my_path = full_path.as_posix()
    return my_path


# Function to generate qr image with student id and name embedded in it

def qr_gen(id_num, name, institute):
    id_num = str(id_num)
    arabic = name
    name = arabic_reshaper.reshape(arabic)
    name = get_display(name, upper_is_rtl=True)
    img = qrcode.make(id_num + "|" + "besmarty")
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype('arial.ttf', 20)
    draw.text((125, 250), name, font=font, align="left")
    my_path = get_path()
    imagname = '{}-{}.png'.format(id_num, arabic)
    my_path = my_path + '/qr/' + institute + '/' + imagname
    img.save(my_path, 'PNG')
    return {
        "qrpath": my_path

    }


def photo_save(photo, _id, name, institute):
    img = Image.open(photo)
    my_path = get_path()
    image = '{}-{}.jpg'.format(_id, name)
    my_path = my_path + '/images/' + institute + '/' + image
    img.save(my_path, 'JPEG')
    return {
        "image_path": my_path
    }


# To get Institutes Number , Students
@router.get("/main-admin")
def main_admin():
    try:
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
    except:
        raise StarletteHTTPException(404, "Not Found")


# To insert Institute
@router.post("/institute")
def post_institute(name: str):
    try:
        new = Institute(name=name)
        Institute.insert(new)
        my_path = get_path()
        if 'qr' not in os.listdir(my_path):
            os.makedirs(my_path + '/qr')
        if 'images' not in os.listdir(my_path):
            os.makedirs(my_path + '/images')
        if name not in os.listdir(my_path + '/qr'):
            os.makedirs(my_path + '/qr/' + name)
        if name not in os.listdir(my_path + '/images'):
            os.makedirs(my_path + '/images/' + name)
        return {"success": True}
    except:
        raise StarletteHTTPException(500, "Internal Server Error")


# To get Institutes
@router.get('/institute')
def get_institute():
    try:
        query = session.query(Institute).all()
        return {'success': True,
                "institutes": [inst.format() for inst in query]}
    except:
        raise StarletteHTTPException(404, "Not Found")


# Update institute
@router.patch('/institute')
def patch_institute(institute_id: int, name: str):
    try:
        new = session.query(Institute).get(institute_id)
        new.name = name
        Institute.update(new)
        return {"success": True}
    except:
        raise StarletteHTTPException(500, "Internal Server Error")


# class Students(BaseModel):
#     name: str
#     dob: Optional[str]
#     institute_id: int
#     phone: Optional[int]
#     note: Optional[str] = "لا يوجد"

# To insert Student

@router.post("/student")
def post_student(name: str = Query("name"),
                 dob: Optional[str] = Query("dob"),
                 institute_id: int = Query("institute_id"),
                 phone: Optional[int] = Query("phone"),
                 note: Optional[str] = Query("note"),
                 photo: bytes = File("photo")):
    try:
        newstudent = Student(name=name, dob=dob, institute_id=institute_id, phone=phone,
                             note=note)

        Student.insert(newstudent)
        institute = session.query(Institute).get(institute_id)

        institute_name = institute.name

        query = session.query(Student).get(newstudent.id)
        photo = BytesIO(photo)
        image = photo_save(photo, query.id, query.name,
                           institute_name)
        query.photo = image['image_path']
        qr = qr_gen(query.id, name, institute_name)
        query.qr = qr['qrpath']
        Student.update(query)
        installment = session.query(Installment).filter_by(
            institute_id=institute_id).all()
        for _ in installment:
            new_install = Student_Installment(student_id=query.id, institute_id=institute_id,
                                              installment_id=_.format()['id'])
            Student_Installment.insert(new_install)
        return {"success": True}, 200
    except:
        raise StarletteHTTPException(500, "Internal Server Error")


# to change student info
@router.patch('/student')
def student(student_id, name: str, dob, institute_id, ban: int = 0,  note: Optional[str] = "لا يوجد"):
    try:
        query = session.query(Student).get(student_id)
        query.name = name
        query.dob = dob
        query.institute_id = institute_id
        query.note = note
        query.banned = ban
        os.remove(query.qr)
        institute = session.query(Institute).filter_by(id=institute_id).all()
        for record in institute:
            institute_name = record.format()['name']
        new = qr_gen(student_id, name, institute_name)
        query.qr = new['qrpath']
        return {
            'success': True
        }
    except:
        raise StarletteHTTPException(500, "Internal Server Error")


# To change ban state of student
@router.patch('/banned')
def banned(student_id: int, ban: int = 0):
    try:
        stud = session.query(Student).get(student_id)
        stud.banned = ban
        Student.update(stud)
        return {
            "success": True
        }
    except:
        raise StarletteHTTPException(500, "Internal Server Error")


# To get students info by institute
@router.get("/student-info")
def student_info(institute_id):
    try:
        student_join = session.query(Student).join(Institute, Student.institute_id == Institute.id).filter(
            Student.institute_id == institute_id).all()

        students = [stu.format() for stu in student_join]

        return students
    except:
        raise StarletteHTTPException(404, "Not Found")


# To get students by institute
@router.get("/students-institute")
def student_institute(institute_id):
    try:
        student_join = session.query(Student).join(Institute, Student.institute_id == Institute.id).filter(
            Student.institute_id == institute_id).all()

        students = [stu.format() for stu in student_join]

        return students
    except:
        raise StarletteHTTPException(404, "Not Found")


# to get installment of students by student id and install id
@router.get("/student-installment-bid")
def install_student(student_id, install_id):
    try:
        installstudent = session.query(Student_Installment).join(Student,
                                                                 Student_Installment.student_id == Student.id).join(
            Installment, Student_Installment.installment_id == Installment.id)
        query = installstudent.filter(Student_Installment.student_id ==
                                      student_id, Student_Installment.installment_id == install_id).all()
        liststudentinstall = [inst.format() for inst in query]
        return liststudentinstall
    except:
        raise StarletteHTTPException(404, "Not Found")


# get students bulky
@router.get('/students')
def students():
    try:
        query = session.query(Student).all()
        stu = [record.format() for record in query]
        return stu
    except:
        raise StarletteHTTPException(404, "Not Found")


# To get student image & qr by id
@router.get('/photo')
def get_photo(student_id):
    try:
        query = session.query(Student).filter_by(id=student_id).all()
        stu = [record.format() for record in query]
        image_path = stu[0]['photo']
        img = Image.open(image_path)
        buf = BytesIO()
        img.save(buf, 'JPEG')
        buf.seek(0)
        return StreamingResponse(buf, media_type="image/jpeg")

    except:
        raise StarletteHTTPException(404, "Not Found")


# To change student's photo

@router.patch('/photo')
def patch_photo(student_id: int, photo: bytes = File("photo")):
    try:
        photo = BytesIO(photo)
        stud = session.query(Student).get(student_id)
        institute = session.query(Institute).get(stud.institute_id)
        os.remove(stud.photo)
        save = photo_save(photo, student_id, stud.name, institute.name)
        stud.photo = save['image_path']
        Student.update(stud)
        return {
            'success': True
        }
    except:
        raise StarletteHTTPException(500, "internal Server Error")


@router.get('/qr')
def get_qr(student_id):
    try:
        query = session.query(Student).filter_by(id=student_id).all()
        stu = [record.format() for record in query]
        qr_path = stu[0]['qr']
        img = Image.open(qr_path)
        buf = BytesIO()
        img.save(buf, 'png')
        buf.seek(0)
        return StreamingResponse(buf, media_type="image/png")

    except:
        raise StarletteHTTPException(404, "Not Found")


# To insert Installment


@router.post("/installment")
def post_installment(name: str, date: str, institute_id: int):
    try:
        new = Installment(name=name, date=date,
                          institute_id=institute_id)
        Installment.insert(new)
        query = session.query(Student).filter_by(
            institute_id=institute_id).all()
        students = [record.students() for record in query]
        for stu in students:
            student_instal = Student_Installment(installment_id=new.id, student_id=stu['id'],
                                                 institute_id=stu['institute_id'])
            Student_Installment.insert(student_instal)
        return {"success": True}
    except:
        raise StarletteHTTPException(500, "internal Server Error")


# To change installment
@router.patch('/installment')
def patch_installment(name: str, institute_id: int, date: str, _id: int):
    try:
        new = session.query(Installment).get(_id)
        new.name = name
        new.date = date
        new.institute_id = institute_id
        Installment.update(new)
        return {"success": True}
    except:
        raise StarletteHTTPException(500, "internal Server Error")


# To insert student Installment

@router.post("/student-installment")
def student_installment(student_id: int, install_id: int, received: int, institute_id):
    try:
        new = Student_Installment(
            student_id=student_id, installment_id=install_id, received=received, institute_id=institute_id)
        Student_Installment.insert(new)
        return {
            "success": True
        }
    except:
        raise StarletteHTTPException(500, "internal Server Error")


# To change student installment
@router.patch('/student-installment')
def patch_student_installment(student_installment_id: int, receive: int
                              ):
    try:
        new = session.query(Student_Installment).get(student_installment_id)
        new.receive = receive
        Student_Installment.update(new)
        return {
            "success": True
        }
    except:
        raise StarletteHTTPException(500, "internal Server Error")


# To get students installments bulky


@router.get("/student-install")
def student_install():
    try:
        query = session.query(Student).join(Installment,
                                            Installment.id == Student_Installment.installment_id).join(
            Institute, Institute.id == Student_Installment.institute_id).join(Student_Installment,
                                                                              Student.id ==
                                                                              Student_Installment.student_id).all()
        query2 = session.query(Installment).join(
            Institute, Institute.id == Installment.institute_id)
        result = {'students': [record.students() for record in query],
                  "installments": [record.installment() for record in query2.all()]}

        for stu in result["students"]:
            query = session.query(Student_Installment).filter_by(
                student_id=stu['id']).all()
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
    except:
        raise StarletteHTTPException(404, "Not Found")


# To get student installments by id student
@router.get('/student-install-bid')
def get_student_installment(student_id):
    try:
        query2 = session.query(Student).filter_by(id=student_id)
        result = {'students': [record.students() for record in query2]}
        for stu in result["students"]:
            query = session.query(Student_Installment).filter_by(
                student_id=stu['id']).all()
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
    except:
        raise StarletteHTTPException(404, "Not Found")


# get students installments by institute id
@router.get("/student-install-institute-bid")
def student_installments_by_institute_id(institute_id):
    try:
        query2 = session.query(Student).filter_by(institute_id=institute_id)
        result = {'students': [record.students() for record in query2]}
        for stu in result["students"]:
            query = session.query(Student_Installment).filter_by(
                student_id=stu['id']).all()
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
    except:
        raise StarletteHTTPException(404, "Not Found")


# To get institutes
@router.get('/students-form')
def students_form():
    try:
        institutes = session.query(Institute).all()
        form = {
            "institutes": [record.format() for record in institutes]
        }
        return form
    except:
        raise StarletteHTTPException(404, "Not Found")
