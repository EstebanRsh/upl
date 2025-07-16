import os
import datetime
from jinja2 import Environment, FileSystemLoader
from xhtml2pdf import pisa
import io

# ✨ Importaciones actualizadas para una construcción de URL más robusta ✨
import urllib.parse
import urllib.request


# Carpeta de plantillas
TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "..", "templates")


def create_invoice_pdf(invoice_data: dict, logo_path: str = "logo.png") -> str:
    # Directorio de salida para las facturas
    now = datetime.datetime.now()
    year = str(now.year)
    month = f"{now.month:02d}"
    out_dir = os.path.join("facturas", year, month)
    os.makedirs(out_dir, exist_ok=True)

    filename = f"recibo_{invoice_data['invoice_id']}.pdf"
    full_path = os.path.join(out_dir, filename)

    # Configurar Jinja2 para cargar plantillas desde TEMPLATES_DIR
    env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))
    template = env.get_template("invoice.html")

    # Renderizar el HTML con los datos de la factura
    html = template.render(**invoice_data, logo_path=logo_path)

    # Crear el PDF usando xhtml2pdf
    source_html = io.BytesIO(html.encode("utf-8"))
    result_file = open(full_path, "wb")

    # ✨ Construcción de la base_url más robusta y multiplataforma ✨
    # Obtener la ruta absoluta del directorio de plantillas
    absolute_templates_path = os.path.abspath(TEMPLATES_DIR)
    # Convertir la ruta a un formato de URL 'file://'
    # os.sep añade la barra correcta para el sistema operativo
    base_url = urllib.parse.urljoin(
        "file:", urllib.request.pathname2url(absolute_templates_path + os.sep)
    )

    try:
        pisa_status = pisa.CreatePDF(
            source_html,  # el HTML a convertir
            dest=result_file,  # el manejador de archivo donde se escribirá el PDF
            base_url=base_url,  # ✨ ¡La URL base es CRUCIAL para que encuentre el CSS y las imágenes! ✨
            show_error_as_pdf=True,  # ✨ Esto generará un PDF con errores si los hay, muy útil para depurar ✨
        )

    finally:
        result_file.close()

    if pisa_status.err:
        print(f"Error al crear el PDF con xhtml2pdf: {pisa_status.err}")
        # Si show_error_as_pdf=True, el PDF generado contendrá los errores
        # No es estrictamente necesario lanzar una excepción aquí, pero lo mantendremos por si acaso
        raise Exception(
            "Error al crear el PDF con xhtml2pdf. Revisa el PDF generado para detalles."
        )

    return filename
