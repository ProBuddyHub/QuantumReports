import os
import zipfile
import requests
from io import BytesIO

from flask import Flask, render_template, request, redirect, send_file
from werkzeug.security import generate_password_hash, check_password_hash

import cloudinary
import cloudinary.uploader
import psycopg2

# =========================
# CLOUDINARY CONFIG
# =========================
cloudinary.config(
    cloud_name="dwddk1pji",
    api_key="546872938222433",
    api_secret="Ss6RyORJaaGefKMB1heNfljLnik"
)

app = Flask(__name__)

DATABASE_URL = os.environ.get("DATABASE_URL")


# =========================
# DB CONNECTION
# =========================
def get_conn():
    return psycopg2.connect(DATABASE_URL, sslmode = 'require')


# =========================
# INIT DB TABLE (RUN ONCE)
# =========================
def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS reports (
        id SERIAL PRIMARY KEY,
        name TEXT,
        student_id TEXT UNIQUE,
        year TEXT,
        branch TEXT,
        password TEXT,
        report1 TEXT,
        report2 TEXT,
        report3 TEXT
    )
    """)

    conn.commit()
    cur.close()
    conn.close()


# =========================
# CLOUDINARY UPLOAD
# =========================
def upload_file(file):
    if file and file.filename.endswith(".pdf"):
        result = cloudinary.uploader.upload(
            file,
            resource_type="raw",
            folder="quantum_reports"
        )
        return result["secure_url"]
    return ""


# =========================
# DASHBOARD
# =========================
@app.route("/")
def dashboard():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT name, student_id, year, branch, report1, report2, report3
        FROM reports
        ORDER BY id DESC
    """)

    rows = cur.fetchall()
    cur.close()
    conn.close()

    data = [
        {
            "name": r[0],
            "student_id": r[1],
            "year": r[2],
            "branch": r[3],
            "report1": r[4],
            "report2": r[5],
            "report3": r[6],
        }
        for r in rows
    ]

    return render_template("dashboard.html", data=data)


# =========================
# SUBMIT (UPSERT)
# =========================
@app.route("/submit", methods=["POST"])
def submit():
    name = request.form["name"]
    student_id = request.form["student_id"].strip().lower()
    year = request.form["year"]
    branch = request.form["branch"]
    password = generate_password_hash(request.form["password"])
    overwrite = request.form.get("overwrite")

    report1 = upload_file(request.files.get("report1"))
    report2 = upload_file(request.files.get("report2"))
    report3 = upload_file(request.files.get("report3"))

    conn = get_conn()
    cur = conn.cursor()

    # Check existing
    cur.execute("SELECT id FROM reports WHERE student_id=%s", (student_id,))
    existing = cur.fetchone()

    if existing and overwrite != "yes":
        return "DUPLICATE"

    # UPSERT logic
    cur.execute("""
    INSERT INTO reports (name, student_id, year, branch, password, report1, report2, report3)
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
    ON CONFLICT (student_id)
    DO UPDATE SET
        name=EXCLUDED.name,
        year=EXCLUDED.year,
        branch=EXCLUDED.branch,
        password=EXCLUDED.password,
        report1=EXCLUDED.report1,
        report2=EXCLUDED.report2,
        report3=EXCLUDED.report3
    """, (name, student_id, year, branch, password, report1, report2, report3))

    conn.commit()
    cur.close()
    conn.close()

    return redirect("/")


# =========================
# EDIT
# =========================
@app.route("/edit", methods=["POST"])
def edit():
    student_id = request.form["student_id"].strip().lower()
    password = request.form["password"]

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT password, report1, report2, report3
        FROM reports
        WHERE student_id=%s
    """, (student_id,))

    row = cur.fetchone()

    if not row:
        return "Not found"

    if not check_password_hash(row[0], password):
        return "Wrong password"

    def update(file, old):
        return upload_file(file) if file and file.filename.endswith(".pdf") else old

    r1 = update(request.files.get("report1"), row[1])
    r2 = update(request.files.get("report2"), row[2])
    r3 = update(request.files.get("report3"), row[3])

    cur.execute("""
        UPDATE reports
        SET report1=%s, report2=%s, report3=%s
        WHERE student_id=%s
    """, (r1, r2, r3, student_id))

    conn.commit()
    cur.close()
    conn.close()

    return redirect("/")


# =========================
# DELETE (FIXED SAFE VERSION)
# =========================
@app.route("/delete", methods=["POST"])
def delete():
    student_id = request.form["student_id"].strip().lower()
    password = request.form["password"]

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT password FROM reports WHERE student_id=%s", (student_id,))
    row = cur.fetchone()

    if not row:
        return "Not found"

    if not check_password_hash(row[0], password):
        return "Wrong password"

    cur.execute("DELETE FROM reports WHERE student_id=%s", (student_id,))

    conn.commit()
    cur.close()
    conn.close()

    return redirect("/")


# =========================
# ZIP DOWNLOAD
# =========================
@app.route("/download/<student_id>")
def download_zip(student_id):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT report1, report2, report3
        FROM reports
        WHERE student_id=%s
    """, (student_id,))

    row = cur.fetchone()

    if not row:
        return "Not found"

    memory_file = BytesIO()

    with zipfile.ZipFile(memory_file, "w") as zf:
        for url in row:
            if url:
                r = requests.get(url)
                filename = url.split("/")[-1]
                zf.writestr(filename, r.content)

    memory_file.seek(0)

    return send_file(memory_file,
                     download_name=f"{student_id}.zip",
                     as_attachment=True)


# =========================
# RUN
# =========================
if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
