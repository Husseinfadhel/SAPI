from tortoise.models import Model
from tortoise import fields


class Users(Model):
    id = fields.IntField(pk=True)
    name = fields.TextField(null=True)
    username = fields.CharField(max_length=100, unique=True)
    password = fields.IntField()
    auth = fields.IntField()

    class Meta:
        table = "Users"


class Student(Model):
    id = fields.IntField(pk=True, unique=True)
    name = fields.TextField(null=True)
    dob = fields.TextField(null=True)
    phone = fields.IntField(null=True)
    qr = fields.CharField(max_length=100, unique=True)
    note = fields.TextField(null=True)
    photo = fields.TextField(null=True)
    banned = fields.IntField(default=0)
    institute = fields.ForeignKeyField('models.Institute', null=True)

    class Meta:
        table = "Student"


class Institute(Model):
    id = fields.IntField(pk=True)
    name = fields.TextField(null=True)

    class Meta:
        table = "Institute"


class Attendance(Model):
    id = fields.IntField(pk=True)
    date = fields.TextField(null=True)
    institute = fields.ForeignKeyField('models.Institute', null=True)

    class Meta:
        table = "Attendance"


class StudentAttendance(Model):
    id = fields.IntField(pk=True)
    student = fields.ForeignKeyField('models.Student', null=True)
    attendance = fields.ForeignKeyField('models.Attendance', null=True)
    attended = fields.IntField(default=0)
    time = fields.TextField(null=True)

    class Meta:
        table = "Student_Attendance"


class Installment(Model):
    id = fields.IntField(pk=True)
    name = fields.TextField(null=True)
    date = fields.TextField(null=True)
    institute = fields.ForeignKeyField('models.Institute', null=True)

    class Meta:
        table = "Installment"


class StudentInstallment(Model):
    id = fields.IntField(pk=True)
    installment = fields.ForeignKeyField('models.Installment', null=True)
    student = fields.ForeignKeyField('models.Student', null=True)
    institute = fields.ForeignKeyField('models.Institute', null=True)
    receive = fields.IntField(default=0)

    class Meta:
        table = "Student_Installment"
