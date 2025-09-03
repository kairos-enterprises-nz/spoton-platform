from __future__ import annotations

import os
from datetime import datetime
from decimal import Decimal

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.platypus import Table, TableStyle

from finance.invoices.models import Invoice


THEME = {
    "primary": "#40E0D0",
    "surface": "#F9FAFB",
    "background_light": "#F0F4F8",
    "highlight": "#FEF3C7",
    "text_subtle": "#333333",
    "footer_text": "#94A3B8",
    "card_bg": "#E6F7F7",
    "card_overdue": "#FEF2F2",
    "dark": "#2F4F4F",
    "black": "#3A3B3C",
}


def _hex(hex_str: str):
    return colors.HexColor(hex_str)


def render_pdf_reportlab(invoice_id: str, output_dir: str = "/app/media/invoices") -> str:
    invoice = Invoice.objects.select_related('bill', 'customer').prefetch_related('lines').get(id=invoice_id)

    lines = [li for li in invoice.lines.all() if li.service_type == 'broadband']
    os.makedirs(output_dir, exist_ok=True)
    pdf_path = os.path.join(output_dir, f"{invoice.invoice_number}.pdf")

    c = canvas.Canvas(pdf_path, pagesize=A4)
    width, height = A4
    margin = 20 * mm

    # Header background
    header_height = 30 * mm
    c.setFillColor(_hex(THEME["surface"]))
    c.rect(0, height - header_height, width, header_height, fill=1, stroke=0)

    # Logo/Title
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(margin, height - 18 * mm, "SpotOn Utilities")

    # Invoice meta
    right_x = width - margin
    c.setFont("Helvetica-Bold", 12)
    c.drawRightString(right_x, height - 12 * mm, "Tax Invoice")
    c.setFont("Helvetica", 9)
    c.drawRightString(right_x, height - 18 * mm, f"Invoice #: {invoice.invoice_number}")
    if invoice.issue_date:
        c.drawRightString(right_x, height - 24 * mm, f"Invoice Date: {invoice.issue_date.strftime('%d %b %Y')}")
    if invoice.due_date:
        c.drawRightString(right_x, height - 30 * mm, f"Due Date: {invoice.due_date.strftime('%d %b %Y')}")
    c.drawRightString(right_x, height - 36 * mm, "GST Number: 112-121-121")

    y = height - header_height - 10 * mm

    # Bill To box
    box_h = 25 * mm
    c.setFillColor(colors.white)
    c.setStrokeColor(_hex('#CBD5E1'))
    c.setLineWidth(0.7)
    c.roundRect(margin, y - box_h, width - 2 * margin, box_h, 4, fill=1, stroke=1)
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(colors.black)
    c.drawString(margin + 6, y - 8, "Bill To")
    c.setFont("Helvetica", 9)
    customer_name = getattr(invoice.customer, 'full_name', None) or getattr(invoice.customer, 'username', 'Customer')
    c.drawString(margin + 6, y - 18, customer_name)
    # Address placeholder (can be filled from Account later)
    c.setFillColor(_hex(THEME["text_subtle"]))
    c.drawString(margin + 6, y - 28, "")
    y -= box_h + 10

    # Broadband Charges title row
    title_h = 10 * mm
    c.setFillColor(_hex(THEME["dark"]))
    c.rect(margin, y - title_h, width - 2 * margin, title_h, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(margin + 6, y - 6, "Broadband Charges")
    c.setFont("Helvetica-Bold", 8)
    period = ''
    if invoice.bill and invoice.bill.period_start and invoice.bill.period_end:
        period = f"Billing Period: {invoice.bill.period_start.strftime('%d %b %Y')} - {invoice.bill.period_end.strftime('%d %b %Y')}"
    c.drawRightString(width - margin - 6, y - 6, period)
    y -= title_h + 6

    # Build table rows
    rows = [["Description", "Quantity", "Unit Price", "Amount"]]
    for li in lines:
        rows.append([
            li.description,
            f"{li.quantity}",
            f"$ {Decimal(li.unit_price):.2f}",
            f"$ {Decimal(li.amount):.2f}",
        ])
    # Totals
    rows.append(["", "", "Subtotal", f"$ {Decimal(invoice.subtotal):.2f}"])
    rows.append(["", "", "GST (15%)", f"$ {Decimal(invoice.tax_amount):.2f}"])
    rows.append(["", "", "Total Due", f"$ {Decimal(invoice.total_amount):.2f}"])

    col_widths = [ (width - 2 * margin) * 0.55, (width - 2 * margin) * 0.15, (width - 2 * margin) * 0.15, (width - 2 * margin) * 0.15 ]
    row_heights = [16] + [18] * (len(rows) - 1)

    tbl = Table(rows, colWidths=col_widths, rowHeights=row_heights)
    style = [
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("BACKGROUND", (0, 0), (-1, 0), _hex(THEME["surface"])),
        ("TEXTCOLOR", (0, 0), (-1, 0), _hex(THEME["dark"])),
        ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
        ("ALIGN", (0, 0), (0, -1), "LEFT"),
        ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.whitesmoke),
        ("LINEBELOW", (0, 1), (-1, -4), 0.3, colors.whitesmoke),
        ("ROWBACKGROUNDS", (0, 1), (-1, -4), [colors.white, _hex(THEME["background_light"])]),
        ("FONTNAME", (-2, -3), (-1, -1), "Helvetica-Bold"),
    ]
    # Highlight Total Due row
    style += [
        ("BACKGROUND", (-2, -1), (-1, -1), _hex(THEME["primary"])),
        ("TEXTCOLOR", (-2, -1), (-1, -1), colors.black),
    ]
    tbl.setStyle(TableStyle(style))
    tbl.wrapOn(c, width, y)
    tbl.drawOn(c, margin, y - sum(row_heights))
    y = y - sum(row_heights) - 12

    # Payment advice
    advice_h = 22 * mm
    c.setFillColor(colors.white)
    c.setStrokeColor(_hex(THEME["primary"]))
    c.setLineWidth(0.8)
    c.roundRect(margin, y - advice_h, 80 * mm, advice_h, 6, fill=1, stroke=1)
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(colors.black)
    c.drawString(margin + 8, y - 8, "Payment Advice")
    c.setFont("Helvetica", 8)
    c.drawString(margin + 8, y - 18, f"Please pay $ {Decimal(invoice.total_amount):.2f} before {invoice.due_date.strftime('%d %b %Y') if invoice.due_date else ''}.")
    c.drawString(margin + 8, y - 28, "Bank Account: Kairos Enterprises Limited – 03-1234-5678901-00")
    c.drawString(margin + 8, y - 38, f"Payment Reference: {invoice.customer_id or ''}")
    y -= advice_h + 10

    # Footer
    c.setFont("Helvetica", 7)
    c.setFillColor(_hex(THEME["footer_text"]))
    c.drawRightString(width - margin, 12 * mm, f"Page 1 of 1")
    c.setFillColor(colors.black)
    c.setFont("Helvetica", 7)
    c.drawString(margin, 12 * mm, "Kairos Enterprises Limited t/a SpotOn 45B Rutherford Street, Woolston, Christchurch 8023")

    c.showPage()
    c.save()

    return pdf_path

