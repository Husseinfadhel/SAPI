from fastapi import APIRouter
from models import session, engine, Base, Institute, Student, Attendance, Student_Attendance, Batch, Student_Installment
from typing import Optional

router = APIRouter()


# insert Attendance
@router.post('/attendance')
def post_attendance(date, batch_id, institute_id):
    new = Attendance(date=date, batch_id=batch_id, institute_id=institute_id)
    Attendance.insert(new)
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
