from __future__ import annotations

import datetime
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.platypus import Table, TableStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


THEME = {
    "primary": "#40E0D0",
    "accent": "#AEEEEE",
    "background_light": "#F0F4F8",
    "surface": "#F9FAFB",
    "highlight": "#FEF3C7",
    "text_subtle": "#333333",
    "footer_text": "#94A3B8",
    "card_bg": "#E6F7F7",
    "card_overdue": "#FEF2F2",
    "dark": "#2F4F4F",
    "black": "#3A3B3C",
    "soft_grey": "#64748B",
}


def _register_fonts():
    try:
        pdfmetrics.registerFont(TTFont("Prompt", "fonts/Prompt-Regular.ttf"))
        pdfmetrics.registerFont(TTFont("Prompt-Bold", "fonts/Prompt-Bold.ttf"))
    except Exception:
        # Fallback to built-in Helvetica if custom fonts unavailable
        pass


def _font_exists(name: str) -> bool:
    try:
        pdfmetrics.getFont(name)
        return True
    except Exception:
        return False


def _font(name: str) -> str:
    if _font_exists(name):
        return name
    # map to Helvetica variants
    return "Helvetica-Bold" if name.endswith("-Bold") else "Helvetica"


def draw_header(c, title, margin, width, height, data=None, show_invoice_details=True):
    y = height - margin
    header_height = 65

    # Full-width background
    c.setFillColor(colors.HexColor(THEME["surface"]))
    c.rect(0, y - header_height, width, header_height + margin, fill=1, stroke=0)

    # Logo / Title
    c.setFont(_font("Prompt-Bold"), 10)
    c.setFillColor(colors.black)
    c.drawString(margin, y - 20, "SpotOn Utilities")

    # Format invoice date
    invoice_date = ""
    if data and show_invoice_details:
        try:
            invoice_date = datetime.datetime.strptime(data.get("invoice_date", ""), "%Y%m%d").strftime("%d %b %Y")
        except Exception:
            invoice_date = data.get("invoice_date", "")

    # Page 1 Header: Tax Invoice and GST
    if title == "Tax Invoice":
        c.setFillColor(colors.HexColor(THEME["black"]))
        c.setFont(_font("Prompt-Bold"), 14)
        c.drawRightString(width - margin, y - 5, "Tax Invoice")
        c.setFont(_font("Prompt"), 9)
        c.drawRightString(width - margin, y - 25, "GST Number : 112-121-121")
    else:
        c.setFillColor(colors.HexColor(THEME["black"]))
        c.setFont(_font("Prompt"), 8)
        if data:
            c.drawRightString(width - margin, y - 0, f"Customer Number: {data.get('account_id', '')}")
            c.drawRightString(width - margin, y - 17, f"Invoice Date: {invoice_date}")
            c.drawRightString(width - margin, y - 34, f"Invoice Number: {data.get('invoice_number', '')}")

    return y - 100


def invoice_details(c, data, x, y, width):
    label_font = _font("Prompt")
    value_font = _font("Prompt-Bold")
    spacing = 40
    badge_height = 26

    # Date
    raw_date = data.get("invoice_date", "")
    try:
        date_value = datetime.datetime.strptime(raw_date, "%Y%m%d").strftime("%d %b %Y")
    except Exception:
        date_value = raw_date

    # Invoice date badge
    c.setLineWidth(1)
    c.setStrokeColor(colors.white)
    c.setFillColor(colors.white)
    date_label = "Invoice Date:"
    c.roundRect(x, y - badge_height, 180, badge_height, 4, fill=1, stroke=1)
    c.setFont(label_font, 8)
    c.setFillColor(colors.black)
    c.drawString(x + 0, y - 15, date_label)
    c.setFont(value_font, 10)
    c.drawString(x + 4 + c.stringWidth(date_label, label_font, 8), y - 15, date_value)

    # Invoice number badge
    x_number = x + 200
    number_label = "Invoice Number:"
    c.setStrokeColor(colors.white)
    c.setFillColor(colors.white)
    c.roundRect(x_number, y - badge_height, 200, badge_height, 4, fill=1, stroke=1)
    c.setFont(label_font, 8)
    c.setFillColor(colors.black)
    c.drawString(x_number + 0, y - 15, number_label)
    c.setFont(value_font, 10)
    c.drawString(x_number + 4 + c.stringWidth(number_label, label_font, 8), y - 15, data.get("invoice_number", ""))

    # Customer badge (right)
    customer_badge_height = int(badge_height * 1.5)
    badge_x = width - x - 160
    c.setLineWidth(1)
    c.setStrokeColor(colors.cadetblue)
    c.setFillColor(colors.white)
    c.roundRect(badge_x, y - customer_badge_height, 160, customer_badge_height, 4, fill=0, stroke=1)
    divider_y = y - customer_badge_height + customer_badge_height / 2
    c.setStrokeColor(colors.cadetblue)
    c.setLineWidth(0.6)
    c.line(badge_x, divider_y, badge_x + 160, divider_y)
    c.setFillColor(colors.black)
    c.setFont(label_font, 10)
    c.drawCentredString(badge_x + 80, divider_y + 8, "Account Number")
    c.setFont(value_font, 10)
    c.drawCentredString(badge_x + 80, divider_y - 12, data.get("account_id", ""))

    return y - customer_badge_height - 20


def draw_customer_block(c, data, x, y, width):
    card_height = 75
    card_width = 300
    c.setFillColor(colors.whitesmoke)
    c.roundRect(x, y - card_height, card_width, card_height, 6, fill=1, stroke=0)
    c.setFillColor(colors.black)
    c.setFont(_font("Prompt-Bold"), 11)
    c.drawString(x + 20, y - 20, data.get("customer_name", ""))
    c.setFont(_font("Prompt"), 10)
    addr = (data.get("customer_address") or "").split(",")
    for i, line in enumerate([a.strip() for a in addr if a.strip()]):
        c.drawString(x + 20, y - 38 - (i * 12), line)
    return y - card_height - 15


def draw_invoice_summary_table(c, data, x, y, width):
    c.setFont(_font("Prompt-Bold"), 16)
    y -= 25
    c.drawString(x + 2, y, "Account Summary")
    y -= 10

    def format_currency(value):
        if value < 0:
            return f"($ {abs(value):.2f})"
        return f"$ {value:.2f}"

    broadband = float(data.get('broadband_subtotal', 0.0))
    rows = []
    rows.append(["Previous Charges", ""])  # header
    rows.append(["Previous Balance", format_currency(float(data.get('previous_balance', 0.0)))])
    rows.append(["Payments Received", format_currency(float(data.get('payments_total', 0.0)))])
    opening_balance_index = len(rows)
    rows.append(["Opening Balance (before Current Invoice Charges)", format_currency(float(data.get('opening_balance', 0.0)))])
    rows.append(["", ""])  # spacer
    rows.append(["Current Invoice Charges", ""])  # header
    if broadband:
        rows.append(["Broadband Charges", format_currency(broadband)])
    rows.append(["", ""])  # spacer
    rows.append(["Invoice Summary", ""])  # header
    rows.append(["Total Current Invoice Charges", format_currency(float(data.get('subtotal', 0.0)))])
    rows.append(["GST (15%)", format_currency(float(data.get('gst', 0.0)))])
    rows.append(["Total Due", format_currency(float(data.get('total', 0.0)))])

    row_heights = [12 if row == ["", ""] else 20 for row in rows]
    table = Table(rows, colWidths=[200, 100], rowHeights=row_heights)
    style = [
        ("FONTNAME", (0, 0), (-1, -1), _font("Prompt")),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.white]),
    ]
    section_titles = ["Previous Charges", "Current Invoice Charges", "Invoice Summary"]
    for idx, row in enumerate(rows):
        if row[0] in section_titles:
            style.extend([
                ("SPAN", (0, idx), (1, idx)),
                ("FONTNAME", (0, idx), (-1, idx), _font("Prompt-Bold")),
                ("FONTSIZE", (0, idx), (-1, idx), 9),
                ("BACKGROUND", (0, idx), (-1, idx), colors.white),
                ("TOPPADDING", (0, idx), (-1, idx), 8),
                ("BOTTOMPADDING", (0, idx), (-1, idx), 6),
                ("LINEABOVE", (0, idx), (-1, idx), 0.7, colors.HexColor(THEME["primary"])),
                ("LINEBELOW", (0, idx), (-1, idx), 0.7, colors.HexColor(THEME["primary"])),
            ])
    style.extend([
        ("FONTNAME", (0, opening_balance_index), (-1, opening_balance_index), _font("Prompt")),
        ("BACKGROUND", (0, opening_balance_index), (-1, opening_balance_index), colors.HexColor(THEME["card_bg"])),
    ])
    total_due_index = len(rows) - 1
    style.extend([
        ("FONTNAME", (0, total_due_index), (-1, total_due_index), _font("Prompt-Bold")),
        ("FONTSIZE", (0, total_due_index), (-1, total_due_index), 10),
        ("BACKGROUND", (0, total_due_index), (-1, total_due_index), colors.HexColor(THEME["primary"])),
        ("TEXTCOLOR", (0, total_due_index), (-1, total_due_index), colors.black),
    ])
    table.setStyle(TableStyle(style))
    table.wrapOn(c, width, y)
    table.drawOn(c, x, y - sum(row_heights))
    return y - sum(row_heights) - 20


def draw_broadband_table(c, broadband_data, x, y, width):
    def format_currency(val):
        return f"$ {val:.2f}"

    connection_details = broadband_data.get("connection_details", {})
    billing_period = connection_details.get("billing_period", "-")
    line_items = broadband_data.get("line_items", [])
    total = 0.0

    from reportlab.lib.styles import ParagraphStyle
    from reportlab.platypus import Paragraph
    from reportlab.lib.enums import TA_LEFT, TA_RIGHT
    import html

    title_style = ParagraphStyle(name="TableTitleLeft", fontName=_font("Prompt-Bold"), fontSize=9, leading=12, textColor=colors.white, alignment=TA_LEFT)
    period_style = ParagraphStyle(name="TableTitleRight", fontName=_font("Prompt-Bold"), fontSize=6.5, leading=10, textColor=colors.HexColor(THEME["highlight"]), alignment=TA_RIGHT)
    title_para = Paragraph("Broadband Charges", title_style)
    period_para = Paragraph(f"Billing Period: {html.escape(billing_period)}", period_style)

    rows = []
    rows.append([title_para, period_para, "", ""])
    rows.append(["Description", "Amount", "GST", "Total"])
    for item in line_items:
        amt = float(item.get("amount", 0.0))
        gst = float(item.get("gst", round(amt * 0.15, 2)))
        tot = float(item.get("total", round(amt + gst, 2)))
        total += tot
        rows.append([item.get("description", ""), format_currency(amt), format_currency(gst), format_currency(tot)])
    rows.append(["Broadband Charges", "", "", format_currency(total)])

    col_widths = [305, 70, 70, 70]
    row_heights = [22] * len(rows)
    table = Table(rows, colWidths=col_widths, rowHeights=row_heights)
    style = [
        ("FONTNAME", (0, 0), (-1, -1), _font("Prompt")),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor(THEME["black"])),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (1, 2), (-1, -1), "RIGHT"),
        ("ROWBACKGROUNDS", (0, 2), (-1, len(rows) - 2), [colors.white, colors.HexColor(THEME["background_light"])]),
        ("SPAN", (0, 0), (0, 0)),
        ("SPAN", (1, 0), (3, 0)),
        ("ALIGN", (0, 0), (0, 0), "LEFT"),
        ("ALIGN", (1, 0), (3, 0), "RIGHT"),
        ("FONTNAME", (0, 0), (-1, 0), _font("Prompt-Bold")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("TOPPADDING", (0, 0), (-1, 0), 8),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(THEME["dark"])),
        ("LINEABOVE", (0, 0), (-1, 0), 0.6, colors.whitesmoke),
        ("LINEBELOW", (0, 0), (-1, 0), 0.6, colors.whitesmoke),
        ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor(THEME["surface"])),
        ("TEXTCOLOR", (0, 1), (-1, 1), colors.HexColor(THEME["dark"])),
        ("FONTNAME", (0, 1), (-1, 1), _font("Prompt-Bold")),
        ("ALIGN", (0, 1), (0, 1), "LEFT"),
        ("ALIGN", (1, 1), (-1, 1), "RIGHT"),
        ("LINEABOVE", (0, 1), (-1, 1), 0.5, colors.whitesmoke),
        ("LINEBELOW", (0, 1), (-1, 1), 0.5, colors.whitesmoke),
        ("SPAN", (0, -1), (2, -1)),
        ("ALIGN", (0, -1), (2, -1), "LEFT"),
        ("ALIGN", (3, -1), (3, -1), "RIGHT"),
        ("FONTNAME", (0, -1), (-1, -1), _font("Prompt-Bold")),
        ("TEXTCOLOR", (0, -1), (-1, -1), colors.slategrey),
        ("FONTSIZE", (0, -1), (-1, -1), 8),
        ("LINEABOVE", (0, -1), (-1, -1), 0.75, colors.HexColor(THEME["primary"])),
        ("LINEBELOW", (0, -1), (-1, -1), 0.75, colors.HexColor(THEME["primary"])),
    ]
    table.setStyle(TableStyle(style))
    table.wrapOn(c, width, y)
    table.drawOn(c, x, y - sum(row_heights))
    return y - sum(row_heights) - 20


def draw_payment_options(c, x, y, data):
    due_amount = f"$ {data.get('total', 0.00):.2f}"
    due_date = data.get("due_date", "")
    payment_type = (data.get("payment_type", "") or "").lower()
    account_ref = data.get("account_id", "N/A")
    bank_account_name = "Kairos Enterprises Limited"
    bank_account_number = "03-1234-5678901-00"

    is_direct_debit = payment_type == "direct debit"
    box_width = 350 if is_direct_debit else 280
    box_height = 60 if is_direct_debit else 85
    box_padding = 8
    box_y = y - box_height - 10

    c.setLineWidth(1)
    c.setStrokeColor(colors.HexColor(THEME["primary"]))
    c.setFillColor(colors.white)
    c.roundRect(x, box_y, box_width, box_height, 6, fill=1, stroke=1)
    c.setFont(_font("Prompt-Bold"), 10)
    c.setFillColor(colors.black)

    if is_direct_debit:
        c.drawString(x + box_padding, box_y + box_height - 20, "Direct Debit Advice")
        c.setFont(_font("Prompt"), 8)
        prefix = "Unless advice to the contrary is received from you "
        suffix = " will be direct debited"
        c.drawString(x + box_padding, box_y + box_height - 35, prefix)
        c.setFont(_font("Prompt-Bold"), 8)
        c.drawString(x + box_padding + c.stringWidth(prefix, _font("Prompt"), 8), box_y + box_height - 35, due_amount)
        c.setFont(_font("Prompt"), 8)
        c.drawString(x + box_padding + c.stringWidth(prefix + due_amount, _font("Prompt"), 8), box_y + box_height - 35, suffix)
        c.drawString(x + box_padding, box_y + box_height - 47, f"from your authorised bank account on the {due_date}.")
    else:
        c.drawString(x + box_padding, box_y + box_height - 20, "Payment Advice")
        c.setFont(_font("Prompt"), 8)
        prefix = "Please pay "
        suffix = f" into our account before {due_date}."
        c.drawString(x + box_padding, box_y + box_height - 35, prefix)
        c.setFont(_font("Prompt-Bold"), 8)
        c.drawString(x + box_padding + c.stringWidth(prefix, _font("Prompt"), 8), box_y + box_height - 35, due_amount)
        c.setFont(_font("Prompt"), 8)
        c.drawString(x + box_padding + c.stringWidth(prefix + due_amount, _font("Prompt"), 8), box_y + box_height - 35, suffix)
        c.setFont(_font("Prompt"), 8)
        c.drawString(x + box_padding, box_y + box_height - 50, "Bank Account Name:")
        c.drawString(x + box_padding + 100, box_y + box_height - 50, bank_account_name)
        c.drawString(x + box_padding, box_y + box_height - 62, "Bank Account Number:")
        c.drawString(x + box_padding + 100, box_y + box_height - 62, bank_account_number)
        c.drawString(x + box_padding, box_y + box_height - 74, "Payment Reference:")
        c.drawString(x + box_padding + 100, box_y + box_height - 74, account_ref)
    return box_y - 20


def generate_invoice(file_path: str, data: dict):
    _register_fonts()
    c = canvas.Canvas(file_path, pagesize=A4)
    width, height = A4
    margin = 40

    # Page 1: Summary
    y = draw_header(c, "Tax Invoice", margin, width, height, data)
    y = invoice_details(c, data, margin, y, width)
    y = draw_customer_block(c, data, margin, y, width)
    y = draw_invoice_summary_table(c, data, margin, y, width)
    bottom_y = 150
    # Info cards omitted for brevity; keep payment advice
    draw_payment_options(c, margin, bottom_y + 15, data)
    # Footer
    c.setFont(_font("Prompt"), 6)
    c.setFillColor(colors.HexColor(THEME["footer_text"]))
    c.drawRightString(width - margin, 25, f"Page 1 of 2")
    c.setFillColor(colors.black)
    c.setFont(_font("Prompt"), 6)
    c.drawString(margin, 25, "Kairos Enterprises Limited t/a SpotOn 45B Rutherford Street, Woolston, Christchurch 8023")
    c.showPage()

    # Page 2: Broadband
    y = draw_header(c, "", margin, width, height, data, show_invoice_details=True)
    # Connection block minimal
    bb = (data.get("charges_by_utility", {}).get("Broadband") or [])
    broadband_conn = bb[0] if bb else {}
    y = draw_broadband_table(c, broadband_conn, margin, y, width)
    # Footer
    c.setFont(_font("Prompt"), 6)
    c.setFillColor(colors.HexColor(THEME["footer_text"]))
    c.drawRightString(width - margin, 25, f"Page 2 of 2")
    c.setFillColor(colors.black)
    c.setFont(_font("Prompt"), 6)
    c.drawString(margin, 25, "Kairos Enterprises Limited t/a SpotOn 45B Rutherford Street, Woolston, Christchurch 8023")
    c.showPage()
    c.save()

    
def render_from_invoice(invoice_id: str, output_dir: str = "/app/media/invoices") -> str:
    """
    Adapter: builds the data structure required by generate_invoice.py from our Invoice model
    and writes the PDF to output_dir using the same layout.
    """
    import os
    from finance.invoices.models import Invoice as InvoiceModel

    inv = (
        InvoiceModel.objects.select_related('bill', 'customer')
        .prefetch_related('lines')
        .get(id=invoice_id)
    )

    # Build summary fields
    invoice_date_raw = inv.issue_date.strftime('%Y%m%d') if inv.issue_date else ''
    billing_period = ''
    if inv.bill and inv.bill.period_start and inv.bill.period_end:
        billing_period = f"{inv.bill.period_start.strftime('%-d %b %Y')} - {inv.bill.period_end.strftime('%-d %b %Y')}"

    customer_name = getattr(inv.customer, 'full_name', None) or getattr(inv.customer, 'username', 'Customer')
    customer_address = ''
    account_id = str(getattr(inv.customer, 'id', ''))

    # Totals
    subtotal = float(inv.subtotal or 0)
    gst = float(inv.tax_amount or 0)
    total = float(inv.total_amount or 0)

    # Broadband-only line items
    bb_lines = [li for li in inv.lines.all() if li.service_type == 'broadband']
    broadband_subtotal = float(sum((li.amount or 0) for li in bb_lines))
    line_items = []
    for li in bb_lines:
        line_items.append({
            'description': li.description,
            'amount': float(li.amount or 0),
            'gst': float(li.tax_amount or 0),
            'total': float((li.amount or 0) + (li.tax_amount or 0)),
        })

    data = {
        'customer_name': customer_name,
        'customer_address': customer_address,
        'account_id': account_id,
        'invoice_date': invoice_date_raw,
        'invoice_number': inv.invoice_number,
        'billing_period': billing_period,
        'due_date': inv.due_date.strftime('%d %b %Y') if inv.due_date else '',
        'previous_balance': 0.0,
        'payments_total': 0.0,
        'electricity_subtotal': 0.0,
        'broadband_subtotal': broadband_subtotal,
        'subtotal': subtotal,
        'opening_balance': 0.0,
        'gst': gst,
        'total': total,
        'payment_type': 'Direct Debit',
        'charges_by_utility': {
            'Broadband': [
                {
                    'connection_name': '',
                    'connection_details': {
                        'Address': customer_address or 'Address on file',
                        'Type': 'Fibre Broadband',
                        'billing_period': billing_period,
                    },
                    'line_items': line_items,
                }
            ]
        },
    }

    os.makedirs(output_dir, exist_ok=True)
    pdf_path = os.path.join(output_dir, f"{inv.invoice_number}.pdf")
    generate_invoice(pdf_path, data)
    return pdf_path

