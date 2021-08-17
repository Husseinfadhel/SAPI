from sqlalchemy import Column, Integer, String, ForeignKey, create_engine, Date, Boolean, MetaData
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
        session.commit()


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
    qr = Column(String, unique=True, nullable=True)
    note = Column(String, nullable=True)
    picture = Column(String, nullable=True)
    institute_id = Column(Integer, ForeignKey("Institute.id"))
    batch_id = Column(Integer, ForeignKey('Batch.id'))
    installment = relationship(
        "Student_Installment", backref="Student", lazy="dynamic")
    attendance = relationship("Student_Attendance",
                              backref="Student", lazy="dynamic")

    def format(self):
        return {
            "id": self.id,
            "name": self.name,
            "dob": self.dob,
            "phone": self.phone,
            "qr": self.qr,
            "note": self.note,
            "batch": self.batch_id,
            "photo": self.picture,
            "institute_id": self.institute_id,
            "institute": self.Institute.name
        }


class Institute(Operation):
    __tablename__ = "Institute"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    student = relationship("Student", backref="Institute", lazy="dynamic")
    installment = relationship(
        "Installment", backref="Institute", lazy="dynamic")
    attendance = relationship(
        "Attendance", backref="Institute", lazy="dynamic")
    installment_student = relationship(
        "Student_Installment", backref="Institute", lazy="dynamic")

    def format(self):
        return {
            "id": self.id,
            "name": self.name

        }


class Attendance(Operation):
    __tablename__ = "Attendance"
    id = Column(Integer, primary_key=True)
    Institute_id = Column(Integer, ForeignKey("Institute.id"))
    date = Column(Date)
    batch_id = Column(Integer, ForeignKey('Batch.id'))

    student_attendance = relationship(
        "Student_Attendance", backref="Attendance", lazy="dynamic")


class Student_Attendance(Operation):
    __tablename__ = "Student_Attendance"
    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("Student.id"))
    attendance_id = Column(Integer, ForeignKey("Attendance.id"))


class Installment(Operation):
    __tablename__ = "Installment"
    id = Column(Integer, primary_key=True, unique=True)
    name = Column(String)
    date = Column(String)
    Institute_id = Column(Integer, ForeignKey("Institute.id"))
    batch_id = Column(Integer, ForeignKey('Batch.id'))
    student_Installment = relationship(
        "Student_Installment", backref="Installment", lazy="dynamic")

    def format(self):
        return {
            "id": self.id,
            "name": self.name,
            "Institute_id": self.Institute.id,
            "Institute_name": self.Institute.name,
            "date": self.date
        }


class Batch(Operation):
    __tablename__ = "Batch"
    id = Column(Integer, primary_key=True)
    batch_num = Column(Integer, unique=True)
    student = relationship('Student', backref='Batch', lazy='dynamic')
    attendance = relationship('Attendance', backref='Batch', lazy='dynamic')
    installment = relationship('Installment', backref='Batch')

    def format(self):
        return {
            "id":self.id,
            "batch_num": self.batch_num
        }

class Student_Installment(Operation):
    __tablename__ = "Student_Installment"
    id = Column(Integer, primary_key=True)
    installment_id = Column(Integer, ForeignKey("Installment.id"))
    student_id = Column(Integer, ForeignKey("Student.id"))
    Institute_id = Column(Integer, ForeignKey("Institute.id"))
    received = Column(Boolean)

    def format(self):
        return {
            "id": self.id,
            "nameStudent": self.Student.name,
            "installNAme": self.Installment.name,
            "received": self.received,
            "Date": self.Installment.date
        }

    def received(self):
        return {
            "received": self.received

        }

    def student(self):
        return {
            "id": self.Student.id,
            "name": self.Student.name,
            "Institute_id": self.Student.Institute_id

        }
