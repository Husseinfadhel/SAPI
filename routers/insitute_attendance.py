from fastapi import APIRouter
from models import session, engine, Base, Institute, Student, Attendance, Student_Attendance, \
    Student_Installment, \
    Installment
from sqlalchemy import desc
from starlette.exceptions import HTTPException as StarletteHTTPException

router = APIRouter()


# insert Attendance
@router.post('/attendance')
def post_attendance(date, institute_id):
    try:
        if date != "":
            query = session.query(Attendance).filter_by(
                date=date, institute_id=institute_id).all()

            if query == []:
                new = Attendance(date=date,
                                 institute_id=institute_id)
                Attendance.insert(new)
                query = session.query(Student).filter_by(
                    institute_id=institute_id).all()
                for stu in query:
                    new_attend = Student_Attendance(
                        student_id=stu.id, attendance_id=new.id)
                    session.add(new_attend)
                Student_Attendance.insert(new_attend)
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
        new.date = date
        new.institute_id = institute_id
        Attendance.update(new)
        return {
            "success": True
        }
    except:
        raise StarletteHTTPException(500, "internal Server Error")


# get student attendance bulky
@router.get('/students-attendance')
def students_attendance_institute():
    try:
        query = session.query(Student).filter_by().all()
        students = [record.students() for record in query]
        query2 = session.query(Attendance).all()
        paternalist = {"students": students,
                       "attendance": [record.format() for record in query2]

                       }
        new_attend = {}
        enlist = []
        for stu in students:
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


# To change Student Attendance
@router.patch('/students-attendance')
def students_attendance(student_attendance_id: int, attended: int, time: str):
    try:
        new = session.query(Student_Attendance).get(student_attendance_id)
        new.attended = attended
        new.time = time
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
                                                                                   == student_id, attendance_date.date >= Installment.date).all()
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
