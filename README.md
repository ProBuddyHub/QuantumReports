# 📘 Quantum Reports

## 🧾 About the Project

Quantum Reports is a simple web application designed to collect and manage **three academic reports** from minor degree students in our college.

This project was primarily built as a **learning exercise** to improve my skills in:

* Web development
* Backend integration
* File handling
* Deploying full-stack applications
* Using AI tools to accelerate development 🚀

---

## 🎯 Purpose

Students can:

* Submit up to 3 PDF reports
* Update their submissions later using a password
* Download all their reports as a ZIP file

Admins (or viewers) can:

* View all submissions in a clean dashboard
* Search and filter students by name, ID, year, or branch

---

## ⚙️ Features

* 📂 Automatic folder creation for each student ID
* 🔐 Password-protected edit & delete functionality
* 🔁 Duplicate detection with overwrite option
* 📦 ZIP download of all uploaded reports
* 🔍 Search + filter (year & branch)
* 📱 Mobile-friendly responsive UI

---

## 🧱 Tech Stack

### 🖥️ Frontend

* HTML
* Tailwind CSS
* JavaScript (for filtering & UI interactions)

### ⚙️ Backend

* Python
* Flask

### 📁 Storage

* JSON file (for storing student data)
* File system / Cloudinary (for storing uploaded PDFs)

### ☁️ Deployment

* Render (for hosting backend)

---

## 🚀 How It Works

1. User submits details + PDF files
2. Backend:

   * Creates a folder using student ID
   * Stores files inside that folder
   * Saves metadata in `data.json`
3. Users can:

   * Edit files (with password)
   * Delete entry completely
   * Download all files as ZIP

---

## 🧠 What I Learned

* Handling file uploads in Flask
* Managing user data securely (password hashing)
* Creating dynamic dashboards with Jinja2
* Debugging real deployment issues
* Integrating cloud storage (Cloudinary)
* Deploying backend apps on Render

---

## ⚠️ Note

This is a **practice project**, not a production-grade system. It was built mainly for learning and experimentation.

---

## 🙌 Credits

Built by me as part of my journey to improve development skills using AI assistance.

---

## 📌 Future Improvements

* Add database (PostgreSQL)
* Email-based password recovery
* Admin panel
* Better UI/UX
* File preview support

---

⭐ If you find this project helpful or interesting, feel free to fork or improve it!
