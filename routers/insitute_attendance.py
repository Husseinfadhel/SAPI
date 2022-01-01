from fastapi import APIRouter, Depends
from models import session, engine, Base, Institute, Student, Attendance, Student_Attendance, \
    Student_Installment, \
    Installment
from sqlalchemy import desc, or_, and_
from sqlalchemy.orm import joinedload
from starlette.exceptions import HTTPException as StarletteHTTPException
from typing import Optional

from datetime import datetime

now = datetime.now()

now_day = now.strftime('%Y-%m-%d')
now_time = now.strftime("%H:%M")

router = APIRouter()


# insert Attendance
@router.post('/attendance')
def post_attendance(institute_id):
    try:
        if now_day != "":
            query = session.query(Attendance).filter_by(
                date=now_day, institute_id=institute_id).all()

            if query == []:
                new = Attendance(date=now_day,
                                 institute_id=institute_id)
                Attendance.insert(new)
                query = session.query(Student).filter_by(
                    institute_id=institute_id).all()
                for stu in query:
                    new_attend = Student_Attendance(
                        student_id=stu.id, attendance_id=new.id)
                    session.add(new_attend)
                session.commit()
            return {
                "success": True
            }
        else:
            raise StarletteHTTPException(402, "Include Date")

    except:
        raise StarletteHTTPException(500, "internal Server Error")


# To change attendance
@router.patch('/attendance')
def patch_attendance(_id: int, date: str, institute_id: int):
    try:
        new = session.query(Attendance).get(_id)
        new.date = now_day
        new.institute_id = institute_id
        Attendance.update(new)
        return {
            "success": True
        }
    except:
        raise StarletteHTTPException(500, "internal Server Error")


# get student attendance bulky with pagination
@router.get('/students-attendance')
def students_attendance(number_of_students: int = 100, page: int = 1, institute_id: int = None,
                        search_type: int = None, search1: str = None, search2: str = None):
    try:
        query = None
        query2 = session.query(Attendance).all()
        count_students = session.query(Student).count()
        if institute_id is None:
            query = session.query(Student).order_by(Student.name).limit(number_of_students).offset((page - 1) *
                                                                                                   number_of_students)
        elif institute_id is not None:
            query = session.query(Student).filter_by(institute_id=institute_id).order_by(Student.name).limit(
                number_of_students).offset(
                (page - 1) * number_of_students)
            count_students = session.query(Student).filter_by(institute_id=institute_id).count()
        if search_type is not None:
            if search_type == 1 and institute_id is not None:  # search by student name
                query = session.query(Student).filter(Student.institute_id == institute_id,
                                                      Student.name.like('%{}%'.format(search1))).order_by(Student.name
                                                                                                          ).limit(
                    number_of_students).offset((page - 1) * number_of_students)
                count_students = session.query(Student).filter(Student.institute_id == institute_id,
                                                               Student.name.like('%{}%'.format(search1))).count()
            elif search_type == 1 and institute_id is None:
                query = session.query(Student).filter(
                    Student.name.like('%{}%'.format(search1))).order_by(Student.name).limit(
                    number_of_students).offset((page - 1) * number_of_students)
                count_students = session.query(Student).filter(
                    Student.name.like('%{}%'.format(search1))).count()
            elif search_type == 2:  # search by two date or one
                if search2 is None and institute_id is not None:
                    query = session.query(Student).filter(Student.institute_id == institute_id).order_by(Student.name).limit(
                        number_of_students).offset((page - 1) * number_of_students)
                    count_students = session.query(Student).filter(Student.institute_id == institute_id).count()
                    query2 = session.query(Attendance).filter(Attendance.date == search1).all()
                elif search2 is None and institute_id is None:
                    query = session.query(Student).order_by(Student.name).limit(
                        number_of_students).offset((page - 1) * number_of_students)
                    count_students = session.query(Student).count()
                    query2 = session.query(Attendance).filter(Attendance.date == search1).all()
                else:
                    if institute_id is not None:
                        query = session.query(Student).filter(Student.institute_id == institute_id).order_by(Student.name).limit(
                            number_of_students).offset((page - 1) * number_of_students)
                        count_students = session.query(Student).filter(Student.institute_id == institute_id).count()
                        query2 = session.query(Attendance).filter(and_(Attendance.date >= search1,
                                                                       Attendance.date <= search2)).all()
                    else:
                        query = session.query(Student).order_by(Student.name).limit(
                            number_of_students).offset((page - 1) * number_of_students)
                        count_students = session.query(Student).count()
                        query2 = session.query(Attendance).filter(and_(Attendance.date >= search1,
                                                                       Attendance.date <= search2)).all()
        if search_type == 3:
            attendance = session.query(Student_Attendance).filter(
                and_(Student_Attendance.time >= search1,
                     Student_Attendance.time <= search2))
            for n in attendance:
                query = session.query(Student).filter(Student.id == n.student_id).order_by(Student.name).limit(
                    number_of_students).offset((page - 1) * number_of_students)
                count_students = session.query(Student).filter(Student.id == n.student_id).count()
        students = [record.students() for record in query]
        if count_students <= number_of_students:
            pages = 1
        else:
            pages = int(round(count_students / number_of_students))

        paternalist = {"students": students,
                       "attendance": [record.format() for record in query2],
                       "total_pages": pages,
                       "total_students": count_students,
                       "page": page

                       }

        new_attend = {}
        enlist = []

        for stu in students:  # todo : fixing
            if search_type != 3:
                attendance = session.query(Student_Attendance).filter_by(
                    student_id=stu['id']).all()
            for attend in [att.format() for att in attendance]:
                new_attend['student_attendance_id'] = attend['id']
                new_attend['attended'] = attend['attended']
                new_attend['attendance_id'] = attend['attendance_id']
                new_attend['time'] = attend['time']
                enlist.append(new_attend)
                new_attend = {}
            stu.update({"student_attendance": enlist})
            enlist = []
        return paternalist
    except:
        raise StarletteHTTPException(404, "Not Found")


# get student attendance by institute id
# @router.get('/students-attendance-institute-bid')
# def students_attendance_institute(institute_id: int, number_of_students: int = 100, page: int = 1):
#     query = session.query(Student).filter_by(institute_id=institute_id).limit(number_of_students).offset(
#         (page - 1) * number_of_students)
#     count = session.query(Student).filter_by(institute_id=institute_id).count()
#     if count <= number_of_students:
#         pages = 1
#     else:
#         pages = int(round(count / number_of_students))
#     students = [record.students() for record in query]
#     query2 = session.query(Attendance).filter_by(
#         institute_id=institute_id).all()
#     paternalist = {"students": students,
#                    "attendance": [record.format() for record in query2],
#                    "total_pages": pages,
#                    "total_students": count,
#                    "page": page
#
#                    }
#     new_attend = {}
#     enlist = []
#     for stu in students:
#         attendance = session.query(Student_Attendance).filter_by(
#             student_id=stu['id']).all()
#         for attend in [att.format() for att in attendance]:
#             new_attend['student_attendance_id'] = attend['id']
#             new_attend['attended'] = attend['attended']
#             new_attend['attendance_id'] = attend['attendance_id']
#             new_attend['time'] = attend['time']
#             enlist.append(new_attend)
#             new_attend = {}
#         stu.update({"student_attendance": enlist})
#         enlist = []
#
#     return paternalist


# To change Student Attendance
@router.patch('/students-attendance')
def patch_students_attendance(student_attendance_id: int, attended: int):
    try:
        new = session.query(Student_Attendance).get(student_attendance_id)
        new.attended = attended

        new.time = now_time
        Student_Attendance.update(new)
        query = session.query(Student).get(new.student_id)
        return {
            "success": True,
            "student_id": new.student_id,
            "student_attendance_id": student_attendance_id,
            "student_name": query.name
        }
    except:
        raise StarletteHTTPException(500, "internal Server Error")


# To start students Attendance counting

@router.get('/attendance-start')
def attendance_start(student_id):
    try:
        student = session.query(Student).get(student_id).format()

        total_absence = session.query(Student_Attendance).filter_by(
            student_id=student_id, attended=0).count() - 1

        incremental_absence = session.query(Student_Attendance).join(Attendance).filter(
            Student_Attendance.student_id == student_id).order_by(Attendance.date).all()

        student_attendance_id = session.query(Student_Attendance).join(Attendance).filter(
            Student_Attendance.student_id == student_id).order_by(
            desc(Attendance.date)).limit(1)

        student_attendance_id = [record.format()
                                 for record in student_attendance_id]
        student.update(
            {"student_attendance_id": student_attendance_id[0]['id']})

        attend = [record.format() for record in incremental_absence]
        attend.pop(-1)

        incrementally_absence = 0
        for record in attend:
            if record['attended'] == 0:
                incrementally_absence += 1
            elif record['attended'] == 1:
                incrementally_absence = 0

        attendance_date = session.query(Attendance).get(
            student_attendance_id[0]['attendance_id'])

        installments = session.query(Student_Installment).join(Installment).filter(Student_Installment.student_id
                                                                                   == student_id,
                                                                                   attendance_date.date >= Installment.date).all()
        installments_list = [student.student() for student in installments]
        finalist = []
        stu = {}
        for record in installments_list:
            stu.update(
                {'installment_name': record['install_name'], "received": record["received"],
                 "installment_id": record["installment_id"]})
            finalist.append(stu)
            stu = {}
        student.update({"total_absence": total_absence})
        student.update({"incrementally_absence": incrementally_absence})
        student.update({"installments": finalist})
        return student
    except:
        raise StarletteHTTPException(500, "internal Server Error")
