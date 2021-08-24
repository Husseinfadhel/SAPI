from fastapi import APIRouter
from models import session, engine, Base, Institute, Student, Attendance, Student_Attendance, Batch, \
    Student_Installment, \
    Installment
from fastapi.responses import FileResponse
from sqlalchemy import desc
from PIL import Image

router = APIRouter()


# insert Attendance
@router.post('/attendance')
def post_attendance(date, batch_id, institute_id):
    new = Attendance(date=date, batch_id=batch_id, institute_id=institute_id)
    Attendance.insert(new)
    query = session.query(Student).filter_by(batch_id=batch_id, institute_id=institute_id).all()
    for stu in [qu.students() for qu in query]:
        new_attend = Student_Attendance(student_id=stu['id'], attendance_id=new.id)
        Student_Attendance.insert(new_attend)
    return {
        "success": True
    }


# To change attendance
@router.patch('/attendance')
def patch_attendance(_id: int, date: str, batch_id: int, institute_id: int):
    new = session.query(Attendance).get(_id)
    new.date = date
    new.batch_id = batch_id
    new.institute_id = institute_id
    Attendance.update(new)
    return {
        "success": True
    }


# get student attendance bulky
@router.get('/students-attendance')
def students_attendance_institute():
    query = session.query(Student).filter_by().all()
    students = [record.students() for record in query]
    query2 = session.query(Attendance).all()
    paternalist = {"students": students,
                   "attendance": [record.format() for record in query2]

                   }
    new_attend = {}
    enlist = []
    for stu in students:
        attendance = session.query(Student_Attendance).filter_by(student_id=stu['id']).all()
        for attend in [att.format() for att in attendance]:
            new_attend['student_attendance_id'] = attend['id']
            new_attend['attended'] = attend['attended']
            new_attend['attendance_id'] = attend['attendance_id']
            enlist.append(new_attend)
            new_attend = {}
        stu.update({"student_attendance": enlist})
        enlist = []

    return paternalist


# To change Student Attendance
@router.patch('/students-attendance')
def students_attendance(_id: int, student_id: int, attend_id: int, attended: int):
    new = session.query(Student_Attendance).get(_id)
    new.student_id = student_id
    new.attendance_id = attend_id
    new.attended = attended
    Student_Attendance.update(new)
    return {
        "success": True
    }


# To start students Attendance counting

@router.get('/attendance-start')
def attendance_start(student_id: int):
    query = session.query(Student).get(student_id)
    student = query.format()
    total_absence = session.query(Student_Attendance).filter_by(student_id=student_id, attended=0)
    incremental = session.query(Student_Attendance).join(Attendance).filter(
        Student_Attendance.student_id == student_id)
    student_attendance_id = incremental.order_by(desc(Attendance.date)).limit(1)
    student_attendance_id = [record.format() for record in student_attendance_id]
    incremental_absence = incremental.order_by(Attendance.date).all()
    attend = [record.format() for record in incremental_absence]
    incrementally_absence = 0
    absence_list = []
    student.update({"student_attendance_id": student_attendance_id[0]['id']})
    for record in attend:
        if record['attended'] == 0:
            absence_list.append(True)
        elif len(absence_list) == 0:
            break
        else:
            incrementally_absence += 1
    installments = session.query(Student_Installment).join(Installment).filter(Student_Installment.student_id
                                                                               == student_id).all()
    installments_list = [student.student() for student in installments]
    finalist = []
    stu = {}
    for record in installments_list:
        stu.update({'installment_name': record['install_name'], "received": record["received"]})
        finalist.append(stu)
        stu = {}
    student.update({"total_absence": total_absence.count()})
    student.update({"incrementally_absence": incrementally_absence})
    student.update({"installments": finalist})

    path = student['photo']
    file = FileResponse(path)

    student['photo'] = file

    return student
