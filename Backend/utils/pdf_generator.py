# utils/pdf_generator.py
# -----------------------------------------------------------------------------
# UTILIDAD PARA LA GENERACIÓN DE ARCHIVOS PDF
# -----------------------------------------------------------------------------
# Este módulo contiene una función de utilidad para crear un recibo de pago
# en formato PDF usando la librería 'reportlab'.
# -----------------------------------------------------------------------------
# utils/pdf_generator.py
import os
import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors


def create_invoice_pdf(invoice_data: dict):
    """
    Genera un archivo PDF para una factura/recibo con un diseño mejorado.
    """
    now = datetime.datetime.now()
    year = str(now.year)
    month = str(now.month).zfill(2)

    file_path = os.path.join("facturas", year, month)
    os.makedirs(file_path, exist_ok=True)

    file_name = f"recibo_factura_{invoice_data['invoice_id']}.pdf"
    full_path = os.path.join(file_path, file_name)

    c = canvas.Canvas(full_path, pagesize=letter)
    width, height = letter

    # --- Encabezado ---
    c.setFont("Helvetica-Bold", 18)
    c.drawString(1 * inch, height - 1 * inch, "FACTURA")

    # Aquí podrías añadir un logo si tuvieras uno
    # c.drawImage("path/a/tu/logo.png", width - 2.5*inch, height - 1.25*inch, width=1.5*inch, preserveAspectRatio=True)

    c.setFont("Helvetica", 10)
    c.drawString(
        width - 3.5 * inch,
        height - 0.9 * inch,
        "FACTURA N°: " + str(invoice_data["invoice_id"]),
    )
    c.drawString(
        width - 3.5 * inch,
        height - 1.1 * inch,
        "Fecha de Emisión: " + invoice_data["issue_date"],
    )
    c.drawString(
        width - 3.5 * inch,
        height - 1.3 * inch,
        "Fecha de Vencimiento: " + invoice_data["due_date"],
    )
    c.drawString(
        width - 3.5 * inch,
        height - 1.5 * inch,
        "Fecha de Pago: " + invoice_data["payment_date"],
    )

    # --- Datos del Cliente y la Empresa ---
    c.setStrokeColor(colors.grey)
    c.line(1 * inch, height - 1.8 * inch, width - 1 * inch, height - 1.8 * inch)

    c.setFont("Helvetica-Bold", 11)
    c.drawString(1 * inch, height - 2.1 * inch, "Facturado a:")
    c.drawString(width / 2, height - 2.1 * inch, "De:")

    c.setFont("Helvetica", 10)
    c.drawString(1 * inch, height - 2.3 * inch, invoice_data["client_name"])
    c.drawString(1 * inch, height - 2.5 * inch, f"DNI: {invoice_data['client_dni']}")
    c.drawString(1 * inch, height - 2.7 * inch, invoice_data["client_address"])

    # Datos de tu empresa (puedes cargarlos desde la BD o ponerlos aquí)
    c.drawString(width / 2, height - 2.3 * inch, "Mi Empresa ISP S.A.")
    c.drawString(width / 2, height - 2.5 * inch, "CUIT: 30-12345678-9")
    c.drawString(width / 2, height - 2.7 * inch, "Dirección Ficticia 123, Ciudad")

    # --- Tabla de Detalles ---
    c.line(1 * inch, height - 3.2 * inch, width - 1 * inch, height - 3.2 * inch)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(1.1 * inch, height - 3.4 * inch, "Descripción")
    c.drawString(5 * inch, height - 3.4 * inch, "Cantidad")
    c.drawString(6 * inch, height - 3.4 * inch, "Precio Unitario")
    c.drawString(7 * inch, height - 3.4 * inch, "Total")
    c.line(1 * inch, height - 3.5 * inch, width - 1 * inch, height - 3.5 * inch)

    c.setFont("Helvetica", 10)
    y_position = height - 3.7 * inch

    # Servicio principal
    c.drawString(
        1.1 * inch,
        y_position,
        f"Servicio de Internet - Plan '{invoice_data['plan_name']}'",
    )
    c.drawString(5.2 * inch, y_position, "1")
    c.drawString(6.2 * inch, y_position, f"${invoice_data['base_amount']:.2f}")
    c.drawString(7.2 * inch, y_position, f"${invoice_data['base_amount']:.2f}")
    y_position -= 0.3 * inch

    # Cargo por mora (si aplica)
    if invoice_data["late_fee"] > 0:
        c.drawString(1.1 * inch, y_position, "Cargo por mora")
        c.drawString(5.2 * inch, y_position, "1")
        c.drawString(6.2 * inch, y_position, f"${invoice_data['late_fee']:.2f}")
        c.drawString(7.2 * inch, y_position, f"${invoice_data['late_fee']:.2f}")

    # --- Total ---
    c.line(width - 4 * inch, height - 8 * inch, width - 1 * inch, height - 8 * inch)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(width - 3.9 * inch, height - 8.2 * inch, "TOTAL PAGADO:")
    c.drawString(
        width - 2 * inch, height - 8.2 * inch, f"${invoice_data['amount_paid']:.2f}"
    )

    # --- Pie de página ---
    c.setFont("Helvetica-Oblique", 9)
    c.drawCentredString(width / 2, 0.75 * inch, "Gracias por su pago.")

    c.save()
    # Devuelve la ruta relativa completa para que la BD la guarde.
    return file_name
