import datetime
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML, CSS
from models.models import (
    Payment,
    Invoice,
)  # Asegúrate que la importación a tus modelos sea correcta

# --- CONSTANTES DE CONFIGURACIÓN ---

# Path() crea un objeto de ruta. __file__ es la ruta de este archivo (pdf_generator.py).
# .parent se mueve un nivel hacia arriba en el directorio.
# Usamos .parent.parent para llegar desde /utils/ hasta la carpeta /Backend/
# Luego, apuntamos a la carpeta 'templates'.
TEMPLATES_DIR = Path(__file__).parent.parent / "templates"

# Directorio base donde se guardarán todas las facturas generadas.
INVOICES_DIR = Path("facturas")


# --- FUNCIONES AUXILIARES ---


def get_logo_path():
    """
    Busca el logo en la carpeta de plantillas y devuelve su ruta como una URL de archivo.
    WeasyPrint necesita una URL (ej: 'file:///path/to/logo.png') para encontrar la imagen.
    """
    # Itera sobre las extensiones de imagen más comunes.
    for ext in ["png", "jpg", "jpeg", "svg"]:
        logo_path = TEMPLATES_DIR / f"logo.{ext}"
        if logo_path.exists():
            # .as_uri() convierte la ruta del sistema de archivos a una URI, ej: "file:///..."
            return logo_path.as_uri()
    print(
        "Advertencia: No se encontró el logo (logo.png, logo.jpg, etc.) en la carpeta 'templates'."
    )
    return None


def create_invoice_pdf(invoice_data: dict) -> str:
    """
    Crea un archivo PDF a partir de datos y una plantilla HTML.

    Esta función renderiza el HTML, lo combina con una hoja de estilos CSS externa
    y genera un archivo PDF usando WeasyPrint.

    Args:
        invoice_data: Un diccionario con todos los datos necesarios para la plantilla.

    Returns:
        La ruta relativa del archivo PDF generado, como un string.
    """
    # 1. Configurar Jinja2 para cargar la plantilla desde el directorio 'templates'.
    env = Environment(loader=FileSystemLoader(TEMPLATES_DIR), autoescape=True)
    template = env.get_template("invoice.html")

    # 2. Renderizar la plantilla HTML con los datos proporcionados.
    html_string = template.render(**invoice_data)

    # 3. Crear la ruta de salida para el PDF (ej: facturas/2024/07/Recibo_...).
    now = datetime.datetime.now()
    output_dir = INVOICES_DIR / str(now.year) / f"{now.month:02d}"
    output_dir.mkdir(parents=True, exist_ok=True)  # Crea los directorios si no existen.

    # Limpia el nombre del cliente para usarlo en el nombre del archivo.
    client_name_safe = invoice_data.get("client_name", "Cliente").replace(" ", "_")
    filename = f"Recibo_{client_name_safe}_f{invoice_data['invoice_id']}.pdf"
    full_path = output_dir / filename

    # 4. Cargar la hoja de estilos CSS externa.
    css_path = TEMPLATES_DIR / "style.css"
    if not css_path.exists():
        raise FileNotFoundError(
            f"El archivo 'style.css' no se encuentra en la ruta: {css_path}"
        )

    # 5. Generar el PDF con WeasyPrint.
    # El 'base_url' es el paso CRÍTICO: le dice a WeasyPrint desde dónde resolver las
    # rutas relativas como las del CSS enlazado o las imágenes en el HTML.
    html_doc = HTML(string=html_string, base_url=TEMPLATES_DIR.as_uri())

    # Escribimos el PDF en el disco, aplicando los estilos del archivo CSS.
    html_doc.write_pdf(full_path, stylesheets=[CSS(css_path)])

    print(f"Factura generada exitosamente en: {full_path}")

    # Devolvemos la ruta relativa del archivo (ej: 'facturas/2024/07/archivo.pdf')
    # para que pueda ser guardada en la base de datos. .as_posix() asegura
    # que se usen barras '/' en la ruta, lo cual es estándar para URLs.
    return str(full_path.as_posix())


def generate_payment_receipt(payment: Payment, invoice: Invoice) -> str:
    """
    Prepara los datos de un pago y una factura, y llama a la función de creación de PDF.

    Args:
        payment: El objeto de SQLAlchemy del Pago.
        invoice: El objeto de SQLAlchemy de la Factura.

    Returns:
        La ruta relativa del archivo PDF generado.
    """
    user_details = invoice.user.userdetail
    plan_details = invoice.subscription.plan

    # Diccionario para traducir el número del mes a su nombre en español.
    meses_es = {
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
    mes_servicio = (
        f"{meses_es.get(invoice.issue_date.month, '')} {invoice.issue_date.year}"
    )
    receipt_number = f"F{payment.payment_date.year}-{invoice.id:03d}"

    # Preparamos el diccionario de datos para pasarlo a la plantilla Jinja2.
    pdf_data = {
        "logo_path": get_logo_path(),
        "company_name": "NetSys Solutions",  # Puedes mover esto a un archivo de config.
        "company_address": "Calle Ficticia 123, Ciudad Ejemplo",
        "company_contact": "Tel: 900 123 456 | Email: contacto@netsys.com",
        "client_name": f"{user_details.firstname} {user_details.lastname}",
        "client_address": user_details.address,
        "client_email": invoice.user.email,
        "receipt_number": receipt_number,
        "payment_date": payment.payment_date.strftime("%d/%m/%Y"),
        "due_date": invoice.due_date.strftime("%d/%m/%Y"),
        "item_description": f"Servicio Internet Fibra {plan_details.speed_mbps}MB - {mes_servicio}",
        "base_amount": invoice.base_amount,
        "late_fee": invoice.late_fee,
        "total_paid": payment.amount,
        "invoice_id": invoice.id,
    }

    # Llamamos a la función principal que crea el PDF.
    pdf_file_path = create_invoice_pdf(pdf_data)

    return pdf_file_path
