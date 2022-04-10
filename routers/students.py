from fastapi import APIRouter, File, HTTPException, UploadFile, Form, Query, Depends
from starlette.responses import StreamingResponse
from models.db import Institute, Student, StudentInstallment, Installment, Attendance, StudentAttendance
from typing import Optional
import qrcode
from tortoise.query_utils import Q, Prefetch
from tortoise.transactions import in_transaction
from PIL import ImageDraw, ImageFont, Image
import arabic_reshaper
from bidi.algorithm import get_display
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
        students = await Student.all().count()
        unbanned = await Student.filter(banned=0).all().count()
        banned = await Student.filter(banned=1).all().count()
        institutes_count = await Institute.all().count()
        institutes = await Institute.all()
        institutes = [n.__dict__ for n in institutes]
        result = {
            "Response": "OK",
            "students_count": students,
            "unbanned_count": unbanned,
            "banned_count": banned,
            "institutes_count": institutes_count,
            "institutes": institutes

        }
        for institute in result["institutes"]:
            student_count = await Student.filter(institute_id=institute['id'], banned=0).all().count()
            attendance = await Attendance.filter(institute_id=institute["id"]).order_by('-date').all()
            # attendance = [att for att in attendance]

            institute.update({'students_institute_count': student_count})
            if attendance:
                attendance = attendance[-1]
                daily_attendance = await StudentAttendance.filter(attendance_id=attendance.id,
                                                                  attended=1).count()
                institute.update({'daily_attendance': daily_attendance})
            else:
                institute.update({'daily_attendance': 0})
        return result

    except:
        raise StarletteHTTPException(404, "Not Found")


# To insert Institute
@router.post("/institute")
async def post_institute(name: str):
    try:
        async with in_transaction() as conn:
            new = Institute(name=name)
            if 'qr' not in os.listdir("./"):
                os.makedirs('./qr')
            if 'images' not in os.listdir("./"):
                os.makedirs('./images')
            if name not in os.listdir('./qr'):
                os.makedirs('./qr/' + name)
            if name not in os.listdir('./images'):
                os.makedirs('./images/' + name)
            await new.save(using_db=conn)
            return {"success": True}
    except:
        raise StarletteHTTPException(500, "Internal Server Error")


# To get Institutes
@router.get('/institute')
async def get_institute():
    try:
        return {'success': True,
                "institutes": await Institute.all()}
    except:
        raise StarletteHTTPException(404, "Not Found")


# Update institute
@router.patch('/institute')
async def patch_institute(institute_id: int, name: str):
    try:
        new = await Institute.filter(id=institute_id).first()
        os.rename("./qr/" + new.name, "./qr/" + name)
        await Institute.filter(id=institute_id).update(name=name)
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
async def post_student(name: str = Query("name"),
                 dob: Optional[str] = Query("dob"),
                 institute_id: int = Query("institute_id"),
                 phone: Optional[int] = Query("phone"),
                 note: Optional[str] = Query("note"),
                 photo: bytes = File(None)):
    try:
        async with in_transaction() as conn:
            new_student = Student(name=name, dob=dob, institute_id=institute_id, phone=phone,
                                  note=note)

            await new_student.save(using_db=conn)
            institute_name = await Institute.filter(id=institute_id).first()
            institute_name = institute_name.name
            query = await Student.filter(id=new_student.id).first()

            attendance = await Attendance.filter(
                institute_id=institute_id).order_by(
                '-date').limit(1).all()
            attendance_id = [_id.id for _id in attendance]
            for _id in attendance_id:
                new = StudentAttendance(
                    student_id=new_student.id, attendance_id=_id)
                await new.save(using_db=conn)
            if photo is not None:
                photo = BytesIO(photo)
                image = photo_save(photo, query.id, query.name,
                                   institute_name)
                query.photo = image['image_path']
            qr = qr_gen(query.id, name, institute_name)
            await Student.filter(id=new_student.id).update(qr=qr['qrpath'])
            installment = await Installment.filter(
                institute_id=institute_id).all()
            for _ in installment:
                new_install = StudentInstallment(student_id=query.id, institute_id=institute_id,
                                                 installment_id=_.id)
                await new_install.save(using_db=conn)
            return {"success": True}, 200
    except:
        raise StarletteHTTPException(500, "Internal Server Error")


# to change student info
@router.patch('/student')
async def patch_student(student_id, name: str, dob, institute_id, ban: int = 0,
                  note: Optional[str] = "لا يوجد "):
    try:
        institute = await Institute.filter(id=institute_id).first()
        institute_name = institute.name
        new = qr_gen(student_id, name, institute_name)
        await Student.filter(id=student_id).update(name=name, dob=dob, institute_id=institute_id,
                                                   note=note, banned=banned, qr=new['qrpath'])
        return {
            'success': True
        }
    except:
        raise StarletteHTTPException(500, "Internal Server Error")


# Delete student by ID
@router.delete('/student')
async def delete_student(student_id: int):
    try:
        query = await Student.filter(id=student_id).first()
        if query.photo is not None:
            os.remove(query.photo)
        if os.path.exists(query.qr):
            os.remove(query.qr)
        await Student.filter(id=student_id).delete()
        return {
            'success': True

        }
    except:
        raise StarletteHTTPException(500, "Internal Server Error")


# To change Qrpath
@router.patch('/qr')
async def qr(student_id, qr: str):
    try:
        await Student.filter(id=student_id).update(qr=qr)
        return {
            'success': True
        }
    except:
        raise StarletteHTTPException(500, "Internal Server Error")


# To change ban state of student
@router.patch('/banned')
async def banned(student_id: int, ban: int = 0):
    try:
        await Student.filter(id=student_id).update(banned=ban)
        return {
            "success": True
        }
    except:
        raise StarletteHTTPException(500, "Internal Server Error")


# To get students info by institute
@router.get("/students")
async def student_info(institute_id: int = None, number_of_students: int = 100, page: int = 1, search: str = None):
    try:
        if institute_id is not None:
            if search is None:
                count = await Student.filter(institute_id=institute_id).all().count()
                student_join = await Student.filter(institute_id=institute_id
                                                    ).order_by('name').limit(number_of_students).offset(
                    (page - 1) * number_of_students
                ).prefetch_related('institute').all()
            else:
                count = await Student.filter(institute_id=institute_id, name__icontains=search).count()
                student_join = await Student.filter(institute_id=institute_id, name__icontains=search).order_by(
                    'name').limit(
                    number_of_students).offset((page - 1) * number_of_students).prefetch_related('institute').all()

            all_data = []
            for d in student_join:
                d = d.__dict__
                d['institute'] = d['_institute']
                del d['_institute']
                del d['institute_id']
                all_data.append(d)
            if count <= number_of_students:
                pages = 1
            else:
                pages = int(round(count / number_of_students))
            return {"students": all_data,
                    "total_pages": pages,
                    "total_students": count,
                    "page": page

                    }
        else:
            if search is not None:
                count = await Student.filter(name__icontains=search).all().count()
                student_join = await Student.filter(name__icontains=search).order_by(
                    'name').limit(
                    number_of_students).offset((page - 1) * number_of_students).prefetch_related('institute').all()
            else:
                count = await Student.all().count()
                student_join = await Student.filter().order_by(
                    'name').limit(
                    number_of_students).offset((page - 1) * number_of_students).prefetch_related('institute').all()

            all_data = []
            for d in student_join:
                d = d.__dict__
                d['institute'] = d['_institute']
                del d['_institute']
                del d['institute_id']
                all_data.append(d)

            if count <= number_of_students:
                pages = 1
            else:
                pages = int(round(count / number_of_students))
            return {"students": student_join,
                    "total_pages": pages,
                    "total_students": count,
                    "page": page

                    }

    except:
        raise StarletteHTTPException(404, "Not Found")


@router.get("/banned-students")
async def student_info(institute_id: int = None, number_of_students: int = 100, page: int = 1, search: str = None):
    try:
        if institute_id is not None:
            if search is None:
                count = await Student.filter(institute_id=institute_id, banned=1).all().count()
                student_join = await Student.filter(institute_id=institute_id, banned=1).order_by('name').limit(
                    number_of_students).offset(
                    (page - 1) * number_of_students
                ).prefetch_related('institute')
            else:
                count = await Student.filter(institute_id=institute_id, banned=1, name__icontains=search).all().count()
                student_join = await Student.filter(institute_id=institute_id, banned=1,
                                                    name__icontains=search).order_by('name').limit(
                    number_of_students).offset(
                    (page - 1) * number_of_students
                ).prefetch_related('institute')

            students = student_join
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
                count = await Student.filter(banned=1, name__icontains=search).all().count()
                student_join = await Student.filter(banned=1,
                                                    name__icontains=search).order_by('name').limit(
                    number_of_students).offset(
                    (page - 1) * number_of_students
                ).prefetch_related('institute')
            else:
                count = await Student.filter(banned=1).all().count()
                student_join = await Student.filter(banned=1).order_by('name').limit(
                    number_of_students).offset(
                    (page - 1) * number_of_students
                ).prefetch_related('institute')

            students = student_join
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


# to get installment of students by student id and install id
@router.get("/student-installment-bid")
async def install_student(student_id, install_id):
    try:
        install_student = await StudentInstallment.filter(student_id=student_id,
                                                          installment_id=install_id).all(

        ).prefetch_related('student', 'installment')

        return install_student
    except:
        raise StarletteHTTPException(404, "Not Found")


# get students by id
@router.get('/student')
async def get_student(student_id: int):
    try:
        stud = await Student.filter(id=student_id).first().prefetch_related('institute')
        stud = stud.__dict__
        stud['institute'] = stud['_institute']
        del stud['_institute']
        del stud['institute_id']
        return stud
    except:
        raise StarletteHTTPException(404, "Not Found")


# To get student image & qr by id
@router.get('/photo')
async def get_photo(student_id):
    try:
        query = await Student.filter(id=student_id).first()
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
async def patch_photo(student_id: int, photo: bytes = File("photo")):
    try:
        photo = BytesIO(photo)
        stud = await Student.filter(id=student_id).first()
        institute = await Institute.filter(id=stud.institute).first()
        if stud.photo is not None:
            os.remove(stud.photo)
        save = photo_save(photo, student_id, stud.name, institute.name)
        await Student.filter(id=student_id).update(photo=save['image_path'])
        return {
            'success': True
        }
    except:
        raise StarletteHTTPException(500, "internal Server Error")


@router.get('/qr')
async def get_qr(student_id):
    try:
        query = await Student.filter(id=student_id).first()
        qr_path = query.qr
        img = Image.open(qr_path)
        buf = BytesIO()
        img.save(buf, 'png')
        buf.seek(0)
        return StreamingResponse(buf, media_type="image/png")

    except:
        raise StarletteHTTPException(404, "Not Found")


# To insert Installment


@router.post("/installment")
async def post_installment(name: str, date: str, institute_id: int):
    try:
        async with in_transaction() as conn:
            new = Installment(name=name, date=date,
                              institute_id=institute_id)
            await new.save(using_db=conn)
            students = await Student.filter(
                institute_id=institute_id).all()

            for stu in students:
                student_instal = StudentInstallment(installment_id=new.id, student_id=stu.id,
                                                     institute_id=stu.institute)
                await student_instal.save(using_db=conn)
            return {"success": True}
    except:
        raise StarletteHTTPException(500, "internal Server Error")


# To change installment
@router.patch('/installment')
async def patch_installment(name: str, institute_id: int, date: str, _id: int):
    try:
        await Installment.filter(id=_id).update(name=name, date=date, institute_id=institute_id)
        return {"success": True}
    except:
        raise StarletteHTTPException(500, "internal Server Error")


# To insert student Installment

@router.post("/student-installment")
async def student_installment(student_id: int, install_id: int, received: int, institute_id):
    try:
        async with in_transaction() as conn:
            new = StudentInstallment(
                student_id=student_id, installment_id=install_id, received=received, institute_id=institute_id)
            await new.save(using_db=conn)
        return {
            "success": True
        }
    except:
        raise StarletteHTTPException(500, "internal Server Error")


# To change student installment
@router.patch('/student-installment')
async def patch_student_installment(student_installment_id: int, receive: int
                              ):
    try:
        await StudentInstallment.filter(id=student_installment_id).update(receive=receive)
        return {
            "success": True
        }
    except:
        raise StarletteHTTPException(500, "internal Server Error")


# To get students installments bulky or by institute id


@router.get("/student-install")
async def student_install(number_of_students: int = 100, page: int = 1, search: str = None, institute_id: int = None):
    try:
        query = await Student.filter().limit(
            number_of_students).offset(
            (page - 1) * number_of_students)
        query2 = await Installment.all().prefetch_related('institute')

        if institute_id is not None:
            query = await Student.filter(institute_id=institute_id).limit(
                number_of_students).offset(
                (page - 1) * number_of_students).all()
            query2 = await Installment.filter(institute_id=institute_id).all().prefetch_related('institute')
            if search is not None:
                query = await Student.filter(institute_id=institute_id, name__icontains=search).limit(
                    number_of_students).offset(
                    (page - 1) * number_of_students).all()

        if search is not None and institute_id is None:
            query = await Student.filter(name__icontains=search).limit(
                number_of_students).offset(
                (page - 1) * number_of_students).all()
        count = len(query)
        if count <= number_of_students:
            pages = 1
        else:
            pages = int(round(count / number_of_students))
        query = [n.__dict__ for n in query]
        result = {'students': query,
                  "installments": query2,
                  "page": page,
                  "total_pages": pages,
                  "total_students": count
                  }

        for stu in result["students"]:
            query = await StudentInstallment.filter(student_id=stu['id']).all()
            dicto = {}
            newlist = []
            stu['installment_received'] = {}
            for record in query:
                dicto.update({"id": record.id,
                              "received": record.receive,
                              "installment_id": record.installment})
                newlist.append(dicto)
                dicto = {}

            stu['installment_received'] = newlist

        return result
    except:
        raise StarletteHTTPException(404, "Not Found")


# To get student installments by id student
@router.get('/student-install-bid')
async def get_student_installment(student_id):
    try:
        query2 = await Student.filter(id=student_id).first().prefetch_related('institute')
        query = await Installment.filter(institute_id=query2.institute.id).all().prefetch_related('institute')
        result = {'students': query2,
                  "installments": query}

        query = await StudentInstallment.filter(student_id=query2.id).all()
        dicto = {}
        newlist = []
        stu = query2.__dict__

        stu['installment_received'] = {}
        for record in query:
            dicto.update({"id": record.id,
                          "received": record.receive,
                          "installment_id": record.installment})
            newlist.append(dicto)
            dicto = {}

        stu['installment_received'] = newlist
        result = {'students': stu,
                  "installments": query}
        return result
    except:

        raise StarletteHTTPException(404, "Not Found")


# To change student installment bulky by installment_id
@router.patch('/student-install-bid')
async def student_installments_by_install_id(installment_id: int):
    await StudentInstallment.filter(installment_id=installment_id).update(receive=1)
    return {
        "success": True
    }


# To get institutes
@router.get('/students-form')
async def students_form():
    try:
        institutes = await Institute.all()
        form = {
            "institutes": institutes
        }
        return form
    except:
        raise StarletteHTTPException(404, "Not Found")
