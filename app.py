# app.py
from flask import Flask, render_template, request, redirect
import sqlite3
from datetime import datetime
import pandas as pd

app = Flask(__name__)
DB_NAME = "attendance.db"

# -------------------------------
# DATABASE SETUP
# -------------------------------
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            status TEXT,
            date TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

# -------------------------------
# DATABASE FUNCTIONS
# -------------------------------
def add_student(name):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO students (name) VALUES (?)", (name,))
    conn.commit()
    conn.close()

def mark_attendance(student_id, status):
    date = datetime.now().strftime("%Y-%m-%d")
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO attendance (student_id, status, date) VALUES (?, ?, ?)",
        (student_id, status, date)
    )
    conn.commit()
    conn.close()

def get_attendance_df():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql("""
        SELECT students.id, students.name, attendance.status, attendance.date
        FROM attendance
        JOIN students ON attendance.student_id = students.id
    """, conn)
    conn.close()
    return df

def get_students():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM students")
    students = cursor.fetchall()
    conn.close()
    return students

# -------------------------------
# ROUTES
# -------------------------------
@app.route("/")
def home():
    df = get_attendance_df()
    summary = None
    if not df.empty:
        summary = df.groupby("name")["status"].value_counts().unstack().fillna(0)
        summary["Total"] = summary.sum(axis=1)
        summary["Attendance %"] = (summary.get("Present", 0) / summary["Total"]) * 100
        summary = summary.reset_index()
    students = get_students()
    return render_template("index.html", students=students, summary=summary)

@app.route("/add_student", methods=["POST"])
def add_student_route():
    name = request.form.get("name")
    if name:
        add_student(name)
    return redirect("/")

@app.route("/mark_attendance", methods=["POST"])
def mark_attendance_route():
    student_id = request.form.get("student_id")
    status = request.form.get("status")
    if student_id and status:
        mark_attendance(student_id, status)
    return redirect("/")

# -------------------------------
# RUN APP
# -------------------------------
if __name__ == "__main__":
    app.run(debug=True)
