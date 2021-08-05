from sqlalchemy import Column, Integer, String, ForeignKey, create_engine, Date, Boolean
from sqlalchemy.orm import relationship, backref, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

engine = create_engine('sqlite:///sapi.db')

Base = declarative_base()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
session = SessionLocal()


class Operation(Base):
    __abstract__ = True

    def insert(self):
        session.add(self)
        session.commit()

    def delete(self):
        session.delete(self)
        session.commit(self)

    def update(self):
        session.commit(self)


class Users(Operation):
    __tablename__ = 'Users'
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    password = Column(Integer, unique=True)


class Student(Operation):
    __tablename__ = "Student"
    id = Column(Integer, primary_key=True, unique=True)
    name = Column(String)
    dob = Column(String, nullable=True)
    phone = Column(Integer, nullable=True)
    qr = Column(String, unique=True)
    note = Column(String, nullable=True)
    picture = Column(String, nullable=True)
    insitute_id = Column(Integer, ForeignKey("Insitute.id"))
    batch = Column(Integer)
    installment = relationship("Student_Installment", backref="Student", lazy="dynamic")
    attendance = relationship("Student_Attendance", backref="Student", lazy="dynamic")

    def format(self, insit=""):
        return {
            "id": self.id,
            "name": self.name,
            "dob": self.dob,
            "phone": self.phone,
            "qr": self.qr,
            "note": self.note,
            "batch": self.batch,
            "photo": self.picture,
            "Insitute": insit

        }


class Insitute(Operation):
    __tablename__ = "Insitute"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    student = relationship("Student", backref="Insitute", lazy="dynamic")
    installment = relationship("Installment", backref="Insitute", lazy="dynamic")
    attendance = relationship("Attendance", backref="Insitute", lazy="dynamic")

    def format(self):
        return {
            "id": self.id,
            "name": self.name

        }


class Attendance(Operation):
    __tablename__ = "Attendance"
    id = Column(Integer, primary_key=True)
    insitute_id = Column(Integer, ForeignKey("Insitute.id"))
    date = Column(Date)
    student_attendance = relationship("Student_Attendance", backref="Attendance", lazy="dynamic")


class Student_Attendance(Operation):
    __tablename__ = "Student_Attendance"
    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("Student.id"))
    attendance_id = Column(Integer, ForeignKey("Attendance.id"))


class Installment(Operation):
    __tablename__ = "Installment"
    id = Column(Integer, primary_key=True, unique=True)
    name = Column(String)
    date = Column(Date)
    insitute_id = Column(Integer, ForeignKey("Insitute.id"))
    student_Installment = relationship("Student_Installment", backref="Installment", lazy="dynamic")


class Student_Installment(Operation):
    __tablename__ = "Student_Installment"
    id = Column(Integer, primary_key=True)
    installment_id = Column(Integer, ForeignKey("Installment.id"))
    student_id = Column(Integer, ForeignKey("Student.id"))
    received = Column(Boolean)
