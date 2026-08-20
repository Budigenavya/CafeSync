import re

def validate_email(email):
    pattern = r'^[^@]+@[^@]+\.[^@]+$'
    return re.match(pattern, email) is not None

def validate_phone(phone):
    return phone.isdigit() and len(phone) == 10

def validate_price(price):
    try:
        return float(price) >= 0
    except:
        return False

def validate_stock(stock):
    try:
        return int(stock) >= 0
    except:
        return False