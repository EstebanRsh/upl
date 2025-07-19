# services/payment_service.py
import logging
import os
from sqlalchemy.orm import Session, joinedload
from models.models import Payment, User, Invoice, Subscription, InputPayment
from utils.pdf_generator import generate_payment_receipt

# Obtenemos el logger para registrar eventos de este servicio
logger = logging.getLogger(__name__)


class PaymentException(Exception):
    """Excepción personalizada para errores de lógica de negocio en pagos."""

    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


def process_new_payment(payment_data: InputPayment, db: Session) -> dict:
    """
    Servicio para procesar un nuevo pago.
    Contiene toda la lógica de negocio para registrar un pago y actualizar la factura.
    """
    logger.info(
        f"Iniciando procesamiento de pago para usuario ID: {payment_data.user_id}."
    )

    # 1. Buscar la suscripción correcta
    subscription = (
        db.query(Subscription)
        .filter(
            Subscription.user_id == payment_data.user_id,
            Subscription.plan_id == payment_data.plan_id,
        )
        .first()
    )
    if not subscription:
        logger.warning(
            f"No se encontró suscripción para usuario {payment_data.user_id} y plan {payment_data.plan_id}."
        )
        raise PaymentException(
            "No se encontró una suscripción para este usuario y plan.", 404
        )

    # 2. Buscar la factura pendiente más antigua asociada a esa suscripción
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
        logger.warning(
            f"No se encontró factura pendiente para la suscripción ID: {subscription.id}."
        )
        raise PaymentException(
            "No se encontró una factura pendiente para esta suscripción.", 404
        )

    logger.info(f"Factura ID {invoice_to_pay.id} encontrada para registrar el pago.")

    # 3. Actualizar factura, crear el registro del pago y generar el PDF
    invoice_to_pay.status = "paid"
    new_payment = Payment(
        user_id=payment_data.user_id,
        amount=payment_data.amount,
        invoice_id=invoice_to_pay.id,
    )
    db.add(new_payment)
    db.flush()  # Sincroniza la sesión para obtener el ID del nuevo pago
    db.refresh(new_payment)
    logger.info(f"Pago ID {new_payment.id} creado en la sesión de la base de datos.")

    receipt_url = generate_payment_receipt(new_payment, invoice_to_pay, db)
    invoice_to_pay.receipt_pdf_url = receipt_url
    logger.info(f"Recibo PDF generado y URL guardada: {receipt_url}")

    # 4. Devolver un diccionario con el resultado para la respuesta final
    return {
        "message": "Pago registrado exitosamente.",
        "receipt_number": f"F{new_payment.payment_date.year}-{invoice_to_pay.id:03d}",
        "pdf_filename": os.path.basename(receipt_url),
        "total_paid": new_payment.amount,
    }
