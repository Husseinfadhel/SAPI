from fastapi import APIRouter
from models import session, engine, Base, Institute, Student, Attendance, Student_Attendance, Batch, Student_Installment
from typing import Optional

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


# insert students attendance
@router.post('/students_attendance')
def post_student_attendance(attendance_id, student_id, attend: int):
    new = Student_Attendance(attendance_id=attendance_id, student_id=student_id, attended=attend)
    Student_Attendance.insert(new)
    return {
        "success": True
    }


# get student attendance by institute id
@router.get('/students-attendance-institute-bid')
def students_attendance_institute(institute_id: int):
    query = session.query(Student).filter_by(institute_id=institute_id).all()
    students = [record.students() for record in query]
    new_attend = {}
    enlist = []
    for stu in students:
        print(stu)
        attendance = session.query(Student_Attendance).filter_by(student_id=stu['id']).all()
        for attend in [att.format() for att in attendance]:
            new_attend['student_attendance_id'] = attend['id']
            new_attend['attended'] = attend['attended']
            enlist.append(new_attend)
            new_attend = {}
        stu.update({"students_attendace": enlist})
        enlist = []

    return students
