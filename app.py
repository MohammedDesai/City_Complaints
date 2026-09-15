"""
City Complaint Tracking MVP
Run with: python app.py
"""
import os
import re
import json
import random
import string
import sqlite3
import smtplib
import logging
import difflib
from functools import wraps
from datetime import datetime, timedelta
from email.message import EmailMessage

from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, session, jsonify, send_from_directory, abort
)
from werkzeug.utils import secure_filename

from config import Config
from classifier import classify_complaint, compute_priority

app = Flask(__name__)
app.config.from_object(Config)

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

logging.basicConfig(level=logging.INFO)
logger = app.logger

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

DATETIME_FMT = "%Y-%m-%d %H:%M:%S"


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------
def get_db_connection():
    conn = sqlite3.connect(app.config["DATABASE"])
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# Columns beyond the original v1 schema. Stored as (name, sql_type, default)
# so init_db can both create a fresh table AND migrate an older v1
# complaints.db in place by adding any columns that are missing.
_V2_COLUMNS = [
    ("severity", "TEXT", "'Low'"),
    ("department", "TEXT", "'General Services'"),
    ("priority_score", "INTEGER", "0"),
    ("priority_label", "TEXT", "'Low'"),
    ("sla_hours", "INTEGER", "336"),
    ("sla_due_at", "TEXT", "NULL"),
    ("latitude", "REAL", "NULL"),
    ("longitude", "REAL", "NULL"),
    ("is_duplicate", "INTEGER", "0"),
    ("duplicate_of", "TEXT", "NULL"),
    ("after_photo_filename", "TEXT", "NULL"),
    ("resolution_note", "TEXT", "NULL"),
    ("verified_at", "TEXT", "NULL"),
    ("verification_status", "TEXT", "'Unverified'"),
]


def init_db():
    """
    Create the complaints table if it does not exist, and transparently
    migrate an older (v1) complaints.db by adding any v2 columns that are
    missing. This means an existing database from the first MVP release
    keeps working after upgrading the app.
    """
    conn = get_db_connection()
    table_existed_before = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='complaints'"
    ).fetchone() is not None

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS complaints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tracking_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT,
            type TEXT NOT NULL,
            location TEXT NOT NULL,
            description TEXT NOT NULL,
            photo_filename TEXT,
            status TEXT NOT NULL DEFAULT 'Submitted',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    conn.commit()

    existing_cols = {row["name"] for row in conn.execute("PRAGMA table_info(complaints)")}
    for col_name, col_type, default in _V2_COLUMNS:
        if col_name not in existing_cols:
            conn.execute(
                f"ALTER TABLE complaints ADD COLUMN {col_name} {col_type} DEFAULT {default}"
            )
            if table_existed_before:
                logger.info(f"Migrated complaints.db: added column '{col_name}'.")
    conn.commit()
    conn.close()
    logger.info("Database initialized (complaints.db ready).")


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------
def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in app.config["ALLOWED_EXTENSIONS"]
    )


def save_uploaded_photo(file_storage):
    """Validate + persist an uploaded image, returning its stored filename."""
    original_name = secure_filename(file_storage.filename)
    ext = original_name.rsplit(".", 1)[1].lower()
    unique_name = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{random.randint(1000, 9999)}.{ext}"
    file_storage.save(os.path.join(app.config["UPLOAD_FOLDER"], unique_name))
    return unique_name


def generate_tracking_id():
    """Generate a short, unique, easy-to-type tracking ID like CMP7K92A."""
    conn = get_db_connection()
    while True:
        suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=5))
        tracking_id = f"CMP{suffix}"
        existing = conn.execute(
            "SELECT id FROM complaints WHERE tracking_id = ?", (tracking_id,)
        ).fetchone()
        if not existing:
            conn.close()
            return tracking_id


def now_str():
    return datetime.now().strftime(DATETIME_FMT)


def parse_dt(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, DATETIME_FMT)
    except ValueError:
        return None


def find_possible_duplicate(issue_type, location, conn):
    """
    Look for an existing, still-open complaint of the same type whose
    location text is a close match, reported within the configurable
    duplicate window. Returns the matching row or None.
    Uses difflib's SequenceMatcher for a dependency-free fuzzy match.
    """
    cutoff = (datetime.now() - timedelta(days=app.config["DUPLICATE_WINDOW_DAYS"])).strftime(DATETIME_FMT)
    candidates = conn.execute(
        """
        SELECT * FROM complaints
        WHERE type = ? AND status != 'Resolved' AND created_at >= ?
        ORDER BY created_at DESC
        """,
        (issue_type, cutoff),
    ).fetchall()

    location_norm = (location or "").strip().lower()
    best_match = None
    best_ratio = 0.0

    for candidate in candidates:
        candidate_location = (candidate["location"] or "").strip().lower()
        ratio = difflib.SequenceMatcher(None, location_norm, candidate_location).ratio()
        if ratio > best_ratio:
            best_ratio = ratio
            best_match = candidate

    if best_match and best_ratio >= app.config["DUPLICATE_LOCATION_SIMILARITY"]:
        return best_match
    return None


def count_duplicates_of(tracking_id, conn):
    row = conn.execute(
        "SELECT COUNT(*) as cnt FROM complaints WHERE duplicate_of = ?", (tracking_id,)
    ).fetchone()
    return row["cnt"] if row else 0


def compute_sla_status(row):
    """Return ('On Track' | 'Overdue' | 'Met', due_at_str) for a complaint row."""
    due_at = parse_dt(row["sla_due_at"]) if "sla_due_at" in row.keys() else None
    if due_at is None:
        return "Unknown", None

    if row["status"] == "Resolved":
        updated_at = parse_dt(row["updated_at"])
        status = "Met" if (updated_at and updated_at <= due_at) else "Met Late"
        return status, row["sla_due_at"]

    status = "Overdue" if datetime.now() > due_at else "On Track"
    return status, row["sla_due_at"]


def complaint_to_dict(row):
    d = {
        "id": row["id"],
        "tracking_id": row["tracking_id"],
        "name": row["name"],
        "email": row["email"],
        "phone": row["phone"] or "",
        "type": row["type"],
        "location": row["location"],
        "description": row["description"],
        "photo_filename": row["photo_filename"],
        "status": row["status"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }
    keys = row.keys()
    d["severity"] = row["severity"] if "severity" in keys else "Low"
    d["department"] = row["department"] if "department" in keys else "General Services"
    d["priority_score"] = row["priority_score"] if "priority_score" in keys else 0
    d["priority_label"] = row["priority_label"] if "priority_label" in keys else "Low"
    d["sla_hours"] = row["sla_hours"] if "sla_hours" in keys else None
    d["sla_due_at"] = row["sla_due_at"] if "sla_due_at" in keys else None
    d["latitude"] = row["latitude"] if "latitude" in keys else None
    d["longitude"] = row["longitude"] if "longitude" in keys else None
    d["is_duplicate"] = bool(row["is_duplicate"]) if "is_duplicate" in keys else False
    d["duplicate_of"] = row["duplicate_of"] if "duplicate_of" in keys else None
    d["after_photo_filename"] = row["after_photo_filename"] if "after_photo_filename" in keys else None
    d["resolution_note"] = row["resolution_note"] if "resolution_note" in keys else None
    d["verified_at"] = row["verified_at"] if "verified_at" in keys else None
    d["verification_status"] = row["verification_status"] if "verification_status" in keys else "Unverified"

    sla_status, sla_due_at = compute_sla_status(row)
    d["sla_status"] = sla_status
    return d


def login_required(view_func):
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if not session.get("admin_logged_in"):
            flash("Please log in to access the admin dashboard.", "warning")
            return redirect(url_for("admin_login"))
        return view_func(*args, **kwargs)
    return wrapped


# ---------------------------------------------------------------------------
# Email notifications
# ---------------------------------------------------------------------------
def send_email(to_email, subject, body):
    """
    Low-level Gmail SMTP sender shared by all notification helpers.
    Returns (success, error_message). Never raises.
    """
    mail_user = app.config.get("MAIL_USERNAME")
    mail_pass = app.config.get("MAIL_PASSWORD")

    if not mail_user or not mail_pass:
        msg = "Gmail credentials are not configured (MAIL_USERNAME/MAIL_PASSWORD missing)."
        logger.warning(msg)
        return False, msg

    try:
        email_msg = EmailMessage()
        email_msg["Subject"] = subject
        email_msg["From"] = mail_user
        email_msg["To"] = to_email
        email_msg.set_content(body)

        with smtplib.SMTP(app.config["MAIL_SERVER"], app.config["MAIL_PORT"], timeout=15) as server:
            server.starttls()
            server.login(mail_user, mail_pass)
            server.send_message(email_msg)

        logger.info(f"Email sent to {to_email}: {subject}")
        return True, None
    except Exception as exc:  # noqa: BLE001 - must never bubble up
        logger.error(f"Failed to send email to {to_email}: {exc}")
        return False, str(exc)


def send_status_email(to_email, name, tracking_id, issue_type, location,
                       old_status, new_status, updated_at):
    resolved_note = ""
    if new_status == "Resolved":
        resolved_note = (
            "\nYour complaint has been marked as RESOLVED. Please visit the "
            "Track Complaint page and let us know whether the issue is "
            "actually fixed - your confirmation helps us verify our work.\n"
        )

    body = f"""Hello {name},

This is an update regarding your complaint filed with the City Complaint Tracker.

Tracking ID:     {tracking_id}
Issue Type:      {issue_type}
Location:        {location}
Previous Status: {old_status}
New Status:      {new_status}
Updated At:      {updated_at}
{resolved_note}
You can check the latest status at any time using your Tracking ID on the
Track Complaint page.

Thank you,
City Complaint Tracker Team
"""
    return send_email(to_email, f"Complaint {tracking_id} Status Updated", body)


# ---------------------------------------------------------------------------
# Resident routes
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    return render_template("index.html", issue_types=app.config["ISSUE_TYPES"])


@app.route("/submit", methods=["POST"])
def submit_complaint():
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    phone = request.form.get("phone", "").strip()
    issue_type = request.form.get("type", "").strip()
    location = request.form.get("location", "").strip()
    description = request.form.get("description", "").strip()
    photo = request.files.get("photo")

    lat_raw = request.form.get("latitude", "").strip()
    lng_raw = request.form.get("longitude", "").strip()

    errors = []

    if not name:
        errors.append("Name is required.")
    if not email:
        errors.append("Email is required.")
    elif not EMAIL_REGEX.match(email):
        errors.append("Please enter a valid email address.")
    if issue_type not in app.config["ISSUE_TYPES"]:
        errors.append("Please select a valid issue type.")
    if not location:
        errors.append("Location is required.")
    if not description:
        errors.append("Description is required.")

    if photo and photo.filename and not allowed_file(photo.filename):
        errors.append("Invalid photo format. Allowed types: jpg, jpeg, png, gif, webp.")

    latitude = longitude = None
    try:
        if lat_raw:
            latitude = float(lat_raw)
        if lng_raw:
            longitude = float(lng_raw)
    except ValueError:
        latitude = longitude = None  # silently ignore malformed GPS data

    if errors:
        for err in errors:
            flash(err, "danger")
        return redirect(url_for("index"))

    photo_filename = save_uploaded_photo(photo) if (photo and photo.filename) else None

    # --- AI-assisted classification: severity, department, SLA window ---
    classification = classify_complaint(issue_type, description)
    severity = classification["severity"]
    department = classification["department"]
    sla_hours = classification["sla_hours"]

    timestamp = now_str()
    sla_due_at = (datetime.now() + timedelta(hours=sla_hours)).strftime(DATETIME_FMT)

    conn = get_db_connection()

    # --- Duplicate detection against other open complaints ---
    duplicate_match = find_possible_duplicate(issue_type, location, conn)
    is_duplicate = 1 if duplicate_match else 0
    duplicate_of = duplicate_match["tracking_id"] if duplicate_match else None

    duplicate_count_for_priority = 0
    if duplicate_match:
        duplicate_count_for_priority = count_duplicates_of(duplicate_match["tracking_id"], conn) + 1

    priority_score, priority_label = compute_priority(
        severity, duplicate_count=duplicate_count_for_priority, age_hours=0
    )

    tracking_id = generate_tracking_id()

    conn.execute(
        """
        INSERT INTO complaints
            (tracking_id, name, email, phone, type, location, description,
             photo_filename, status, created_at, updated_at,
             severity, department, priority_score, priority_label,
             sla_hours, sla_due_at, latitude, longitude,
             is_duplicate, duplicate_of, verification_status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            tracking_id, name, email, phone, issue_type, location, description,
            photo_filename, "Submitted", timestamp, timestamp,
            severity, department, priority_score, priority_label,
            sla_hours, sla_due_at, latitude, longitude,
            is_duplicate, duplicate_of, "Unverified",
        ),
    )
    conn.commit()

    # If this complaint bumped an existing one's duplicate count, refresh
    # that original complaint's priority score too.
    if duplicate_match:
        new_count = count_duplicates_of(duplicate_match["tracking_id"], conn)
        orig_age_hours = 0
        created = parse_dt(duplicate_match["created_at"])
        if created:
            orig_age_hours = (datetime.now() - created).total_seconds() / 3600
        orig_score, orig_label = compute_priority(
            duplicate_match["severity"] if "severity" in duplicate_match.keys() else "Low",
            duplicate_count=new_count,
            age_hours=orig_age_hours,
        )
        conn.execute(
            "UPDATE complaints SET priority_score = ?, priority_label = ? WHERE tracking_id = ?",
            (orig_score, orig_label, duplicate_match["tracking_id"]),
        )
        conn.commit()

    conn.close()

    return redirect(url_for("success", tracking_id=tracking_id))


@app.route("/success/<tracking_id>")
def success(tracking_id):
    conn = get_db_connection()
    row = conn.execute(
        "SELECT * FROM complaints WHERE tracking_id = ?", (tracking_id,)
    ).fetchone()
    conn.close()
    complaint = complaint_to_dict(row) if row else None
    return render_template("success.html", tracking_id=tracking_id, complaint=complaint)


@app.route("/track", methods=["GET", "POST"])
def track():
    complaint = None
    searched = False
    tracking_id_input = ""

    if request.method == "POST":
        tracking_id_input = request.form.get("tracking_id", "").strip().upper()
        searched = True
        if tracking_id_input:
            conn = get_db_connection()
            row = conn.execute(
                "SELECT * FROM complaints WHERE tracking_id = ?",
                (tracking_id_input,),
            ).fetchone()
            conn.close()
            if row:
                complaint = complaint_to_dict(row)
            else:
                flash(
                    f"No complaint found with tracking ID '{tracking_id_input}'. "
                    "Please check the ID and try again.",
                    "warning",
                )

    return render_template(
        "track.html",
        complaint=complaint,
        searched=searched,
        tracking_id_input=tracking_id_input,
    )


@app.route("/api/track/<tracking_id>")
def api_track(tracking_id):
    conn = get_db_connection()
    row = conn.execute(
        "SELECT * FROM complaints WHERE tracking_id = ?", (tracking_id.strip().upper(),)
    ).fetchone()
    conn.close()

    if not row:
        return jsonify({"success": False, "error": "Tracking ID not found."}), 404

    return jsonify({"success": True, "complaint": complaint_to_dict(row)})


@app.route("/verify/<tracking_id>", methods=["POST"])
def verify_complaint(tracking_id):
    """
    Lets the resident who holds the tracking ID confirm a Resolved
    complaint was actually fixed, or dispute it - which reopens the
    complaint back to 'In Progress' for another pass.
    """
    action = request.form.get("action", "").strip()
    tracking_id = tracking_id.strip().upper()

    conn = get_db_connection()
    row = conn.execute(
        "SELECT * FROM complaints WHERE tracking_id = ?", (tracking_id,)
    ).fetchone()

    if not row:
        conn.close()
        flash("Complaint not found.", "danger")
        return redirect(url_for("track"))

    if row["status"] != "Resolved":
        conn.close()
        flash("Only resolved complaints can be verified.", "warning")
        return redirect(url_for("track"))

    if action == "confirm":
        conn.execute(
            "UPDATE complaints SET verification_status = ?, verified_at = ? WHERE tracking_id = ?",
            ("Verified Fixed", now_str(), tracking_id),
        )
        conn.commit()
        flash("Thanks for confirming! This complaint is now marked as Verified.", "success")
    elif action == "dispute":
        conn.execute(
            """
            UPDATE complaints
            SET status = ?, updated_at = ?, verification_status = ?, verified_at = NULL
            WHERE tracking_id = ?
            """,
            ("In Progress", now_str(), "Disputed - Reopened", tracking_id),
        )
        conn.commit()
        flash("Thanks for letting us know. This complaint has been reopened.", "warning")
    else:
        flash("Unknown verification action.", "danger")

    conn.close()
    return redirect(url_for("track"))


@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    safe_name = secure_filename(filename)
    file_path = os.path.join(app.config["UPLOAD_FOLDER"], safe_name)
    if not os.path.isfile(file_path):
        abort(404)
    return send_from_directory(app.config["UPLOAD_FOLDER"], safe_name)


# ---------------------------------------------------------------------------
# Admin routes
# ---------------------------------------------------------------------------
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        if (
            username == app.config["ADMIN_USERNAME"]
            and password == app.config["ADMIN_PASSWORD"]
        ):
            session["admin_logged_in"] = True
            session["admin_username"] = username
            flash("Logged in successfully.", "success")
            return redirect(url_for("admin_dashboard"))

        flash("Invalid username or password.", "danger")
        return redirect(url_for("admin_login"))

    return render_template("admin_login.html")


@app.route("/admin/logout")
def admin_logout():
    session.pop("admin_logged_in", None)
    session.pop("admin_username", None)
    flash("You have been logged out.", "info")
    return redirect(url_for("admin_login"))


@app.route("/admin/dashboard")
@login_required
def admin_dashboard():
    status_filter = request.args.get("status", "All")
    department_filter = request.args.get("department", "All")

    conn = get_db_connection()

    query = "SELECT * FROM complaints WHERE 1=1"
    params = []
    if status_filter and status_filter != "All":
        query += " AND status = ?"
        params.append(status_filter)
    if department_filter and department_filter != "All":
        query += " AND department = ?"
        params.append(department_filter)
    query += " ORDER BY priority_score DESC, created_at DESC"

    rows = conn.execute(query, params).fetchall()
    complaints = [complaint_to_dict(r) for r in rows]

    # --- Chart data: counts by issue type (always all 4 types) ---
    type_counts = {}
    for t in app.config["ISSUE_TYPES"]:
        count_row = conn.execute(
            "SELECT COUNT(*) as cnt FROM complaints WHERE type = ?", (t,)
        ).fetchone()
        type_counts[t] = count_row["cnt"]

    # --- Chart data: counts by status ---
    status_counts = {}
    for s in app.config["STATUSES"]:
        count_row = conn.execute(
            "SELECT COUNT(*) as cnt FROM complaints WHERE status = ?", (s,)
        ).fetchone()
        status_counts[s] = count_row["cnt"]

    # --- Workload: open (non-resolved) complaints per department ---
    workload = []
    for dept in app.config["DEPARTMENTS"]:
        open_row = conn.execute(
            "SELECT COUNT(*) as cnt FROM complaints WHERE department = ? AND status != 'Resolved'",
            (dept,),
        ).fetchone()
        total_row = conn.execute(
            "SELECT COUNT(*) as cnt FROM complaints WHERE department = ?", (dept,)
        ).fetchone()
        open_rows_for_sla = conn.execute(
            "SELECT sla_due_at FROM complaints WHERE department = ? AND status != 'Resolved'",
            (dept,),
        ).fetchall()
        overdue = 0
        for r in open_rows_for_sla:
            due = parse_dt(r["sla_due_at"])
            if due and datetime.now() > due:
                overdue += 1
        workload.append({
            "department": dept,
            "open": open_row["cnt"],
            "total": total_row["cnt"],
            "overdue": overdue,
        })

    total_row = conn.execute("SELECT COUNT(*) as cnt FROM complaints").fetchone()
    total_complaints = total_row["cnt"]

    conn.close()

    # --- Heatmap points: only complaints that captured GPS coordinates ---
    heatmap_points = [
        [c["latitude"], c["longitude"]]
        for c in complaints
        if c["latitude"] is not None and c["longitude"] is not None
    ]

    overdue_total = sum(w["overdue"] for w in workload)

    return render_template(
        "admin_dashboard.html",
        complaints=complaints,
        status_filter=status_filter,
        department_filter=department_filter,
        statuses=["All"] + app.config["STATUSES"],
        departments=["All"] + app.config["DEPARTMENTS"],
        severities=app.config["SEVERITIES"],
        type_labels=json.dumps(list(type_counts.keys())),
        type_values=json.dumps(list(type_counts.values())),
        status_labels=json.dumps(list(status_counts.keys())),
        status_values=json.dumps(list(status_counts.values())),
        total_complaints=total_complaints,
        workload=workload,
        overdue_total=overdue_total,
        heatmap_points=json.dumps(heatmap_points),
    )


@app.route("/admin/update_status/<int:complaint_id>", methods=["POST"])
@login_required
def update_status(complaint_id):
    new_status = request.form.get("new_status", "").strip()
    resolution_note = request.form.get("resolution_note", "").strip()
    after_photo = request.files.get("after_photo")
    current_filter = request.form.get("current_filter", "All")
    current_dept_filter = request.form.get("current_department_filter", "All")

    conn = get_db_connection()
    row = conn.execute(
        "SELECT * FROM complaints WHERE id = ?", (complaint_id,)
    ).fetchone()

    if not row:
        conn.close()
        flash("Complaint not found.", "danger")
        return redirect(url_for("admin_dashboard"))

    current_status = row["status"]

    if new_status not in app.config["STATUSES"]:
        conn.close()
        flash("Invalid status value.", "danger")
        return redirect(url_for("admin_dashboard"))

    allowed_next = app.config["STATUS_TRANSITIONS"].get(current_status)

    if new_status == current_status:
        conn.close()
        flash("Complaint is already in that status.", "info")
        return redirect(url_for("admin_dashboard"))

    if allowed_next is None or new_status != allowed_next:
        conn.close()
        flash(
            f"Invalid status transition: '{current_status}' -> '{new_status}' "
            f"is not allowed. Statuses must progress "
            f"Submitted -> In Progress -> Resolved.",
            "danger",
        )
        return redirect(url_for("admin_dashboard"))

    # Optional "after" photo, captured when resolving, for a before/after view
    after_photo_filename = row["after_photo_filename"] if "after_photo_filename" in row.keys() else None
    if new_status == "Resolved" and after_photo and after_photo.filename:
        if allowed_file(after_photo.filename):
            after_photo_filename = save_uploaded_photo(after_photo)
        else:
            flash(
                "After-photo was skipped: invalid format "
                "(allowed: jpg, jpeg, png, gif, webp).",
                "warning",
            )

    updated_at = now_str()

    # Step 1: update the database first - this must succeed independently
    # of whether the notification email succeeds or fails.
    conn.execute(
        """
        UPDATE complaints
        SET status = ?, updated_at = ?, after_photo_filename = ?, resolution_note = ?
        WHERE id = ?
        """,
        (new_status, updated_at, after_photo_filename, resolution_note or None, complaint_id),
    )
    conn.commit()

    resident_email = row["email"]
    resident_name = row["name"]
    tracking_id = row["tracking_id"]
    issue_type = row["type"]
    location = row["location"]

    conn.close()

    flash(
        f"Status for {tracking_id} updated: {current_status} -> {new_status}.",
        "success",
    )

    # Step 2: attempt to send the email notification. Failure here is
    # logged and shown as a warning, but never rolls back the update above.
    email_sent, email_error = send_status_email(
        to_email=resident_email,
        name=resident_name,
        tracking_id=tracking_id,
        issue_type=issue_type,
        location=location,
        old_status=current_status,
        new_status=new_status,
        updated_at=updated_at,
    )

    if email_sent:
        flash(f"Notification email sent to {resident_email}.", "success")
    else:
        flash(
            f"Status was updated, but the notification email could not be sent "
            f"({email_error}). Please check the Gmail SMTP configuration in .env.",
            "warning",
        )

    return redirect(url_for("admin_dashboard", status=current_filter, department=current_dept_filter))


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    init_db()
    app.run(debug=True, host="127.0.0.1", port=5000)
