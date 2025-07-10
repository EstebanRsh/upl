# utils/pdf_generator.py
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
import datetime


def create_invoice_pdf(invoice_data: dict):
    """
    Genera un archivo PDF para una factura/recibo y lo guarda en una ruta organizada.
    """
    now = datetime.datetime.now()
    year = str(now.year)
    month = str(now.month).zfill(
        2
    )  # zfill(2) asegura que el mes tenga 2 dígitos (ej. 08)

    # 1. Definir la ruta de guardado: facturas/año/mes/
    file_path = os.path.join("facturas", year, month)
    os.makedirs(file_path, exist_ok=True)  # Crea las carpetas si no existen

    file_name = f"recibo_factura_{invoice_data['invoice_id']}.pdf"
    full_path = os.path.join(file_path, file_name)

    # 2. Crear el contenido del PDF
    c = canvas.Canvas(full_path, pagesize=letter)
    width, height = letter  # Ancho y alto de la página

    # Título
    c.setFont("Helvetica-Bold", 16)
    c.drawString(1 * inch, height - 1 * inch, "Recibo de Pago")

    # Datos del cliente y la factura
    c.setFont("Helvetica", 12)
    text_y = height - 1.5 * inch

    c.drawString(1 * inch, text_y, f"Cliente: {invoice_data['client_name']}")
    text_y -= 0.25 * inch
    c.drawString(1 * inch, text_y, f"Fecha de Pago: {invoice_data['payment_date']}")
    text_y -= 0.5 * inch  # Espacio

    c.drawString(1 * inch, text_y, f"Nro. de Factura: {invoice_data['invoice_id']}")
    text_y -= 0.25 * inch
    c.drawString(1 * inch, text_y, f"Plan Contratado: {invoice_data['plan_name']}")
    text_y -= 0.5 * inch  # Espacio

    # Total
    c.setFont("Helvetica-Bold", 14)
    c.drawString(1 * inch, text_y, f"Total Pagado: ${invoice_data['amount_paid']:.2f}")

    c.save()  # Guardar el archivo PDF

    # 3. Devolver la ruta relativa para guardarla en la base de datos
    # Se usa .replace para asegurar que las barras sean compatibles con URLs
    return os.path.join(year, month, file_name).replace("\\", "/")
