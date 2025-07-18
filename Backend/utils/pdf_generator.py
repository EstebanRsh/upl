import os
import datetime
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML, CSS
from models.models import Payment, Invoice

# Carpeta de plantillas
TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "..", "templates")


def create_invoice_pdf(invoice_data: dict) -> str:
    """
    Crea un PDF a partir de datos usando WeasyPrint, que soporta CSS moderno.
    Formateo mejorado para coincidir con el recibo de referencia.
    """
    # 1. Definir la ruta de salida
    now = datetime.datetime.now()
    out_dir = os.path.join("facturas", str(now.year), f"{now.month:02d}")
    os.makedirs(out_dir, exist_ok=True)

    # Generar nombre del archivo basado en cliente y fecha
    client_name = invoice_data.get("client_name", "Cliente").replace(" ", "_")
    filename = f"Recibo_{client_name}_f{invoice_data['invoice_id']}.pdf"
    full_path = os.path.join(out_dir, filename)

    # 2. Verificar y preparar la ruta del logo
    logo_path = invoice_data.get("logo_path")
    if logo_path and os.path.exists(logo_path):
        # Convertir a URL relativa para WeasyPrint
        logo_url = f"file://{os.path.abspath(logo_path)}"
        invoice_data["logo_path"] = logo_url
    else:
        # Buscar el logo en diferentes formatos
        logo_formats = ["logo.png", "logo.jpg", "logo.jpeg", "logo.svg"]
        templates_dir = os.path.abspath(TEMPLATES_DIR)

        for logo_name in logo_formats:
            logo_full_path = os.path.join(templates_dir, logo_name)
            if os.path.exists(logo_full_path):
                invoice_data["logo_path"] = f"file://{logo_full_path}"
                break
        else:
            invoice_data["logo_path"] = None
            print("Advertencia: No se encontró el logo de la empresa")

    # 3. Cargar y renderizar la plantilla HTML
    env = Environment(loader=FileSystemLoader(TEMPLATES_DIR), autoescape=True)
    template = env.get_template("invoice.html")
    html_string = template.render(**invoice_data)

    # 4. Configurar CSS adicional para mejorar el formato
    css_string = """
    @page {
        size: A4;
        margin: 0;
    }
    
    body {
        font-family: "Arial", "Helvetica", sans-serif;
        -webkit-print-color-adjust: exact;
        print-color-adjust: exact;
    }
    
    .receipt-wrapper {
        page-break-inside: avoid;
    }
    
    .items-table {
        page-break-inside: avoid;
    }
    
    .totals-section {
        page-break-inside: avoid;
    }
    
    .logo {
        max-width: 100px;
        height: auto;
        display: block;
    }
    """

    # 5. Generar PDF con WeasyPrint
    base_url = f"file://{os.path.abspath(os.path.join(TEMPLATES_DIR, os.pardir))}"

    html = HTML(string=html_string, base_url=base_url)
    css = CSS(string=css_string)

    html.write_pdf(full_path, stylesheets=[css])

    return filename


def format_spanish_date(date_obj):
    """
    Formatea una fecha al formato español DD/MM/YYYY
    """
    if isinstance(date_obj, datetime.datetime):
        return date_obj.strftime("%d/%m/%Y")
    return date_obj


def format_currency(amount):
    """
    Formatea un número como moneda española
    """
    return f"{amount:.2f} €"


def generate_receipt_number(payment_id, year):
    """
    Genera un número de recibo con el formato F2025-XXX
    """
    return f"F{year}-{payment_id:03d}"


def generate_payment_receipt(payment: Payment, invoice: Invoice) -> str:
    """
    Prepara los datos, genera el PDF para un recibo de pago y devuelve la URL del archivo.

    Args:
        payment: El objeto Payment recién creado.
        invoice: La factura que se ha pagado.

    Returns:
        La ruta relativa del archivo PDF generado.
    """
    # 1. Preparar los datos para el PDF
    user_details = invoice.user.userdetail
    plan_details = invoice.subscription.plan

    # Formatear el mes del servicio en español
    meses = {
        1: "Enero",
        2: "Febrero",
        3: "Marzo",
        4: "Abril",
        5: "Mayo",
        6: "Junio",
        7: "Julio",
        8: "Agosto",
        9: "Septiembre",
        10: "Octubre",
        11: "Noviembre",
        12: "Diciembre",
    }
    mes_servicio = f"{meses[invoice.issue_date.month]} {invoice.issue_date.year}"

    # Obtener la ruta absoluta del logo
    logo_formats = ["logo.png", "logo.jpg", "logo.jpeg"]
    logo_path = None
    for logo_name in logo_formats:
        potential_path = os.path.abspath(os.path.join("templates", logo_name))
        if os.path.exists(potential_path):
            logo_path = potential_path
            break
    if not logo_path:
        print(
            "Advertencia: No se encontró el logo de la empresa en la carpeta templates/"
        )

    # Formatear el número de recibo
    receipt_number = f"F{payment.payment_date.year}-{invoice.id:03d}"

    pdf_data = {
        "company_name": "NetSys Solutions",
        "company_address": "Calle Ficticia 123, Ciudad Ejemplo",
        "company_contact": "Tel: 900 123 456 | Email: contacto@netsys.com",
        "logo_path": logo_path,
        "client_name": f"{user_details.firstname} {user_details.lastname}",
        "client_dni": user_details.dni,
        "client_address": user_details.address,
        "client_barrio": user_details.barrio,
        "client_city": user_details.city,
        "client_phone": user_details.phone,
        "client_email": invoice.user.email,
        "receipt_number": receipt_number,
        "payment_date": payment.payment_date.strftime("%d/%m/%Y"),
        "due_date": invoice.due_date.strftime("%d/%m/%Y"),
        "item_description": f"Servicio Internet Premium Fibra {plan_details.speed_mbps}MB - {mes_servicio}",
        "base_amount": invoice.base_amount,
        "late_fee": invoice.late_fee,
        "total_paid": payment.amount,
        "invoice_id": invoice.id,
    }

    # 2. Llamar a la función que crea el PDF
    pdf_filename = create_invoice_pdf(pdf_data)

    # 3. Construir y devolver la URL del recibo
    receipt_url = os.path.join(
        str(payment.payment_date.year),
        f"{payment.payment_date.month:02d}",
        pdf_filename,
    ).replace("\\", "/")

    return receipt_url
