from datetime import datetime


def line(width=42):
    return "-" * width


def center(text, width=42):
    return text.center(width)


def left_right(left, right, width=42):
    left = str(left)
    right = str(right)

    spaces = width - len(left) - len(right)

    if spaces < 1:
        spaces = 1

    return left + (" " * spaces) + right


def generate_thermal_receipt(order, items, cafe):

    receipt = ""

    receipt += center(cafe["name"]) + "\n"
    receipt += center(cafe["address"]) + "\n"
    receipt += center("Phone : " + cafe["phone"]) + "\n"
    receipt += center("GST : " + cafe["gst_number"]) + "\n"

    receipt += line() + "\n"

    receipt += left_right("Bill", order["bill_no"]) + "\n"
    receipt += left_right("Date", str(order["created_at"])) + "\n"
    receipt += left_right("Table", str(order["table_name"])) + "\n"
    receipt += left_right("Payment", order["payment_method"]) + "\n"

    receipt += line() + "\n"

    receipt += "{:<18}{:>6}{:>8}{:>10}\n".format(
        "Item",
        "Qty",
        "Rate",
        "Total"
    )

    receipt += line() + "\n"

    for item in items:

        receipt += "{:<18}{:>6}{:>8.2f}{:>10.2f}\n".format(
            item["name"][:18],
            item["quantity"],
            item["price"],
            item["total"]
        )

    receipt += line() + "\n"

    receipt += left_right(
        "Subtotal",
        f"{order['subtotal']:.2f}"
    ) + "\n"

    receipt += left_right(
        "GST",
        f"{order['gst']:.2f}"
    ) + "\n"

    receipt += left_right(
        "Discount",
        f"{order['discount']:.2f}"
    ) + "\n"

    receipt += line() + "\n"

    receipt += left_right(
        "TOTAL",
        f"{order['total']:.2f}"
    ) + "\n"

    receipt += line() + "\n"

    receipt += center("Thank You!") + "\n"
    receipt += center("Visit Again") + "\n"

    receipt += "\n\n\n"

    return receipt