from fastapi import APIRouter, Depends, status
from tortoise.query_utils import Q, Prefetch
from tortoise.transactions import in_transaction

from models.db import Institute, Student, Attendance, StudentAttendance, \
    StudentInstallment, \
    Installment
from starlette.exceptions import HTTPException as StarletteHTTPException
from typing import Optional

from datetime import datetime

router = APIRouter()


# insert Attendance
@router.post('/attendance')
async def post_attendance(institute_id, date: str):
    # try:
    now = datetime.now()
    async with in_transaction() as conn:
        if date != "":
            query = await Attendance.filter(
                date=date, institute_id=institute_id).all()

            if len(query) == 0:
                new = Attendance(date=date,
                                 institute_id=institute_id)
                await new.save(using_db=conn)
                query = await Student.filter(
                    institute_id=institute_id).all()
                for stu in query:
                    new_attend = StudentAttendance(
                        student_id=stu.id, attendance_id=new.id)
                    await new_attend.save(using_db=conn)

                    incremental_absence = await StudentAttendance.filter(
                        student_id=stu.id).all().prefetch_related(Prefetch('attendance',
                                                                           queryset=Attendance.all().order_by('-date')))

                    attend = [record.__dict__ for record in incremental_absence]
                    attend.pop(-1)

                    incrementally_absence = 0
                    for record in attend:
                        if record['attended'] == 0:
                            incrementally_absence += 1
                        elif record['attended'] == 1:
                            incrementally_absence = 0
                    if incrementally_absence > 3:
                        await Student.filter(id=stu.id).update(banned=1)

            return {
                "success": True
            }
        else:
            raise StarletteHTTPException(402, "Include Date")

    # except:
    #     raise StarletteHTTPException(500, "internal Server Error")


# To change attendance
@router.patch('/attendance')
async def patch_attendance(_id: int, date: str, institute_id: int):
    try:
        await Attendance.filter(id=_id).update(date=date, institute_id=institute_id)
        return {
            "success": True
        }
    except:
        raise StarletteHTTPException(500, "internal Server Error")


atten_student = None


# get student attendance bulky with pagination
@router.get('/students-attendance')
async def students_attendance(number_of_students: int = 100, page: int = 1, institute_id: int = None,
                              search_type: int = None, search1: str = None, search2: str = None):
    global atten_student
    try:
        n = 0
        query = None
        query2 = await Attendance.filter().order_by('-date').all()
        count_students = await Student.all().count()
        if institute_id is None:
            query = await Student.filter().order_by('name').limit(number_of_students).offset((page - 1) *
                                                                                            number_of_students)
        elif institute_id is not None:
            query = await Student.filter(institute_id=institute_id).order_by('name').limit(
                number_of_students).offset(
                (page - 1) * number_of_students)
            count_students = await Student.filter(institute_id=institute_id).count()
            query2 = await Attendance.filter(institute_id=institute_id).order_by(
                '-date').all()
        if search_type is not None:
            if search_type == 1 and institute_id is not None:  # search by student name
                query = await Student.filter(institute_id=institute_id,
                                            name__icontains=search1).order_by('name'
                                                                            ).limit(
                    number_of_students).offset((page - 1) * number_of_students)
                count_students = await Student.filter(institute_id=institute_id,
                                                    name__icontains=search1).count()
            elif search_type == 1 and institute_id is None:
                query = await Student.filter(
                    name__icontains=search1).order_by('name').limit(
                    number_of_students).offset((page - 1) * number_of_students)
                count_students = await Student.filter(
                    name__icontains=search1).count()
            elif search_type == 2:  # search by two date or one
                if search2 is None and institute_id is not None:
                    query = await Student.filter(institute_id=institute_id).order_by(
                        'name').limit(
                        number_of_students).offset((page - 1) * number_of_students)
                    count_students = await Student.filter(institute_id=institute_id).count()
                    query2 = await Attendance.filter(date=search1, institute_id=institute_id).order_by('-date').all()
                elif search2 is None and institute_id is None:
                    query = await Student.filter().order_by('name').limit(
                        number_of_students).offset((page - 1) * number_of_students)
                    count_students = await Student.all().count()
                    query2 = await Attendance.filter(date=search1).order_by('-date').all()
                else:
                    if institute_id is not None:
                        query = await Student.filter(institute_id=institute_id).order_by(
                            'name').limit(
                            number_of_students).offset((page - 1) * number_of_students)
                        count_students = await Student.filter(institute_id=institute_id).count()
                        query2 = await Attendance.filter(Q(date__gte=search1) &
                                                        Q(date__lte=search2),
                                                        institute_id=institute_id).order_by(
                            '-date').all()
                    else:
                        query = await Student.filter().order_by('name').limit(
                            number_of_students).offset((page - 1) * number_of_students)
                        count_students = await Student.all().count()
                        query2 = await Attendance.filter(Q(date__gte=search1) &
                                                        Q(date__lte=search2)).order_by(
                            '-date').all()
        if search_type == 3:
            attendance = await StudentAttendance.filter(
                Q(time__gte=search1) &
                Q(time__lte=search2)).all().prefetch_related('student')

            bulk_attend = attendance
            atten_student = [stude.student for stude in bulk_attend]
            atten_student = list(atten_student)
            n = 1
            query = []
            if len(atten_student) <= 100:
                for cou in atten_student:
                    min_query = await Student.filter(id=cou).all()
                    query.extend(min_query)
            elif len(atten_student) > 100:
                start = (page - 1) * number_of_students
                attended = atten_student[start:start + number_of_students]
                for cou in attended:
                    min_query = await Student.filter(id=cou.id).all()
                    query.extend(min_query)
        if n == 1:
            students = query
            count_students = len(atten_student)
            if count_students <= number_of_students:
                pages = 1
            else:
                pages = int(round(count_students / number_of_students))
        else:
            students = query
            if count_students <= number_of_students:
                pages = 1
            else:
                pages = int(round(count_students / number_of_students))
        students = [n.__dict__ for n in students]
        new_attend = {}
        enlist = []
        for stu in students:
            if search_type != 3:
                print(stu['id'])
                attendance = await StudentAttendance.filter(
                    student_id=stu['id']).all().prefetch_related('attendance')
                for attend in attendance:
                    new_attend['student_attendance_id'] = attend.id
                    new_attend['attended'] = attend.attended
                    new_attend['attendance_id'] = attend.attendance.id
                    new_attend['time'] = attend.time
                    enlist.append(new_attend)
                    new_attend = {}
                stu.update({"student_attendance": enlist})
                enlist = []
            elif search_type == 3:
                attendance = await StudentAttendance.filter(
                    Q(time__gte=search1) &
                    Q(time__lte=search2), student_id=stu['id']).all().prefetch_related('attendance')
                for attend in attendance:
                    new_attend['student_attendance_id'] = attend.id
                    new_attend['attended'] = attend.attended
                    new_attend['attendance_id'] = attend.attendance.id
                    new_attend['time'] = attend.time
                    enlist.append(new_attend)
                    new_attend = {}
                stu.update({"student_attendance": enlist})
                enlist = []

        return {
            "students": students,
            "attendance": query2,
            "total_pages": pages,
            "total_students": count_students,
            "page": page
        }
    except:
        raise StarletteHTTPException(404, "Not Found")


# get student attendance bulky with pagination
@router.get('/banned-students-attendance')
async def students_attendance(number_of_students: int = 100, page: int = 1, institute_id: int = None,
                              search_type: int = None, search1: str = None, search2: str = None):
    global atten_student
    try:
        n = 0
        query = None
        query2 = await Attendance.filter().order_by('-date').all()
        count_students = await Student.filter(banned=1).all().count()
        if institute_id is None:
            query = await Student.filter(banned=1).order_by('name').limit(number_of_students).offset((page - 1) *
                                                                                            number_of_students)
        elif institute_id is not None:
            query = await Student.filter(institute_id=institute_id, banned=1).order_by('name').limit(
                number_of_students).offset(
                (page - 1) * number_of_students)
            count_students = await Student.filter(institute_id=institute_id, banned=1).count()
            query2 = await Attendance.filter(institute_id=institute_id).order_by(
                '-date').all()
        if search_type is not None:
            if search_type == 1 and institute_id is not None:  # search by student name
                query = await Student.filter(institute_id=institute_id,
                                            name__icontains=search1, banned=1).order_by('name'
                                                                            ).limit(
                    number_of_students).offset((page - 1) * number_of_students)
                count_students = await Student.filter(institute_id=institute_id,
                                                    name__icontains=search1, banned=1).count()
            elif search_type == 1 and institute_id is None:
                query = await Student.filter(
                    name__icontains=search1, banned=1).order_by('name').limit(
                    number_of_students).offset((page - 1) * number_of_students)
                count_students = await Student.filter(
                    name__icontains=search1, banned=1).count()
            elif search_type == 2:  # search by two date or one
                if search2 is None and institute_id is not None:
                    query = await Student.filter(institute_id=institute_id, banned=1).order_by(
                        'name').limit(
                        number_of_students).offset((page - 1) * number_of_students)
                    count_students = await Student.filter(institute_id=institute_id, banned=1).count()
                    query2 = await Attendance.filter(date=search1, institute_id=institute_id).order_by('-date').all()
                elif search2 is None and institute_id is None:
                    query = await Student.filter(banned=1).order_by('name').limit(
                        number_of_students).offset((page - 1) * number_of_students)
                    count_students = await Student.filter(banned=1).all().count()
                    query2 = await Attendance.filter(date=search1).order_by('-date').all()
                else:
                    if institute_id is not None:
                        query = await Student.filter(institute_id=institute_id, banned=1).order_by(
                            'name').limit(
                            number_of_students).offset((page - 1) * number_of_students)
                        count_students = await Student.filter(institute_id=institute_id, banned=1).count()
                        query2 = await Attendance.filter(Q(date__gte=search1) &
                                                        Q(date__lte=search2),
                                                        institute_id=institute_id).order_by(
                            '-date').all()
                    else:
                        query = await Student.filter(banned=1).order_by('name').limit(
                            number_of_students).offset((page - 1) * number_of_students)
                        count_students = await Student.filter(banned=1).all().count()
                        query2 = await Attendance.filter(Q(date__gte=search1) &
                                                        Q(date__lte=search2)).order_by(
                            '-date').all()
        if search_type == 3:
            attendance = await StudentAttendance.filter(
                Q(time__gte=search1) &
                Q(time__lte=search2)).all().prefetch_related('student')

            bulk_attend = attendance
            atten_student = [stude.student for stude in bulk_attend]
            atten_student = list(atten_student)
            n = 1
            query = []
            if len(atten_student) <= 100:
                for cou in atten_student:
                    min_query = await Student.filter(id=cou).all()
                    query.extend(min_query)
            elif len(atten_student) > 100:
                start = (page - 1) * number_of_students
                attended = atten_student[start:start + number_of_students]
                for cou in attended:
                    min_query = await Student.filter(id=cou.id).all()
                    query.extend(min_query)
        if n == 1:
            students = query
            count_students = len(atten_student)
            if count_students <= number_of_students:
                pages = 1
            else:
                pages = int(round(count_students / number_of_students))
        else:
            students = query
            if count_students <= number_of_students:
                pages = 1
            else:
                pages = int(round(count_students / number_of_students))
        students = [n.__dict__ for n in students]
        new_attend = {}
        enlist = []
        for stu in students:
            if search_type != 3:
                attendance = await StudentAttendance.filter(
                    student_id=stu['id']).all().prefetch_related('attendance')
                for attend in attendance:
                    new_attend['student_attendance_id'] = attend.id
                    new_attend['attended'] = attend.attended
                    new_attend['attendance_id'] = attend.attendance.id
                    new_attend['time'] = attend.time
                    enlist.append(new_attend)
                    new_attend = {}
                stu.update({"student_attendance": enlist})
                enlist = []
            elif search_type == 3:
                attendance = await StudentAttendance.filter(
                    Q(time__gte=search1) &
                    Q(time__lte=search2), student_id=stu['id']).all().prefetch_related('attendance')
                for attend in attendance:
                    new_attend['student_attendance_id'] = attend.id
                    new_attend['attended'] = attend.attended
                    new_attend['attendance_id'] = attend.attendance.id
                    new_attend['time'] = attend.time
                    enlist.append(new_attend)
                    new_attend = {}
                stu.update({"student_attendance": enlist})
                enlist = []

        return {
            "students": students,
            "attendance": query2,
            "total_pages": pages,
            "total_students": count_students,
            "page": page
        }
    except:
        raise StarletteHTTPException(404, "Not Found")

# To change Student Attendance
@router.patch('/students-attendance')
async def patch_students_attendance(student_attendance_id: int, attended: int):
    try:
        now = datetime.now()
        now_time = now.strftime("%H:%M")
        await StudentAttendance.filter(id=student_attendance_id).update(attended=attended, time=now_time)
        q = await StudentAttendance.filter(id=student_attendance_id).prefetch_related('student').first()
        return {
            "success": True,
            "student_id": q.student.id,
            "student_attendance_id": student_attendance_id,
            "student_name": q.student.name
        }
    except:
        raise StarletteHTTPException(500, "internal Server Error")


# To start students Attendance counting

@router.get('/attendance-start')
async def attendance_start(student_id):
    # try:
    student = await Student.filter(id=student_id).first().prefetch_related('institute')
    student = student.__dict__
    student['institute'] = student['_institute']
    del student['_institute']
    del student['institute_id']
    total_absence = await StudentAttendance.filter(
        student_id=student_id, attended=0).all().count() - 1

    incremental_absence = await StudentAttendance.filter(
        student_id=student_id).prefetch_related(Prefetch('attendance',
                                                         queryset=Attendance.all().order_by('-date'))).all()

    student_attendance_id = await StudentAttendance.filter(
        student_id=student_id).prefetch_related(Prefetch('attendance',
                                                         queryset=Attendance.all().order_by('-date'))).first()

    if student_attendance_id.attendance == 1:
        raise StarletteHTTPException(401, "Unauthorized")

    student.update(
        {"student_attendance_id": student_attendance_id.id})

    attend = [record.__dict__ for record in incremental_absence]
    attend.pop(-1)

    incrementally_absence = 0
    for record in attend:
        if record['attended'] == 0:
            incrementally_absence += 1
        elif record['attended'] == 1:
            incrementally_absence = 0

    attendance_date = await Attendance.filter(id=
                                              student_attendance_id.attendance.id).first()

    installments = await StudentInstallment.filter(student_id=student_id
                                                   ).prefetch_related(
        Prefetch('installment',
                 queryset=Installment.filter(date__lte=attendance_date.date)), 'student').all()
    installments_list = installments
    finalist = []
    stu = {}
    for record in installments_list:
        stu.update(
            {'installment_name': record.installment.name, "received": record.receive,
             "installment_id": record.installment.id})
        finalist.append(stu)
        stu = {}
    student.update({"total_absence": total_absence})
    student.update({"incrementally_absence": incrementally_absence})
    student.update({"installments": finalist})
    return student
# except:
#         raise StarletteHTTPException(500, "internal Server Error")
