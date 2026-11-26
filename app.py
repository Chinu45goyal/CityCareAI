from flask import (
    Flask, render_template, request,
    redirect, url_for, flash, session
)

from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash
from functools import wraps

from database import get_connection
from intelligence import analyze_complaint

import os
import uuid


app = Flask(__name__)

app.secret_key = "06ffb988ea1da7d55423328a4d0616539e32a73e1883ef3b9fde0dcb91894073"
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

UPLOAD_FOLDER = os.path.join("static", "uploads")

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# ---------------------------------------
# CHECK IMAGE FILE TYPE
# ---------------------------------------

def allowed_file(filename):

    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )
# ---------------------------------------
# ADMIN LOGIN SECURITY
# ---------------------------------------

def admin_required(view_function):

    @wraps(view_function)
    def wrapped_view(*args, **kwargs):

        if "admin_id" not in session:

            flash("Please login as admin first.", "error")

            return redirect(url_for("admin_login"))

        return view_function(*args, **kwargs)

    return wrapped_view


# ---------------------------------------
# HOME PAGE
# ---------------------------------------

@app.route("/")
def home():

    return render_template("index.html")

# ---------------------------------------
# ADMIN LOGIN
# ---------------------------------------

@app.route("/admin_login", methods=["GET", "POST"])
def admin_login():

    if "admin_id" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        connection = None
        cursor = None

        try:
            connection = get_connection()
            cursor = connection.cursor(dictionary=True)

            cursor.execute(
                """
                SELECT admin_id, username, password_hash
                FROM admins
                WHERE username = %s
                """,
                (username,)
            )

            admin = cursor.fetchone()

            if admin and check_password_hash(
                admin["password_hash"], password
            ):

                session.clear()
                session["admin_id"] = admin["admin_id"]
                session["admin_username"] = admin["username"]

                flash("Login successful!", "success")

                return redirect(url_for("dashboard"))

            else:
                flash("Invalid username or password.", "error")

        except Exception as error:
            print("Admin Login Error:", error)
            flash("Unable to login. Please try again.", "error")

        finally:
            if cursor:
                cursor.close()

            if connection and connection.is_connected():
                connection.close()

    return render_template("admin_login.html")


# ---------------------------------------
# ADMIN LOGOUT
# ---------------------------------------

@app.route("/admin_logout")
def admin_logout():

    session.clear()

    flash("You have been logged out successfully.", "success")

    return redirect(url_for("admin_login"))



# ---------------------------------------
# TRACK COMPLAINT
# ---------------------------------------

@app.route("/track", methods=["GET", "POST"])
def track_complaint():

    complaint = None
    history = []
    error = None

    if request.method == "POST":

        complaint_id = request.form.get(
            "complaint_id", ""
        ).strip()

        if not complaint_id.isdigit():

            error = "Please enter a valid Complaint ID."

        else:

            connection = None
            cursor = None

            try:

                connection = get_connection()

                cursor = connection.cursor(dictionary=True)

                # Fetch complaint details

                cursor.execute(
                    """
                    SELECT
                        c.complaint_id,
                        c.citizen_name,
                        c.description,
                        c.category,
                        c.location,
                        c.severity,
                        c.priority,
                        c.status,
                        c.created_at,
                        d.department_name
                    FROM complaints c
                    LEFT JOIN departments d
                    ON c.department_id = d.department_id
                    WHERE c.complaint_id = %s
                    """,
                    (int(complaint_id),)
                )

                complaint = cursor.fetchone()

                if complaint:

                    # Fetch complaint status history

                    cursor.execute(
                        """
                        SELECT
                            old_status,
                            new_status,
                            updated_at
                        FROM complaint_history
                        WHERE complaint_id = %s
                        ORDER BY updated_at ASC, history_id ASC
                        """,
                        (int(complaint_id),)
                    )

                    history = cursor.fetchall()

                else:

                    error = "No complaint found with this ID."

            except Exception as e:

                print("Tracking Error:", e)

                error = "Unable to retrieve complaint. Please try again."

            finally:

                if cursor:
                    cursor.close()

                if connection and connection.is_connected():
                    connection.close()

    return render_template(
        "track.html",
        complaint=complaint,
        history=history,
        error=error
    )

# ---------------------------------------
# SUBMIT COMPLAINT
# ---------------------------------------

@app.route("/submit_complaint", methods=["POST"])
def submit_complaint():

    citizen_name = request.form.get("citizen_name", "").strip()

    description = request.form.get("description", "").strip()

    location = request.form.get("location", "").strip()

    image = request.files.get("image")

    # Validate required fields

    if not citizen_name or not description or not location:

        flash("Please fill in all required fields.", "error")

        return redirect(url_for("home"))

    if len(citizen_name) > 100 or len(location) > 255:

        flash("Name or location is too long.", "error")

        return redirect(url_for("home"))

    # Handle image upload

    image_path = None

    if image and image.filename:

        if not allowed_file(image.filename):

            flash("Please upload PNG, JPG, JPEG or WEBP images only.", "error")

            return redirect(url_for("home"))

        original_name = secure_filename(image.filename)

        unique_name = str(uuid.uuid4()) + "_" + original_name

        image.save(
            os.path.join(app.config["UPLOAD_FOLDER"], unique_name)
        )

        image_path = "uploads/" + unique_name

    connection = None
    cursor = None

    try:

        connection = get_connection()

        # Run intelligence engine

        analysis = analyze_complaint(
            description,
            location,
            connection
        )

        category = analysis["category"]

        severity = analysis["severity"]

        priority = analysis["priority"]

        department = analysis["department"]

        duplicate_of = analysis["duplicate_of"]

        # Find department ID

        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT department_id
            FROM departments
            WHERE department_name = %s
            """,
            (department,)
        )

        department_result = cursor.fetchone()

        if department_result is None:

            raise Exception("Assigned department not found in database.")

        department_id = department_result[0]

        # Save new complaint

        cursor.execute(
            """
            INSERT INTO complaints
            (
                citizen_name,
                description,
                category,
                location,
                image_path,
                severity,
                priority,
                department_id,
                duplicate_of,
                status
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                citizen_name,
                description,
                category,
                location,
                image_path,
                severity,
                priority,
                department_id,
                duplicate_of,
                "Pending"
            )
        )

        complaint_id = cursor.lastrowid

        # If duplicate, update the original complaint count

        if duplicate_of is not None:

            cursor.execute(
                """
                UPDATE complaints
                SET duplicate_count = duplicate_count + 1
                WHERE complaint_id = %s
                """,
                (duplicate_of,)
            )

        # Record initial status history

        cursor.execute(
            """
            INSERT INTO complaint_history
            (complaint_id, old_status, new_status)
            VALUES (%s, %s, %s)
            """,
            (complaint_id, None, "Pending")
        )

        connection.commit()
        print("COMPLAINT SAVED SUCCESSFULLY")
        print("Complaint ID:", complaint_id)
        print("Analysis:", analysis)

        # Show analysis result

        return render_template(
            "index.html",
            success=True,
            complaint_id=complaint_id,
            analysis=analysis
        )

    except Exception as error:

        if connection:
            connection.rollback()

        print("Complaint submission error:", repr(error))

        flash(
            "Something went wrong while submitting your complaint. Please try again.",
            "error"
        )

        return redirect(url_for("home"))

    finally:

        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()
# ---------------------------------------
# ADMIN DASHBOARD
# ---------------------------------------

@app.route("/dashboard")
@admin_required
def dashboard():

    connection = None
    cursor = None

    try:

        connection = get_connection()
        cursor = connection.cursor(dictionary=True)

        # 1. Total complaints

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM complaints
        """)

        total_complaints = cursor.fetchone()["total"]

        # 2. Resolved complaints

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM complaints
            WHERE status = 'Resolved'
        """)

        resolved_complaints = cursor.fetchone()["total"]

        # 3. Pending complaints

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM complaints
            WHERE status = 'Pending'
        """)

        pending_complaints = cursor.fetchone()["total"]

        # 4. In-progress complaints

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM complaints
            WHERE status = 'In Progress'
        """)

        in_progress_complaints = cursor.fetchone()["total"]

        # 5. High-priority complaints

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM complaints
            WHERE priority = 'High'
        """)

        high_priority_complaints = cursor.fetchone()["total"]

        # 6. Category-wise statistics

        cursor.execute("""
            SELECT category, COUNT(*) AS total
            FROM complaints
            GROUP BY category
            ORDER BY total DESC
        """)

        category_stats = cursor.fetchall()

        # 7. Department-wise statistics

        cursor.execute("""
            SELECT
                d.department_name,
                COUNT(c.complaint_id) AS total
            FROM departments d
            LEFT JOIN complaints c
                ON d.department_id = c.department_id
            GROUP BY d.department_id, d.department_name
            ORDER BY total DESC
        """)

        department_stats = cursor.fetchall()
        # Critical Area Detection
        cursor.execute("""
            SELECT
                location,
                COUNT(*) AS total_complaints,
                SUM(CASE WHEN priority = 'High' THEN 1 ELSE 0 END)
                    AS high_priority_count,
                ROUND(AVG(severity), 1) AS average_severity
            FROM complaints
            GROUP BY LOWER(TRIM(location)), location
            HAVING COUNT(*) >= 4
            ORDER BY total_complaints DESC
        """)
        
        critical_areas = cursor.fetchall()
        
        
        # 8. Recent complaints

        cursor.execute("""
            SELECT
                c.complaint_id,
                c.citizen_name,
                c.description,
                c.category,
                c.location,
                c.priority,
                c.severity,
                c.status,
                c.created_at,
                d.department_name
            FROM complaints c
            LEFT JOIN departments d
                ON c.department_id = d.department_id
            ORDER BY c.created_at DESC
        """)

        complaints = cursor.fetchall()

        return render_template(
            "dashboard.html",
            total_complaints=total_complaints,
            resolved_complaints=resolved_complaints,
            pending_complaints=pending_complaints,
            in_progress_complaints=in_progress_complaints,
            high_priority_complaints=high_priority_complaints,
            category_stats=category_stats,
            department_stats=department_stats,
            complaints=complaints,
            critical_areas=critical_areas
        )

    except Exception as error:

        print("Dashboard Error:", error)

        return "Unable to load dashboard. Check the VS Code terminal.", 500

    finally:

        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()


# ---------------------------------------
# UPDATE COMPLAINT STATUS
# ---------------------------------------

@app.route("/update_status", methods=["POST"])
@admin_required
def update_status():

    complaint_id = request.form.get("complaint_id", "").strip()

    new_status = request.form.get("status", "").strip()

    allowed_statuses = [
        "Pending",
        "In Progress",
        "Resolved"
    ]

    if not complaint_id.isdigit() or new_status not in allowed_statuses:

        flash("Invalid complaint ID or status.", "error")

        return redirect(url_for("dashboard"))

    connection = None
    cursor = None

    try:

        connection = get_connection()
        cursor = connection.cursor()

        # Get current status

        cursor.execute(
            """
            SELECT status
            FROM complaints
            WHERE complaint_id = %s
            """,
            (int(complaint_id),)
        )

        result = cursor.fetchone()

        if result is None:

            flash("Complaint not found.", "error")

            return redirect(url_for("dashboard"))

        old_status = result[0]

        if old_status == new_status:

            flash("Complaint already has this status.", "error")

            return redirect(url_for("dashboard"))

        # Update complaint

        cursor.execute(
            """
            UPDATE complaints
            SET status = %s
            WHERE complaint_id = %s
            """,
            (new_status, int(complaint_id))
        )

        # Save status change in history

        cursor.execute(
            """
            INSERT INTO complaint_history
            (complaint_id, old_status, new_status)
            VALUES (%s, %s, %s)
            """,
            (int(complaint_id), old_status, new_status)
        )

        connection.commit()

        flash("Complaint status updated successfully!", "success")

    except Exception as error:

        if connection:
            connection.rollback()

        print("Status Update Error:", error)

        flash("Unable to update complaint status.", "error")

    finally:

        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()

    return redirect(url_for("dashboard"))

# ---------------------------------------
# RUN APPLICATION
# ---------------------------------------

if __name__ == "__main__":

    app.run(debug=False)