# Backend/utils/pdf_generator.py
import datetime
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML, CSS
from sqlalchemy.orm import Session

# --- ¡IMPORTACIONES CORREGIDAS! ---
# Se elimina BusinessSettings y se añade CompanySettings
from models.models import Payment, Invoice, CompanySettings, UserDetail

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
INVOICES_DIR = Path("facturas")


def get_logo_path():
    for ext in ["png", "jpg", "jpeg", "svg"]:
        logo_path = TEMPLATES_DIR / f"logo.{ext}"
        if logo_path.exists():
            return logo_path.as_uri()
    print("Advertencia: No se encontró el logo en la carpeta 'templates'.")
    return None


def create_invoice_pdf(invoice_data: dict, custom_filename: str) -> str:
    """
    Crea un archivo PDF usando un nombre de archivo personalizado y seguro.
    ESTA FUNCIÓN NO SE MODIFICA PARA CONSERVAR EL DISEÑO.
    """
    env = Environment(loader=FileSystemLoader(TEMPLATES_DIR), autoescape=True)
    template = env.get_template("invoice.html")
    html_string = template.render(**invoice_data)

    now = datetime.datetime.now()
    output_dir = INVOICES_DIR / str(now.year) / f"{now.month:02d}"
    output_dir.mkdir(parents=True, exist_ok=True)

    full_path = output_dir / custom_filename

    css_path = TEMPLATES_DIR / "style.css"
    if not css_path.exists():
        raise FileNotFoundError(
            f"El archivo 'style.css' no se encuentra en: {css_path}"
        )

    html_doc = HTML(string=html_string, base_url=TEMPLATES_DIR.as_uri())
    html_doc.write_pdf(full_path, stylesheets=[CSS(css_path)])

    print(f"Factura generada exitosamente en: {full_path}")
    return str(full_path.as_posix())


def generate_payment_receipt(
    payment: Payment, invoice: Invoice, db: Session, custom_filename: str
) -> str:
    """
    Prepara los datos y llama a la creación del PDF con el nombre de archivo personalizado.
    """
    user_details = invoice.user.userdetail
    plan_details = invoice.subscription.plan

    # --- ¡LÓGICA CORREGIDA Y SIMPLIFICADA! ---
    # Se busca la única fila de configuración en la nueva tabla.
    settings = db.query(CompanySettings).first()
    if not settings:
        raise ValueError(
            "La configuración de la empresa (CompanySettings) no ha sido inicializada en la base de datos."
        )

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

    # Se usan los campos directamente del objeto 'settings', de forma segura.
    pdf_data = {
        "logo_path": get_logo_path(),
        "company_name": settings.business_name,
        "company_address": settings.business_address,
        "company_city": "",  # Este campo ya no existe, se puede añadir si lo necesitas
        "company_dni": settings.business_cuit,
        "company_contact": "",  # Este campo tampoco existe, puedes añadirlo al modelo si quieres
        "client_name": f"{user_details.firstname} {user_details.lastname}",
        "client_dni": user_details.dni,
        "client_address": user_details.address,
        "client_barrio": user_details.barrio,
        "client_city": user_details.city,
        "client_phone": user_details.phone,
        "receipt_number": receipt_number,
        "payment_date": payment.payment_date.strftime("%d/%m/%Y"),
        "due_date": invoice.due_date.strftime("%d/%m/%Y"),
        "item_description": f"Servicio Internet {plan_details.speed_mbps}MB - {mes_servicio}",
        "base_amount": invoice.base_amount,
        "late_fee": invoice.late_fee,
        "total_paid": payment.amount,
        "invoice_id": invoice.id,
    }

    pdf_file_path = create_invoice_pdf(pdf_data, custom_filename=custom_filename)
    return pdf_file_path
