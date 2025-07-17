import os
import datetime
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML, CSS

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
