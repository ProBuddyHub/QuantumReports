import os
import json
import zipfile
from flask import Flask, render_template, request, redirect, send_from_directory, send_file
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
DATA_FILE = "data.json"

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump([], f)


def load_data():
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)


@app.route("/")
def dashboard():
    return render_template("dashboard.html", data=load_data())


# ✅ SUBMIT
@app.route("/submit", methods=["POST"])
def submit():
    name = request.form["name"]
    student_id = request.form["student_id"]
    year = request.form["year"]
    branch = request.form["branch"]
    password = request.form["password"]
    overwrite = request.form.get("overwrite")

    hashed_password = generate_password_hash(password)

    data = load_data()

    # 🔍 Check duplicate
    for i, d in enumerate(data):
        if d["student_id"] == student_id:

            if overwrite != "yes":
                return "DUPLICATE"

            # ✅ Delete old entry
            old_folder = os.path.join(UPLOAD_FOLDER, student_id)
            if os.path.exists(old_folder):
                for f in os.listdir(old_folder):
                    os.remove(os.path.join(old_folder, f))

            data.pop(i)
            break

    # 📁 Create folder
    student_folder = os.path.join(UPLOAD_FOLDER, student_id)
    os.makedirs(student_folder, exist_ok=True)

    def save_file(file):
        if file and file.filename.endswith(".pdf"):
            path = os.path.join(student_folder, file.filename)
            file.save(path)
            return file.filename
        return ""

    report1 = save_file(request.files.get("report1"))
    report2 = save_file(request.files.get("report2"))
    report3 = save_file(request.files.get("report3"))

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


# ✅ SERVE FILE
@app.route("/uploads/<student_id>/<filename>")
def uploaded_file(student_id, filename):
    return send_from_directory(os.path.join(UPLOAD_FOLDER, student_id), filename)


# ✅ EDIT
@app.route("/edit", methods=["POST"])
def edit():
    index = int(request.form["index"])
    password = request.form["password"]

    data = load_data()
    entry = data[index]

    if not check_password_hash(entry["password"], password):
        return "Wrong password"

    student_folder = os.path.join(UPLOAD_FOLDER, entry["student_id"])

    def update_file(file, old):
        if file and file.filename.endswith(".pdf"):
            path = os.path.join(student_folder, file.filename)
            file.save(path)
            return file.filename
        return old

    entry["report1"] = update_file(request.files.get("report1"), entry["report1"])
    entry["report2"] = update_file(request.files.get("report2"), entry["report2"])
    entry["report3"] = update_file(request.files.get("report3"), entry["report3"])

    save_data(data)

    return redirect("/")


# ✅ ZIP DOWNLOAD
@app.route("/download/<student_id>")
def download_zip(student_id):
    student_folder = os.path.join(UPLOAD_FOLDER, student_id)
    zip_path = os.path.join(UPLOAD_FOLDER, f"{student_id}.zip")

    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for file in os.listdir(student_folder):
            file_path = os.path.join(student_folder, file)
            zipf.write(file_path, arcname=file)

    return send_file(zip_path, as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True)