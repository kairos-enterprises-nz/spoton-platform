from __future__ import annotations

import os
from datetime import datetime
from django.template.loader import render_to_string
from django.utils.html import escape
from weasyprint import HTML

from finance.invoices.models import Invoice


TEMPLATE_HTML = """
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8"/>
  <style>
    body { font-family: Arial, Helvetica, sans-serif; font-size: 12px; color: #111; }
    .header { display:flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px; }
    .h-left { font-weight: bold; font-size: 16px; }
    .h-right { text-align: right; font-size: 12px; }
    .box { border: 1px solid #e5e7eb; border-radius: 6px; padding: 10px; margin: 10px 0; }
    table { width: 100%; border-collapse: collapse; }
    th, td { padding: 8px; border-bottom: 1px solid #f0f0f0; }
    th { background: #f9fafb; text-align: left; }
    .totals { width: 300px; margin-left: auto; }
    .totals td { padding: 6px; }
    .right { text-align: right; }
    .footer { margin-top: 24px; font-size: 10px; color: #555; }
    .title { font-size: 14px; font-weight: bold; margin-top: 16px; }
  </style>
  <title>{{ invoice.invoice_number }}</title>
  </head>
<body>
  <div class="header">
    <div class="h-left">SpotOn Utilities</div>
    <div class="h-right">
      <div>Tax Invoice</div>
      <div>Invoice #: {{ invoice.invoice_number }}</div>
      <div>Invoice Date: {{ issue_date }}</div>
      <div>Due Date: {{ due_date }}</div>
      <div>GST Number: 112-121-121</div>
    </div>
  </div>

  <div class="box">
    <div class="title">Bill To</div>
    <div>{{ customer_name }}</div>
    {% if customer_address %}<div>{{ customer_address }}</div>{% endif %}
  </div>

  <div class="title">Broadband Charges</div>
  <table>
    <thead>
      <tr>
        <th>Description</th>
        <th class="right">Quantity</th>
        <th class="right">Unit Price</th>
        <th class="right">Amount</th>
      </tr>
    </thead>
    <tbody>
      {% for li in lines %}
      <tr>
        <td>{{ li.description }}</td>
        <td class="right">{{ li.quantity }}</td>
        <td class="right">{{ li.unit_price }}</td>
        <td class="right">{{ li.amount }}</td>
      </tr>
      {% endfor %}
    </tbody>
  </table>

  <table class="totals">
    <tr>
      <td>Subtotal</td>
      <td class="right">${{ invoice.subtotal }}</td>
    </tr>
    <tr>
      <td>GST (15%)</td>
      <td class="right">${{ invoice.tax_amount }}</td>
    </tr>
    <tr>
      <td><strong>Total Due</strong></td>
      <td class="right"><strong>${{ invoice.total_amount }}</strong></td>
    </tr>
  </table>

  <div class="footer">
    Kairos Enterprises Limited t/a SpotOn – 45B Rutherford Street, Woolston, Christchurch 8023
  </div>
</body>
</html>
"""


def render_pdf(invoice_id: str, output_dir: str = "/app/media/invoices") -> str:
    invoice = Invoice.objects.select_related('bill').prefetch_related('lines').get(id=invoice_id)

    # Filter only broadband lines for Phase A
    lines = [li for li in invoice.lines.all() if li.service_type == 'broadband']

    context = {
        'invoice': invoice,
        'issue_date': invoice.issue_date.strftime('%d %b %Y') if invoice.issue_date else '',
        'due_date': invoice.due_date.strftime('%d %b %Y') if invoice.due_date else '',
        'customer_name': getattr(invoice.customer, 'full_name', None) or getattr(invoice.customer, 'username', 'Customer'),
        'customer_address': '',  # TODO: fetch from Account/Address when available
        'lines': lines,
    }

    html = TEMPLATE_HTML
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    pdf_path = os.path.join(output_dir, f"{invoice.invoice_number}.pdf")

    HTML(string=html.replace("{{", "{% raw %}{{{% endraw %}").replace("}}", "{% raw %}}}{% endraw %}")).write_pdf(target=pdf_path, presentational_hints=True)
    # Re-render with simple string formatting via Django template system if needed in future
    # For now, use minimal interpolation manually as above

    # Second pass using Django templating for variables
    rendered = html
    for key, value in context.items():
        # Skip complex types except invoice fields used above; robust templating can be added later
        if isinstance(value, str):
            rendered = rendered.replace(f"{{{{ {key} }}}}", escape(value))
    HTML(string=rendered).write_pdf(target=pdf_path, presentational_hints=True)

    return pdf_path

