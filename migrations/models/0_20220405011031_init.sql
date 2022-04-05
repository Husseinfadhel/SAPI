-- upgrade --
CREATE TABLE IF NOT EXISTS "Institute" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "name" TEXT
);
CREATE TABLE IF NOT EXISTS "Attendance" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "date" TEXT,
    "institute_id" INT REFERENCES "Institute" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "Installment" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "name" TEXT,
    "date" TEXT,
    "institute_id" INT REFERENCES "Institute" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "Student" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "name" TEXT,
    "dob" TEXT,
    "phone" INT,
    "qr" VARCHAR(100) NOT NULL UNIQUE,
    "note" TEXT,
    "photo" TEXT,
    "banned" INT NOT NULL  DEFAULT 0,
    "institute_id" INT REFERENCES "Institute" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "Student_Attendance" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "attended" INT NOT NULL  DEFAULT 0,
    "time" TEXT,
    "attendance_id" INT REFERENCES "Attendance" ("id") ON DELETE CASCADE,
    "student_id" INT REFERENCES "Student" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "Student_Installment" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "receive" INT NOT NULL  DEFAULT 0,
    "installment_id" INT REFERENCES "Installment" ("id") ON DELETE CASCADE,
    "institute_id" INT REFERENCES "Institute" ("id") ON DELETE CASCADE,
    "student_id" INT REFERENCES "Student" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "Users" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "name" TEXT,
    "username" VARCHAR(100) NOT NULL UNIQUE,
    "password" INT NOT NULL,
    "auth" INT NOT NULL
);
CREATE TABLE IF NOT EXISTS "aerich" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(20) NOT NULL,
    "content" JSON NOT NULL
);
