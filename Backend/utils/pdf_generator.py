# Backend/utils/pdf_generator.py
import datetime
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML, CSS
from sqlalchemy.orm import Session
from models.models import Payment, Invoice, BusinessSettings, UserDetail, InternetPlan

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
    """Crea un archivo PDF usando un nombre de archivo personalizado y seguro."""
    env = Environment(loader=FileSystemLoader(TEMPLATES_DIR), autoescape=True)
    template = env.get_template("invoice.html")
    html_string = template.render(**invoice_data)

    now = datetime.datetime.now()
    output_dir = INVOICES_DIR / str(now.year) / f"{now.month:02d}"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Usamos directamente el nombre de archivo seguro que nos pasan
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
    """Prepara los datos y llama a la creación del PDF con el nombre de archivo personalizado."""
    user_details = invoice.user.userdetail
    plan_details = invoice.subscription.plan
    settings_from_db = db.query(BusinessSettings).all()
    company_settings = {s.setting_name: s.setting_value for s in settings_from_db}

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

    pdf_data = {
        "logo_path": get_logo_path(),
        "company_name": company_settings.get("BUSINESS_NAME", "Nombre de Empresa"),
        "company_address": company_settings.get("BUSINESS_ADDRESS", "Dirección"),
        "company_city": company_settings.get("BUSINESS_CITY", "Ciudad"),
        "company_dni": company_settings.get("BUSINESS_CUIT", "CUIT de Empresa"),
        "company_contact": f"Whatsapp: {company_settings.get('BUSINESS_PHONE', '')}",
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
