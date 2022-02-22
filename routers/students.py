from fastapi import APIRouter, File, HTTPException, UploadFile, Form, Query, Depends
from starlette.responses import StreamingResponse
from models import session, Institute, Student, Student_Installment, Installment, Attendance, Student_Attendance
from typing import Optional
import qrcode
from PIL import ImageDraw, ImageFont, Image
import arabic_reshaper
from bidi.algorithm import get_display
from sqlalchemy import desc
import os
from io import BytesIO
from fastapi.responses import FileResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

router = APIRouter()


# Function to get correct path optimized with windows directory
# def get_path():
#     path = pathlib.Path('.')
#     full_path = path.absolute()
#     my_path = full_path.as_posix()
#     return my_path


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
    imagname = '{}-{}.png'.format(id_num, arabic)
    my_path = './qr/' + institute + '/' + imagname
    img.save(my_path, 'PNG')
    return {
        "qrpath": my_path

    }


def photo_save(photo, _id, name, institute):
    img = Image.open(photo)
    image = '{}-{}.jpg'.format(_id, name)
    my_path = './images/' + institute + '/' + image
    img.save(my_path, 'JPEG')
    return {
        "image_path": my_path
    }


# To get Institutes Number , Students
@router.get("/main-admin")
async def main_admin():
    try:
        students = session.query(Student)
        banned = session.query(Student).filter(Student.banned == 1)
        institutes = session.query(Institute)

        result = {
            "Response": "OK",
            "students_count": students.count(),
            "banned_count": banned.count(),
            "institutes_count": institutes.count(),
            "institutes": [institute.format() for institute in institutes.all()]

        }
        for institute in result["institutes"]:
            student_count = students.join(
                Institute, Student.institute_id == Institute.id).filter(institute["id"] == Student.institute_id).count()
            attendance = session.query(Attendance).filter_by(institute_id=institute["id"]).order_by(
                desc(Attendance.date)).limit(1).all()
            attendance = [att for att in attendance]

            institute.update({'students_institute_count': student_count})
            if attendance:
                attendance = attendance.pop()
                daily_attendance = session.query(Student_Attendance).filter_by(attendance_id=attendance.id,
                                                                               attended=1).count()
                institute.update({'daily_attendance': daily_attendance})
            else:
                institute.update({'daily_attendance': 0})
        return result

    except:
        raise StarletteHTTPException(404, "Not Found")


# To insert Institute
@router.post("/institute")
def post_institute(name: str):
    try:
        new = Institute(name=name)
        if 'qr' not in os.listdir("./"):
            os.makedirs('./qr')
        if 'images' not in os.listdir("./"):
            os.makedirs('./images')
        if name not in os.listdir('./qr'):
            os.makedirs('./qr/' + name)
        if name not in os.listdir('./images'):
            os.makedirs('./images/' + name)
        Institute.insert(new)
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
        os.rename("./qr/" + new.name, "./qr/" + name)
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
                 photo: bytes = File(None)):
    try:
        newstudent = Student(name=name, dob=dob, institute_id=institute_id, phone=phone,
                             note=note)

        Student.insert(newstudent)
        institute = session.query(Institute).get(institute_id)

        institute_name = institute.name

        query = session.query(Student).get(newstudent.id)

        attendance = session.query(Attendance).filter_by(
            institute_id=institute_id).order_by(
            desc(Attendance.date)).limit(1).all()
        attendance_id = [_id.format()['id'] for _id in attendance]
        for _id in attendance_id:
            new = Student_Attendance(
                student_id=newstudent.id, attendance_id=_id)
            session.add(new)
        session.commit()

        if photo is not None:
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
            session.add(new_install)
        session.commit()
        return {"success": True}, 200
    except:
        raise StarletteHTTPException(500, "Internal Server Error")


# to change student info
@router.patch('/student')
def patch_student(student_id, name: str, dob, institute_id, ban: int = 0,
                  note: Optional[str] = "لا يوجد "):
    try:
        query = session.query(Student).get(student_id)
        query.name = name
        query.dob = dob
        query.institute_id = institute_id
        query.note = note
        query.banned = ban
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


# Delete student by ID
@router.delete('/student')
def delete_student(student_id: int):
    try:
        query = session.query(Student).get(student_id)
        if query.photo is not None:
            os.remove(query.photo)
        if os.path.exists(query.qr):
            os.remove(query.qr)
        Student.delete(query)
        return {
            'success': True

        }
    except:
        raise StarletteHTTPException(500, "Internal Server Error")


# To change Qrpath
@router.patch('/qr')
def qr(student_id, qr: str):
    try:
        query = session.query(Student).get(student_id)
        query.qr = qr
        Student.update(query)
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
@router.get("/students")
def student_info(institute_id: int = None, number_of_students: int = 100, page: int = 1, search: str = None):
    try:
        if institute_id is not None:
            if search is None:
                count = session.query(Student).join(Institute, Student.institute_id == Institute.id).filter(
                    Student.institute_id == institute_id).count()
                student_join = session.query(Student).join(Institute, Student.institute_id == Institute.id).filter(
                    Student.institute_id == institute_id).order_by(Student.name).limit(number_of_students).offset(
                    (page - 1) * number_of_students
                )
            else:
                count = session.query(Student).join(Institute, Student.institute_id == Institute.id).filter(
                    Student.institute_id == institute_id, Student.name.like('%{}%'.format(search))).count()
                student_join = session.query(Student).join(Institute, Student.institute_id == Institute.id).filter(
                    Student.institute_id == institute_id, Student.name.like('%{}%'.format(search))).order_by(
                    Student.name).limit(
                    number_of_students).offset((page - 1) * number_of_students)


            students = [stu.format() for stu in student_join]
            if count <= number_of_students:
                pages = 1
            else:
                pages = int(round(count / number_of_students))
            return {"students": students,
                    "total_pages": pages,
                    "total_students": count,
                    "page": page

                    }
        else:
            if search is not None:
                count = session.query(Student).join(Institute, Student.institute_id == Institute.id).filter(Student.name.like('%{}%'.format(search))).count()
                student_join = session.query(Student).join(Institute, Student.institute_id == Institute.id).filter(Student.name.like('%{}%'.format(search))).order_by(
                    Student.name).limit(
                    number_of_students).offset((page - 1) * number_of_students)
            else:
                count = session.query(Student).join(Institute, Student.institute_id == Institute.id).count()
                student_join = session.query(Student).join(Institute, Student.institute_id == Institute.id).order_by(
                    Student.name).limit(
                    number_of_students).offset((page - 1) * number_of_students)

            students = [stu.format() for stu in student_join]
            if count <= number_of_students:
                pages = 1
            else:
                pages = int(round(count / number_of_students))
            return {"students": students,
                    "total_pages": pages,
                    "total_students": count,
                    "page": page

                    }

    except:
        raise StarletteHTTPException(404, "Not Found")


@router.get("/banned-students")
def student_info(institute_id: int = None, number_of_students: int = 100, page: int = 1, search: str = None):
    try:
        if institute_id is not None:
            if search is None:
                count = session.query(Student).join(Institute, Student.institute_id == Institute.id).filter(
                    Student.institute_id == institute_id).filter(Student.banned==1).count()
                student_join = session.query(Student).join(Institute, Student.institute_id == Institute.id).filter(
                    Student.institute_id == institute_id, Student.banned==1).order_by(Student.name).limit(number_of_students).offset(
                    (page - 1) * number_of_students
                )
            else:
                count = session.query(Student).join(Institute, Student.institute_id == Institute.id).filter(
                    Student.institute_id == institute_id, Student.name.like('%{}%'.format(search)), Student.banned==1).count()
                student_join = session.query(Student).join(Institute, Student.institute_id == Institute.id).filter(
                    Student.institute_id == institute_id, Student.name.like('%{}%'.format(search)), Student.banned==1).order_by(
                    Student.name).limit(
                    number_of_students).offset((page - 1) * number_of_students)


            students = [stu.format() for stu in student_join]
            if count <= number_of_students:
                pages = 1
            else:
                pages = int(round(count / number_of_students))
            return {"students": students,
                    "total_pages": pages,
                    "total_students": count,
                    "page": page

                    }
        else:
            if search is not None:
                count = session.query(Student).join(Institute, Student.institute_id == Institute.id).filter(Student.name.like('%{}%'.format(search))).count()
                student_join = session.query(Student).join(Institute, Student.institute_id == Institute.id).filter(Student.name.like('%{}%'.format(search)), Student.banned==1).order_by(
                    Student.name).limit(
                    number_of_students).offset((page - 1) * number_of_students)
            else:
                count = session.query(Student).join(Institute, Student.institute_id == Institute.id).filter(Student.banned==1).count()
                student_join = session.query(Student).join(Institute, Student.institute_id == Institute.id).filter(Student.banned==1).order_by(
                    Student.name).limit(
                    number_of_students).offset((page - 1) * number_of_students)

            students = [stu.format() for stu in student_join]
            if count <= number_of_students:
                pages = 1
            else:
                pages = int(round(count / number_of_students))
            return {"students": students,
                    "total_pages": pages,
                    "total_students": count,
                    "page": page

                    }

    except:
        raise StarletteHTTPException(404, "Not Found")

# To get students by institute
# @router.get("/students-institute")
# def student_institute(institute_id, number_of_students: int = 100, page: int = 1, search: str = None):
#     try:
#         if search is None:
#             count = session.query(Student).join(Institute, Student.institute_id == Institute.id).filter(
#                 Student.institute_id == institute_id).count()
#             student_join = session.query(Student).join(Institute, Student.institute_id == Institute.id).filter(
#                 Student.institute_id == institute_id).order_by(Student.name).limit(number_of_students).offset(
#                 (page - 1) * number_of_students)
#
#             students = [stu.format() for stu in student_join]
#             if count <= number_of_students:
#                 pages = 1
#             else:
#                 pages = int(round(count / number_of_students))
#             return {"students": students,
#                     "total_pages": pages,
#                     "total_students": count,
#                     "page": page
#
#                     }
#         else:
#             count = session.query(Student).join(Institute, Student.institute_id == Institute.id).filter(
#                 Student.institute_id == institute_id, Student.name.like('%{}%'.format(search))).count()
#             student_join = session.query(Student).join(Institute, Student.institute_id == Institute.id).filter(
#                 Student.institute_id == institute_id, Student.name.like('%{}%'.format(search))).order_by(Student.name
#                                                                                                          ).limit(
#                 number_of_students).offset((page - 1) * number_of_students)
#
#             students = [stu.format() for stu in student_join]
#             if count <= number_of_students:
#                 pages = 1
#             else:
#                 pages = int(round(count / number_of_students))
#             return {"students": students,
#                     "total_pages": pages,
#                     "total_students": count,
#                     "page": page
#
#                     }
#
#     except:
#         raise StarletteHTTPException(404, "Not Found")


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
# @router.get('/students')
# def students(number_of_students: int = 100, page: int = 1, search: str = None):
#     try:
#         if search is None:
#             count = session.query(Student).count()
#             query = session.query(Student).order_by(Student.name).limit(number_of_students).offset(
#                 (page - 1) * number_of_students)
#         else:
#             count = session.query(Student).filter(Student.name.like('%{}%'.format(search))).count()
#             query = session.query(Student).filter(Student.name.like('%{}%'.format(search))).order_by(
#                 Student.name).limit(number_of_students).offset((page - 1) * number_of_students)
#         stu = [record.format() for record in query]
#         if count <= number_of_students:
#             pages = 1
#         else:
#             pages = int(round(count / number_of_students))
#         return {"students": stu,
#                 "total_pages": pages,
#                 "total_students": count,
#                 "page": page
#                 }
#     except:
#         raise StarletteHTTPException(404, "Not Found")


# get students by id
@router.get('/student')
def get_student(student_id: int):
    try:
        return session.query(Student).get(student_id).format()
    except:
        raise StarletteHTTPException(404, "Not Found")


# To get student image & qr by id
@router.get('/photo')
def get_photo(student_id):
    try:
        query = session.query(Student).get(student_id)
        image_path = query.photo
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
        if stud.photo is not None:
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
            session.add(student_instal)
        session.commit()
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


# To get students installments bulky or by institute id


@router.get("/student-install")
def student_install(number_of_students: int = 100, page: int = 1, search: str = None, institute_id: int = None):
    try:
        query = session.query(Student).join(Installment,
                                            Installment.id == Student_Installment.installment_id).join(
            Institute, Institute.id == Student_Installment.institute_id).join(Student_Installment,
                                                                              Student.id ==
                                                                              Student_Installment.student_id).limit(
            number_of_students).offset(
            (page - 1) * number_of_students)
        query2 = session.query(Installment).join(
            Institute, Institute.id == Installment.institute_id)

        if institute_id is not None:
            query = session.query(Student).join(Installment,
                                                Installment.id == Student_Installment.installment_id).join(
                Institute, Institute.id == Student_Installment.institute_id).join(Student_Installment,
                                                                                  Student.id ==
                                                                                  Student_Installment.student_id).filter(
                Student.institute_id == institute_id).limit(
                number_of_students).offset(
                (page - 1) * number_of_students)
            query2 = session.query(Installment).join(
                Institute, Institute.id == Installment.institute_id).filter(Installment.institute_id == institute_id)
            if search is not None:
                query = session.query(Student).join(Installment,
                                                    Installment.id == Student_Installment.installment_id).join(
                    Institute, Institute.id == Student_Installment.institute_id).join(Student_Installment,
                                                                                      Student.id ==
                                                                                      Student_Installment.student_id
                                                                                      ).filter(
                    Student.institute_id == institute_id, Student.name.like('%{}%'.format(search))).limit(
                    number_of_students).offset(
                    (page - 1) * number_of_students)

        if search is not None and institute_id is None:
            query = session.query(Student).join(Installment,
                                                Installment.id == Student_Installment.installment_id).join(
                Institute, Institute.id == Student_Installment.institute_id).join(Student_Installment,
                                                                                  Student.id ==
                                                                                  Student_Installment.student_id).filter(
                Student.name.like('%{}%'.format(search))).limit(
                number_of_students).offset(
                (page - 1) * number_of_students)
        count = query.count()
        if count <= number_of_students:
            pages = 1
        else:
            pages = int(round(count / number_of_students))
        result = {'students': [record.students() for record in query],
                  "installments": [record.installment() for record in query2.all()],
                  "page": page,
                  "total_pages": pages,
                  "total_students": count
                  }

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
        query = session.query(Installment).filter_by(
            institute_id=query2.first().institute_id).all()
        result = {'students': [record.students() for record in query2],
                  "installments": [record.installment() for record in query]}
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
# @router.get("/student-install-institute-bid")
# def student_installments_by_institute_id(institute_id, number_of_students: int = 100, page: int = 1):
#     try:
#         count = session.query(Student).filter_by(institute_id=institute_id).count()
#         query2 = session.query(Student).filter_by(institute_id=institute_id).limit(number_of_students).offset(
#             (page - 1) * number_of_students)
#         if count <= number_of_students:
#             pages = 1
#         else:
#             pages = int(round(count / number_of_students))
#         result = {'students': [record.students() for record in query2]}
#         for stu in result["students"]:
#             query = session.query(Student_Installment).filter_by(
#                 student_id=stu['id']).all()
#             dicto = {}
#             newlist = []
#             stu['installment_received'] = {}
#             for record in [record1.received() for record1 in query]:
#                 dicto.update({"id": record['id'],
#                               "received": record['received'],
#                               "installment_id": record['installment_id']})
#                 newlist.append(dicto)
#                 dicto = {}
#             stu['installment_received'] = newlist
#         return {"students": result,
#                 "total_pages": pages,
#                 "total_students": count,
#                 "page": page
#                 }
#     except:
#         raise StarletteHTTPException(404, "Not Found")


# To change student installment bulky by installment_id
@router.patch('/student-install-bid')
def student_installments_by_install_id(installment_id: int):
    query = session.query(Student_Installment).filter_by(
        installment_id=installment_id).all()
    for record in query:
        record.receive = 1
        session.add(record)
    session.commit()
    return {
        "success": True
    }


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
