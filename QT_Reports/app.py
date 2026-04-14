import os
import json
import zipfile
import requests
from io import BytesIO
from flask import Flask, render_template, request, redirect, send_file
from werkzeug.security import generate_password_hash, check_password_hash
import cloudinary
import cloudinary.uploader

# =========================
# CLOUDINARY CONFIG
# =========================
cloudinary.config(
    cloud_name="dwddk1pji",
    api_key="546872938222433",
    api_secret="Ss6RyORJaaGefKMB1heNfljLnik"
)

app = Flask(__name__)

DATA_FILE = "data.json"

# Ensure data file exists
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump([], f)


# =========================
# UTIL FUNCTIONS
# =========================
def load_data():
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)


def normalize_id(student_id):
    return student_id.strip().lower()


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
# ROUTES
# =========================

@app.route("/")
def dashboard():
    return render_template("dashboard.html", data=load_data())


# =========================
# SUBMIT
# =========================
@app.route("/submit", methods=["POST"])
def submit():
    name = request.form["name"]
    student_id = normalize_id(request.form["student_id"])
    year = request.form["year"]
    branch = request.form["branch"]
    password = request.form["password"]
    overwrite = request.form.get("overwrite")

    hashed_password = generate_password_hash(password)
    data = load_data()

    # 🔍 Check duplicate
    existing_index = None
    for i, d in enumerate(data):
        if normalize_id(d["student_id"]) == student_id:
            existing_index = i
            break

    # 🚨 Duplicate handling
    if existing_index is not None:
        if overwrite != "yes":
            return "DUPLICATE"

        # Remove old entry
        data.pop(existing_index)

    # 📤 Upload files to Cloudinary
    report1 = upload_file(request.files.get("report1"))
    report2 = upload_file(request.files.get("report2"))
    report3 = upload_file(request.files.get("report3"))

    # ✅ Save entry
    data.append({
        "name": name,
        "student_id": student_id,
        "year": year,
        "branch": branch,
        "password": hashed_password,
        "report1": report1,
        "report2": report2,
        "report3": report3
    })

    save_data(data)

    return redirect("/")


# =========================
# EDIT
# =========================
@app.route("/edit", methods=["POST"])
def edit():
    index = int(request.form["index"])
    password = request.form["password"]

    data = load_data()

    if index >= len(data):
        return "Invalid entry"

    entry = data[index]

    # 🔐 Password check
    if not check_password_hash(entry["password"], password):
        return "Wrong password"

    def update_file(file, old):
        if file and file.filename.endswith(".pdf"):
            return upload_file(file)
        return old

    entry["report1"] = update_file(request.files.get("report1"), entry["report1"])
    entry["report2"] = update_file(request.files.get("report2"), entry["report2"])
    entry["report3"] = update_file(request.files.get("report3"), entry["report3"])

    save_data(data)

    return redirect("/")


# =========================
# DELETE ENTRY
# =========================
@app.route("/delete", methods=["POST"])
def delete():
    index = int(request.form["index"])
    password = request.form["password"]

    data = load_data()

    if index >= len(data):
        return "Invalid entry"

    entry = data[index]

    # 🔐 Password check
    if not check_password_hash(entry["password"], password):
        return "Wrong password"

    # Remove entry only (Cloudinary files remain unless you delete manually)
    data.pop(index)
    save_data(data)

    return redirect("/")


# =========================
# ZIP DOWNLOAD (Cloudinary)
# =========================
@app.route("/download/<student_id>")
def download_zip(student_id):
    data = load_data()

    entry = next((e for e in data if e["student_id"] == student_id), None)

    if not entry:
        return "Not found"

    memory_file = BytesIO()

    with zipfile.ZipFile(memory_file, 'w') as zf:
        for key in ["report1", "report2", "report3"]:
            url = entry.get(key)
            if url:
                response = requests.get(url)
                filename = url.split("/")[-1]
                zf.writestr(filename, response.content)

    memory_file.seek(0)

    return send_file(memory_file, download_name=f"{student_id}.zip", as_attachment=True)


# =========================
# RUN
# =========================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
