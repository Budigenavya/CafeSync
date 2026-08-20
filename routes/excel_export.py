from openpyxl import Workbook

def export_products(filename, products):

    wb = Workbook()

    ws = wb.active

    ws.append([
        "ID",
        "Name",
        "Price",
        "Stock"
    ])

    for product in products:

        ws.append([
            product["id"],
            product["name"],
            product["price"],
            product["stock"]
        ])

    wb.save(filename)