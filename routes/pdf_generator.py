from reportlab.pdfgen import canvas

def create_sales_report(filename, sales):

    pdf = canvas.Canvas(filename)

    pdf.drawString(50, 800, "CafeSync Sales Report")

    y = 770

    for sale in sales:

        pdf.drawString(
            50,
            y,
            f"{sale['customer_name']} - ₹{sale['total']}"
        )

        y -= 20

    pdf.save()