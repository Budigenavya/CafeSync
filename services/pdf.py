import os

from reportlab.lib.units import mm
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle
)
from reportlab.lib import colors


class PDFInvoice:

    def __init__(self, filename):

        os.makedirs("invoices", exist_ok=True)

        self.filename = filename

        self.doc = SimpleDocTemplate(

            filename,

            pagesize=(80 * mm, 250 * mm),

            rightMargin=5,

            leftMargin=5,

            topMargin=5,

            bottomMargin=5

        )

        self.styles = getSampleStyleSheet()

        self.story = []

    # =======================================
    # Cafe Header
    # =======================================

    def add_header(self, cafe):

        title = self.styles["Heading2"]

        title.alignment = TA_CENTER

        self.story.append(
            Paragraph(cafe["name"], title)
        )

        normal = self.styles["BodyText"]

        normal.alignment = TA_CENTER

        self.story.append(
            Paragraph(cafe["address"], normal)
        )

        self.story.append(
            Paragraph(
                f"Phone : {cafe['phone']}",
                normal
            )
        )

        self.story.append(
            Paragraph(
                f"GST : {cafe['gst_number']}",
                normal
            )
        )

        self.story.append(
            Spacer(1, 5)
        )

    # =======================================
    # Invoice Details
    # =======================================

    def add_invoice_info(self, order):

        normal = self.styles["BodyText"]

        self.story.append(
            Paragraph(
                f"<b>Bill No :</b> {order['bill_no']}",
                normal
            )
        )

        self.story.append(
            Paragraph(
                f"<b>Date :</b> {order['created_at']}",
                normal
            )
        )

        self.story.append(
            Paragraph(
                f"<b>Table :</b> {order['table_name']}",
                normal
            )
        )

        self.story.append(
            Paragraph(
                f"<b>Payment :</b> {order['payment_method']}",
                normal
            )
        )

        self.story.append(
            Spacer(1, 5)
        )

    # =======================================
    # Customer
    # =======================================

    def add_customer(self, customer):

        normal = self.styles["BodyText"]

        self.story.append(
            Paragraph(
                "<b>Customer Details</b>",
                normal
            )
        )

        self.story.append(
            Paragraph(
                f"Name : {customer['name']}",
                normal
            )
        )

        self.story.append(
            Paragraph(
                f"Phone : {customer['phone']}",
                normal
            )
        )

        self.story.append(
            Spacer(1, 5)
        )

    # =======================================
    # Item Table
    # =======================================

    def add_items(self, items):

        data = [

            [

                "Item",

                "Qty",

                "Rate",

                "Total"

            ]

        ]

        for item in items:

            data.append([

                item["name"],

                str(item["quantity"]),

                f"{item['price']:.2f}",

                f"{item['total']:.2f}"

            ])

        table = Table(

            data,

            colWidths=[28*mm,10*mm,16*mm,18*mm]

        )

        table.setStyle(TableStyle([

            ("GRID",(0,0),(-1,-1),0.4,colors.black),

            ("BACKGROUND",(0,0),(-1,0),colors.lightgrey),

            ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),

            ("ALIGN",(1,1),(-1,-1),"CENTER"),

            ("BOTTOMPADDING",(0,0),(-1,0),6)

        ]))

        self.story.append(table)

        self.story.append(
            Spacer(1,5)
        )
    # =======================================
    # Bill Summary
    # =======================================

    def add_summary(self, order):

        data = [

            ["Subtotal", f"₹ {order['subtotal']:.2f}"],

            ["GST", f"₹ {order['gst']:.2f}"],

            ["Discount", f"₹ {order['discount']:.2f}"],

            ["Grand Total", f"₹ {order['total']:.2f}"]

        ]

        table = Table(
            data,
            colWidths=[40*mm,30*mm]
        )

        table.setStyle(TableStyle([

            ("GRID",(0,0),(-1,-1),0.4,colors.black),

            ("BACKGROUND",(0,3),(-1,3),colors.lightgrey),

            ("FONTNAME",(0,3),(-1,3),"Helvetica-Bold"),

            ("ALIGN",(1,0),(-1,-1),"RIGHT"),

            ("BOTTOMPADDING",(0,0),(-1,-1),6)

        ]))

        self.story.append(table)

        self.story.append(
            Spacer(1,8)
        )


    # =======================================
    # Footer
    # =======================================

    def add_footer(self):

        normal = self.styles["BodyText"]

        normal.alignment = TA_CENTER

        self.story.append(

            Paragraph(
                "<b>Thank You!</b>",
                normal
            )

        )

        self.story.append(

            Paragraph(
                "Visit Again",
                normal
            )

        )

        self.story.append(

            Paragraph(
                "Powered by CafeSync POS",
                normal
            )

        )

        self.story.append(
            Spacer(1,5)
        )


    # =======================================
    # Save PDF
    # =======================================

    def build(self):

        self.doc.build(self.story)
# =======================================
# Generate PDF Invoice
# =======================================

def generate_invoice_pdf(order, items):

    filename = os.path.join(
        "invoices",
        f"{order['bill_no']}.pdf"
    )

    cafe = {

        "name": "CafeSync",

        "address": "Your Cafe Address",

        "phone": "9876543210",

        "gst_number": "GST123456789"

    }

    customer = {

        "name": order.get("customer_name", "Walk-in Customer"),

        "phone": order.get("customer_phone", "")

    }

    pdf = PDFInvoice(filename)

    pdf.add_header(cafe)

    pdf.add_invoice_info(order)

    pdf.add_customer(customer)

    pdf.add_items(items)

    pdf.add_summary(order)

    pdf.add_footer()

    pdf.build()

    return filename