from datetime import datetime

def current_time():
    return datetime.now()

def format_currency(amount):
    return f"₹{amount:.2f}"

def success(message, data=None):
    return {
        "success": True,
        "message": message,
        "data": data
    }

def error(message):
    return {
        "success": False,
        "message": message
    }