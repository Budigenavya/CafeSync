import os

# ======================================================
# CafeSync Configuration
# ======================================================

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# ===========================
# Flask
# ===========================

SECRET_KEY = "cafesync_super_secret_key"

DEBUG = True

HOST = "0.0.0.0"

PORT = 5000


# ===========================
# Database
# ===========================

DATABASE = os.path.join(BASE_DIR, "database.db")


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

ENABLE_SWIGGY = False

ENABLE_ZOMATO = False

SWIGGY_API_KEY = ""

ZOMATO_API_KEY = ""


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