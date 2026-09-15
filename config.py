"""
Configuration for the City Complaint Tracking MVP.
All sensitive values (Gmail credentials, admin password, secret key) are
loaded from environment variables via a local .env file so nothing
sensitive is hardcoded into source control.
"""
import os
from dotenv import load_dotenv

# Load variables from a .env file in the project root (if present)
load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    # --- Core Flask config ---
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")

    # --- Database ---
    DATABASE = os.path.join(BASE_DIR, "complaints.db")

    # --- Uploads ---
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
    ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "gif", "webp"}
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 MB max upload size

    # --- Admin credentials (MVP only - not for production use) ---
    ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")

    # --- Gmail SMTP configuration (loaded from environment) ---
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME", "")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD", "")
    MAIL_SERVER = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", 587))

    # --- Complaint domain values ---
    ISSUE_TYPES = ["Pothole", "Garbage", "Streetlight", "Other"]
    STATUSES = ["Submitted", "In Progress", "Resolved"]

    # Valid forward-only status transitions (admin-driven).
    # Residents can additionally send a Resolved complaint back to
    # "In Progress" via the verification/dispute flow - that path is
    # handled separately in the /verify route, not here.
    STATUS_TRANSITIONS = {
        "Submitted": "In Progress",
        "In Progress": "Resolved",
        "Resolved": None,
    }

    # --- Severity / priority / SLA / department config ---
    SEVERITIES = ["Low", "Medium", "High", "Critical"]

    SEVERITY_WEIGHT = {"Low": 10, "Medium": 30, "High": 60, "Critical": 90}

    PRIORITY_THRESHOLDS = [
        (80, "Urgent"),
        (55, "High"),
        (30, "Medium"),
        (0, "Low"),
    ]

    # SLA response window (hours) allowed per severity level before a
    # complaint is considered overdue.
    SLA_HOURS = {"Critical": 24, "High": 72, "Medium": 168, "Low": 336}

    DEPARTMENT_MAP = {
        "Pothole": "Public Works",
        "Streetlight": "Electrical Dept.",
        "Garbage": "Sanitation Dept.",
        "Other": "General Services",
    }
    DEPARTMENTS = sorted(set(DEPARTMENT_MAP.values()))

    # Duplicate-detection tuning
    DUPLICATE_LOCATION_SIMILARITY = 0.6  # 0-1, higher = stricter match
    DUPLICATE_WINDOW_DAYS = 14
