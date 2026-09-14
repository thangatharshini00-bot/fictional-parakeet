"""
AI Student Support Assistant
-----------------------------
Beginner-friendly Flask project with:
- Student Login / Register (SQLite)
- AI Chatbot (simple keyword-based, easy to upgrade to a real LLM API)
- Study Assistance
- Exam Support
- Attendance Tracker
- Assignment Reminder
- College Information
- Career Guidance
"""

from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = "change-this-secret-key"  # used for login sessions

DB_PATH = os.path.join(os.path.dirname(__file__), "database.db")


# ---------------------------------------------------------
# DATABASE SETUP
# ---------------------------------------------------------
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            subject TEXT,
            status TEXT,
            date TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS assignments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            title TEXT,
            due_date TEXT,
            status TEXT DEFAULT 'Pending',
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)

    conn.commit()
    conn.close()


# ---------------------------------------------------------
# HELPER: login required check
# ---------------------------------------------------------
def is_logged_in():
    return "user_id" in session


# ---------------------------------------------------------
# HOME
# ---------------------------------------------------------
@app.route("/")
def home():
    return render_template("index.html", logged_in=is_logged_in())


# ---------------------------------------------------------
# REGISTER
# ---------------------------------------------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        conn = get_db()
        try:
            conn.execute(
                "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
                (name, email, password),
            )
            conn.commit()
            flash("Registration successful! Please login.", "success")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("Email already registered. Try logging in.", "error")
        finally:
            conn.close()

    return render_template("register.html")


# ---------------------------------------------------------
# LOGIN
# ---------------------------------------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = get_db()
        user = conn.execute(
            "SELECT * FROM users WHERE email = ? AND password = ?",
            (email, password),
        ).fetchone()
        conn.close()

        if user:
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            flash(f"Welcome back, {user['name']}!", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid email or password.", "error")

    return render_template("login.html")


# ---------------------------------------------------------
# LOGOUT
# ---------------------------------------------------------
@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "success")
    return redirect(url_for("home"))


# ---------------------------------------------------------
# DASHBOARD
# ---------------------------------------------------------
@app.route("/dashboard")
def dashboard():
    if not is_logged_in():
        return redirect(url_for("login"))
    return render_template("dashboard.html", name=session.get("user_name"))


# ---------------------------------------------------------
# AI CHATBOT  (simple rule-based demo — swap in a real LLM API later)
# ---------------------------------------------------------
def get_bot_reply(message):
    message = message.lower()

    responses = {
        "hi": "Hello! How can I help you with your studies today?",
        "hello": "Hi there! Ask me about study tips, exams, attendance, or assignments.",
        "attendance": "You can check your attendance from the Attendance Tracker page.",
        "assignment": "Check the Assignment Reminder section to see pending assignments.",
        "exam": "Visit the Exam Support page for tips and preparation guides.",
        "career": "Head over to Career Guidance for career path suggestions.",
        "college": "You can find college details in the College Information section.",
        "thanks": "You're welcome! All the best for your studies.",
        "bye": "Goodbye! Study well.",
    }

    for keyword, reply in responses.items():
        if keyword in message:
            return reply

    return "I'm still learning! Try asking about attendance, exams, assignments, or career guidance."


@app.route("/chatbot", methods=["GET", "POST"])
def chatbot():
    if not is_logged_in():
        return redirect(url_for("login"))

    reply = None
    user_message = None

    if request.method == "POST":
        user_message = request.form["message"]
        reply = get_bot_reply(user_message)

    return render_template("chatbot.html", reply=reply, user_message=user_message)


# ---------------------------------------------------------
# STUDY ASSISTANCE
# ---------------------------------------------------------
@app.route("/study")
def study():
    if not is_logged_in():
        return redirect(url_for("login"))

    tips = [
        "Use the Pomodoro Technique: 25 minutes study, 5 minutes break.",
        "Summarize each chapter in your own words after reading.",
        "Practice active recall instead of just re-reading notes.",
        "Teach the topic to someone else to test your understanding.",
        "Revise using spaced repetition (1 day, 3 days, 7 days later).",
    ]
    return render_template("study.html", tips=tips)


# ---------------------------------------------------------
# EXAM SUPPORT
# ---------------------------------------------------------
@app.route("/exam")
def exam():
    if not is_logged_in():
        return redirect(url_for("login"))

    guides = [
        "Prepare a revision timetable at least 2 weeks before exams.",
        "Solve previous years' question papers.",
        "Focus more time on topics with higher weightage.",
        "Get enough sleep the night before the exam.",
        "Reach the exam hall at least 30 minutes early.",
    ]
    return render_template("exam.html", guides=guides)


# ---------------------------------------------------------
# ATTENDANCE TRACKER
# ---------------------------------------------------------
@app.route("/attendance", methods=["GET", "POST"])
def attendance():
    if not is_logged_in():
        return redirect(url_for("login"))

    conn = get_db()

    if request.method == "POST":
        subject = request.form["subject"]
        status = request.form["status"]
        today = datetime.now().strftime("%Y-%m-%d")
        conn.execute(
            "INSERT INTO attendance (user_id, subject, status, date) VALUES (?, ?, ?, ?)",
            (session["user_id"], subject, status, today),
        )
        conn.commit()

    records = conn.execute(
        "SELECT * FROM attendance WHERE user_id = ? ORDER BY date DESC",
        (session["user_id"],),
    ).fetchall()
    conn.close()

    total = len(records)
    present = len([r for r in records if r["status"] == "Present"])
    percentage = round((present / total) * 100, 2) if total > 0 else 0

    return render_template(
        "attendance.html", records=records, percentage=percentage
    )


# ---------------------------------------------------------
# ASSIGNMENT REMINDER
# ---------------------------------------------------------
@app.route("/assignments", methods=["GET", "POST"])
def assignments():
    if not is_logged_in():
        return redirect(url_for("login"))

    conn = get_db()

    if request.method == "POST":
        title = request.form["title"]
        due_date = request.form["due_date"]
        conn.execute(
            "INSERT INTO assignments (user_id, title, due_date) VALUES (?, ?, ?)",
            (session["user_id"], title, due_date),
        )
        conn.commit()

    tasks = conn.execute(
        "SELECT * FROM assignments WHERE user_id = ? ORDER BY due_date ASC",
        (session["user_id"],),
    ).fetchall()
    conn.close()

    return render_template("assignments.html", tasks=tasks)


@app.route("/assignments/complete/<int:task_id>")
def complete_assignment(task_id):
    if not is_logged_in():
        return redirect(url_for("login"))

    conn = get_db()
    conn.execute(
        "UPDATE assignments SET status = 'Done' WHERE id = ? AND user_id = ?",
        (task_id, session["user_id"]),
    )
    conn.commit()
    conn.close()
    return redirect(url_for("assignments"))


# ---------------------------------------------------------
# COLLEGE INFORMATION
# ---------------------------------------------------------
@app.route("/college")
def college():
    if not is_logged_in():
        return redirect(url_for("login"))

    info = {
        "Courses Offered": "B.Tech, M.Tech, MBA, BCA, MCA",
        "Library Timing": "8:00 AM - 8:00 PM",
        "Fee Payment Deadline": "Last week of every semester",
        "Contact": "college-office@example.edu",
    }
    return render_template("college.html", info=info)


# ---------------------------------------------------------
# CAREER GUIDANCE
# ---------------------------------------------------------
@app.route("/career")
def career():
    if not is_logged_in():
        return redirect(url_for("login"))

    paths = [
        {"field": "Software Development", "skills": "Python, Java, DSA, Git"},
        {"field": "Data Science", "skills": "Python, Statistics, ML, SQL"},
        {"field": "Web Development", "skills": "HTML, CSS, JS, React, Flask/Node"},
        {"field": "Cybersecurity", "skills": "Networking, Linux, Ethical Hacking"},
        {"field": "Higher Studies (M.Tech/MS)", "skills": "GATE/GRE prep, Research"},
    ]
    return render_template("career.html", paths=paths)


# ---------------------------------------------------------
# RUN APP
# ---------------------------------------------------------
if __name__ == "__main__":
    init_db()
    app.run(debug=True, host="0.0.0.0", port=5000)
