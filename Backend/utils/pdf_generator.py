# utils/pdf_generator.py
# -----------------------------------------------------------------------------
# UTILIDAD PARA LA GENERACIÓN DE ARCHIVOS PDF
# -----------------------------------------------------------------------------
# Este módulo contiene una función de utilidad para crear un recibo de pago
# en formato PDF usando la librería 'reportlab'.
# -----------------------------------------------------------------------------
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter  # Tamaño de página estándar (carta).
from reportlab.lib.units import inch  # Para usar pulgadas como unidad de medida.
import datetime


def create_invoice_pdf(invoice_data: dict):
    """
    Genera un archivo PDF para una factura/recibo y lo guarda en una ruta organizada.
    """
    now = datetime.datetime.now()
    year = str(now.year)
    month = str(now.month).zfill(
        2
    )  # 'zfill(2)' asegura 2 dígitos para el mes (ej. '07').

    # 1. Define una ruta de guardado organizada por año y mes.
    file_path = os.path.join("facturas", year, month)
    os.makedirs(file_path, exist_ok=True)  # Crea las carpetas si no existen.

    file_name = f"recibo_factura_{invoice_data['invoice_id']}.pdf"
    full_path = os.path.join(file_path, file_name)

    # 2. Crea el contenido del PDF usando un 'canvas' de reportlab.
    c = canvas.Canvas(full_path, pagesize=letter)
    width, height = letter  # Obtiene las dimensiones de la página.

    # Dibuja el Título.
    c.setFont("Helvetica-Bold", 16)
    c.drawString(1 * inch, height - 1 * inch, "Recibo de Pago")

    # Dibuja los datos del cliente y la factura.
    c.setFont("Helvetica", 12)
    text_y = height - 1.5 * inch  # Coordenada Y inicial para el texto.
    c.drawString(1 * inch, text_y, f"Cliente: {invoice_data['client_name']}")
    text_y -= 0.25 * inch  # Mueve la coordenada Y hacia abajo.
    c.drawString(1 * inch, text_y, f"Fecha de Pago: {invoice_data['payment_date']}")
    text_y -= 0.5 * inch  # Espacio adicional.
    c.drawString(1 * inch, text_y, f"Nro. de Factura: {invoice_data['invoice_id']}")
    text_y -= 0.25 * inch
    c.drawString(1 * inch, text_y, f"Plan Contratado: {invoice_data['plan_name']}")
    text_y -= 0.5 * inch

    # Dibuja el Total.
    c.setFont("Helvetica-Bold", 14)
    c.drawString(1 * inch, text_y, f"Total Pagado: ${invoice_data['amount_paid']:.2f}")

    c.save()  # Guarda el archivo PDF en disco.

    # 3. Devuelve la ruta relativa para ser guardada en la base de datos.
    # Se reemplazan las barras invertidas por barras normales para compatibilidad con URLs.
    return os.path.join(year, month, file_name).replace("\\", "/")
