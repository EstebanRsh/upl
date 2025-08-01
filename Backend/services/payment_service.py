# services/payment_service.py
import logging
import os
import re
from sqlalchemy.orm import Session, joinedload
from models.models import (
    Payment,
    User,
    Invoice,
    Subscription,
    InputPayment,
    InputPaymentAdmin,
)
from utils.pdf_generator import generate_payment_receipt

logger = logging.getLogger(__name__)


class PaymentException(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


def sanitize_name(name: str) -> str:
    if not name:
        return ""
    name = name.lower()
    name = re.sub(r"[áäâà]", "a", name)
    name = re.sub(r"[éëêè]", "e", name)
    name = re.sub(r"[íïîì]", "i", name)
    name = re.sub(r"[óöôò]", "o", name)
    name = re.sub(r"[úüûù]", "u", name)
    name = re.sub(r"[ñ]", "n", name)
    name = re.sub(r"[^a-z0-9]", "", name)
    return name.capitalize()


# --- FUNCIÓN ORIGINAL (RESTAURADA) PARA EL CLIENTE ---
def process_new_payment(payment_data: InputPayment, db: Session) -> dict:
    """
    Servicio para procesar un nuevo pago iniciado por un cliente.
    """
    logger.info(
        f"Iniciando procesamiento de pago para usuario ID: {payment_data.user_id}."
    )

    subscription = (
        db.query(Subscription)
        .filter(
            Subscription.user_id == payment_data.user_id,
            Subscription.plan_id == payment_data.plan_id,
        )
        .first()
    )
    if not subscription:
        raise PaymentException(
            "No se encontró una suscripción para este usuario y plan.", 404
        )

    invoice_to_pay = (
        db.query(Invoice)
        .filter(Invoice.subscription_id == subscription.id, Invoice.status == "pending")
        .options(
            joinedload(Invoice.user).joinedload(User.userdetail),
            joinedload(Invoice.subscription).joinedload(Subscription.plan),
        )
        .order_by(Invoice.issue_date)
        .first()
    )

    if not invoice_to_pay:
        raise PaymentException(
            "No se encontró una factura pendiente para esta suscripción.", 404
        )

    logger.info(f"Factura ID {invoice_to_pay.id} encontrada para registrar el pago.")
    invoice_to_pay.status = "paid"
    new_payment = Payment(
        user_id=payment_data.user_id,
        amount=payment_data.amount,
        invoice_id=invoice_to_pay.id,
    )
    db.add(new_payment)
    db.flush()
    db.refresh(new_payment)

    # ... (Lógica de generación de PDF idéntica a la que ya tenías)
    user_details = invoice_to_pay.user.userdetail
    payment_date_str = new_payment.payment_date.strftime("%Y-%m-%d")
    clean_lastname = sanitize_name(user_details.lastname)
    clean_firstname = sanitize_name(user_details.firstname)
    pdf_filename = f"{payment_date_str}_F{invoice_to_pay.id}_C{invoice_to_pay.user_id}_{clean_lastname}{clean_firstname}.pdf"

    full_receipt_path = generate_payment_receipt(
        payment=new_payment, invoice=invoice_to_pay, db=db, custom_filename=pdf_filename
    )
    relative_path = os.path.relpath(full_receipt_path, "facturas").replace("\\", "/")
    invoice_to_pay.receipt_pdf_url = relative_path

    db.commit()

    return {
        "message": "Pago registrado exitosamente.",
        "receipt_number": f"F{new_payment.payment_date.year}-{invoice_to_pay.id:03d}",
        "pdf_filename": os.path.basename(full_receipt_path),
        "total_paid": new_payment.amount,
    }


# --- NUEVA FUNCIÓN PARA EL ADMINISTRADOR ---
def process_new_payment_admin(payment_data: InputPaymentAdmin, db: Session) -> dict:
    """
    Servicio para procesar un nuevo pago registrado por un administrador.
    """
    logger.info(
        f"Iniciando procesamiento de pago manual para factura ID: {payment_data.invoice_id}."
    )

    invoice_to_pay = (
        db.query(Invoice)
        .filter(Invoice.id == payment_data.invoice_id)
        .options(
            joinedload(Invoice.user).joinedload(User.userdetail),
            joinedload(Invoice.subscription).joinedload(Subscription.plan),
        )
        .first()
    )
    if not invoice_to_pay:
        raise PaymentException("No se encontró la factura especificada.", 404)
    if invoice_to_pay.status == "Pagado":
        raise PaymentException("Esta factura ya ha sido pagada.", 400)

    invoice_to_pay.status = "Pagado"
    if payment_data.receipt_url:
        invoice_to_pay.receipt_pdf_url = payment_data.receipt_url

    new_payment = Payment(
        user_id=invoice_to_pay.user_id,
        amount=payment_data.amount,
        invoice_id=invoice_to_pay.id,
        payment_date=payment_data.payment_date,
        payment_method=payment_data.payment_method,
    )
    db.add(new_payment)
    db.flush()
    db.refresh(new_payment)

    if payment_data.payment_method.lower() == "efectivo":
        user_details = invoice_to_pay.user.userdetail
        payment_date_str = new_payment.payment_date.strftime("%Y-%m-%d")
        clean_lastname = sanitize_name(user_details.lastname)
        clean_firstname = sanitize_name(user_details.firstname)
        pdf_filename = f"{payment_date_str}_F{invoice_to_pay.id}_C{invoice_to_pay.user_id}_{clean_lastname}{clean_firstname}.pdf"

        full_receipt_path = generate_payment_receipt(
            payment=new_payment,
            invoice=invoice_to_pay,
            db=db,
            custom_filename=pdf_filename,
        )
        relative_path = os.path.relpath(full_receipt_path, "facturas").replace(
            "\\", "/"
        )
        invoice_to_pay.receipt_pdf_url = relative_path

    db.commit()

    return {
        "message": "Pago registrado exitosamente.",
        "payment_id": new_payment.id,
        "invoice_id": invoice_to_pay.id,
        "new_status": "Pagado",
    }
