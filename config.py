import os
import secrets
from dotenv import load_dotenv

# ======================================================
# CafeSync Configuration
# ======================================================

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))
load_dotenv(os.path.join(os.path.dirname(BASE_DIR), ".env"), override=False)

# ===========================
# Flask
# ===========================

# ===========================
# Database
# ===========================

# On hosts with an attached persistent disk, set CAFESYNC_DATA_DIR to its
# mount point (for example /var/data on Render). The app-local defaults keep
# development installs simple.
PERSISTENT_DATA_DIR = os.environ.get("CAFESYNC_DATA_DIR")
DATABASE = os.path.join(PERSISTENT_DATA_DIR, "database.db") if PERSISTENT_DATA_DIR else os.path.join(BASE_DIR, "database.db")
# PostgreSQL is opt-in. Keep SQLite as the default until compatibility testing passes.
DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()
USE_POSTGRES = (
    os.environ.get("CAFESYNC_USE_POSTGRES", "false").strip().lower()
    in {"1", "true", "yes"}
)

if USE_POSTGRES and not DATABASE_URL:
    raise RuntimeError(
        "CAFESYNC_USE_POSTGRES is enabled, but DATABASE_URL is not configured."
    )


def _secret_key():
    configured = os.environ.get("CAFESYNC_SECRET_KEY", "").strip()
    if configured:
        return configured

    # A PostgreSQL deployment should keep its Flask signing key in Render's
    # environment, not in the service's ephemeral filesystem or an unrelated
    # SQLite disk mount.
    if USE_POSTGRES:
        raise RuntimeError(
            "PostgreSQL mode requires CAFESYNC_SECRET_KEY to be configured "
            "in the service environment."
        )

    # Never ship a public, predictable Flask signing key. Keep the generated
    # key beside the persistent data when available so sessions survive restarts.
    secret_dir = PERSISTENT_DATA_DIR or BASE_DIR
    os.makedirs(secret_dir, exist_ok=True)
    secret_path = os.path.join(secret_dir, ".cafesync-secret")
    try:
        with open(secret_path, "x", encoding="utf-8") as secret_file:
            secret_file.write(secrets.token_urlsafe(48))
    except FileExistsError:
        pass
    with open(secret_path, "r", encoding="utf-8") as secret_file:
        value = secret_file.read().strip()
    if len(value) < 32:
        raise RuntimeError("CafeSync signing key is invalid. Set CAFESYNC_SECRET_KEY to a secure random value.")
    try:
        os.chmod(secret_path, 0o600)
    except OSError:
        pass
    return value


SECRET_KEY = _secret_key()

DEBUG = os.environ.get("CAFESYNC_DEBUG", "false").strip().lower() in {"1", "true", "yes"}

HOST = "0.0.0.0"

PORT = 5000


# ===========================
# Tax Settings
# ===========================

GST_PERCENTAGE = 5


# ===========================
# Currency
# ===========================

CURRENCY = "₹"


# ===========================
# Cafe Details
# ===========================

CAFE_NAME = "CafeSync"

CAFE_ADDRESS = "Your Cafe Address"

CAFE_PHONE = "9876543210"

CAFE_EMAIL = "cafesync@gmail.com"

GST_NUMBER = "GST123456789"


# ===========================
# Invoice
# ===========================

INVOICE_PREFIX = "INV"

KOT_PREFIX = "KOT"


# ===========================
# Printer
# ===========================

THERMAL_PRINTER = True

PRINTER_WIDTH = 80

AUTO_PRINT = False


# ===========================
# Barcode
# ===========================

ENABLE_BARCODE = True


# ===========================
# QR Payment
# ===========================

ENABLE_UPI = True

UPI_ID = "yourupi@bank"


# ===========================
# Uploads
# ===========================

UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
PRODUCT_IMAGE_FOLDER = os.path.join(PERSISTENT_DATA_DIR, "product-images") if PERSISTENT_DATA_DIR else os.path.join(UPLOAD_FOLDER, "products")

LOGO_FOLDER = os.path.join(BASE_DIR, "backend", "static", "logos")


# ===========================
# Backup
# ===========================

BACKUP_FOLDER = os.path.join(BASE_DIR, "database", "backup")


# ===========================
# Reports
# ===========================

REPORT_FOLDER = os.path.join(BASE_DIR, "reports")


# ===========================
# Swiggy & Zomato
# ===========================

ENABLE_SWIGGY = os.environ.get("ENABLE_SWIGGY", "false").lower() in {"1", "true", "yes"}

ENABLE_ZOMATO = os.environ.get("ENABLE_ZOMATO", "false").lower() in {"1", "true", "yes"}

SWIGGY_API_KEY = os.environ.get("SWIGGY_API_KEY", "")

ZOMATO_API_KEY = os.environ.get("ZOMATO_API_KEY", "")


# ===========================
# Security
# ===========================

SESSION_TIMEOUT = 30


# ===========================
# Theme
# ===========================

DEFAULT_THEME = "light"


# ===========================
# Version
# ===========================

APP_VERSION = "1.0.0"
