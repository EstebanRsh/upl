# routes/billing_routes.py
import logging
import datetime
import os
import math
from fastapi import APIRouter, Depends, HTTPException, status, Query, Header
from fastapi.responses import FileResponse
from sqlalchemy import extract
from sqlalchemy.orm import Session
from models.models import (
    BusinessSettings,
    Setting,
    Subscription,
    Invoice,
    InvoiceOut,
    PaginatedResponse,
)
from auth.security import Security
from config.db import get_db

logger = logging.getLogger(__name__)
billing_router = APIRouter()


# --- Dependencia de Seguridad Simplificada ---
def verify_admin_permission(authorization: str = Header(...)):
    """
    Verifica que el token en la cabecera pertenezca a un administrador.
    """
    token_data = Security.verify_token({"authorization": authorization})
    if not token_data.get("success") or token_data.get("role") != "administrador":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos de administrador para realizar esta acción.",
        )
    return token_data


# --- Lógica de negocio y tareas programadas (sin cambios) ---
def generate_monthly_invoices_logic(db: Session):
    logger.info("Iniciando la lógica de generación de facturas mensuales.")
    automation_setting = (
        db.query(BusinessSettings)
        .filter_by(setting_name="auto_invoicing_enabled")
        .first()
    )
    if automation_setting and automation_setting.setting_value.lower() != "true":
        logger.info(
            "La generación automática de facturas está desactivada. Omitiendo tarea."
        )
        return {
            "message": "Proceso omitido. La facturación automática está desactivada.",
            "facturas_generadas": 0,
            "facturas_omitidas": 0,
        }

    payment_window_setting = (
        db.query(BusinessSettings).filter_by(setting_name="payment_window_days").first()
    )
    if not payment_window_setting:
        logger.error("La regla 'payment_window_days' no está configurada.")
        return {"error": "La regla 'payment_window_days' no está configurada."}

    payment_window_days = int(payment_window_setting.setting_value)
    active_subscriptions = db.query(Subscription).filter_by(status="active").all()
    generated_count, skipped_count = 0, 0
    today = datetime.date.today()

    for sub in active_subscriptions:
        if (
            db.query(Invoice)
            .filter(
                Invoice.subscription_id == sub.id,
                extract("month", Invoice.issue_date) == today.month,
                extract("year", Invoice.issue_date) == today.year,
            )
            .first()
        ):
            skipped_count += 1
            continue

        new_invoice = Invoice(
            user_id=sub.user_id,
            subscription_id=sub.id,
            due_date=today + datetime.timedelta(days=payment_window_days),
            base_amount=sub.plan.price,
            total_amount=sub.plan.price,
        )
        db.add(new_invoice)
        generated_count += 1

    db.commit()
    logger.info(
        f"Facturación completada. Generadas: {generated_count}, Omitidas: {skipped_count}."
    )
    return {
        "message": "Proceso completado.",
        "facturas_generadas": generated_count,
        "facturas_omitidas_por_duplicado": skipped_count,
    }


def generate_monthly_invoices_job(db: Session):
    logger.info("Ejecutando TAREA PROGRAMADA: Generación de facturas mensuales.")
    try:
        generate_monthly_invoices_logic(db)
    except Exception as e:
        logger.error(f"Error en la tarea programada de facturación: {e}", exc_info=True)
    finally:
        db.close()
    logger.info("Tarea programada de facturación finalizada.")


# --- Rutas de la API ---


@billing_router.post(
    "/admin/invoices/generate-monthly",
    summary="Generar facturas mensuales manualmente",
    dependencies=[Depends(verify_admin_permission)],
    tags=["Admin"],
)
def generate_monthly_invoices_manual(db: Session = Depends(get_db)):
    logger.info("Invocación MANUAL de la generación de facturas.")
    result = generate_monthly_invoices_logic(db)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@billing_router.get("/invoices/{invoice_id}/download", tags=["Facturación"])
def download_invoice_pdf(
    invoice_id: int,
    authorization: str = Header(...),
    db: Session = Depends(get_db),
):
    token_data = Security.verify_token({"authorization": authorization})
    if not token_data.get("success"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=token_data.get("message")
        )

    requesting_user_id = token_data.get("user_id")
    requesting_user_role = token_data.get("role")

    logger.info(
        f"Usuario ID {requesting_user_id} solicitando descarga de factura ID: {invoice_id}."
    )

    invoice = db.query(Invoice).filter_by(id=invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Factura no encontrada")

    # Un usuario puede ver su propia factura, o un admin puede ver cualquiera.
    if (
        requesting_user_role != "administrador"
        and requesting_user_id != invoice.user_id
    ):
        raise HTTPException(
            status_code=403, detail="No tienes permiso para descargar esta factura."
        )

    if not invoice.receipt_pdf_url:
        raise HTTPException(
            status_code=404, detail="La factura no tiene un recibo PDF asociado."
        )

    full_file_path = (
        invoice.receipt_pdf_url
    )  # Asumiendo que ahora se guarda la ruta completa
    if not os.path.exists(full_file_path):
        logger.error(f"El archivo PDF no fue encontrado en la ruta: {full_file_path}")
        raise HTTPException(
            status_code=404,
            detail="El archivo PDF del recibo no se encontró en el servidor.",
        )

    return FileResponse(
        path=full_file_path,
        media_type="application/pdf",
        filename=os.path.basename(full_file_path),
    )


@billing_router.post(
    "/admin/invoices/process-overdue",
    dependencies=[Depends(verify_admin_permission)],
    tags=["Admin"],
)
def process_overdue_invoices(db: Session = Depends(get_db)):
    logger.info("Iniciando el procesamiento de facturas vencidas.")
    late_fee_setting = (
        db.query(BusinessSettings).filter_by(setting_name="late_fee_amount").first()
    )
    suspension_days_setting = (
        db.query(BusinessSettings).filter_by(setting_name="days_for_suspension").first()
    )

    if not late_fee_setting or not suspension_days_setting:
        raise HTTPException(
            status_code=400, detail="Faltan reglas de negocio para procesar vencidas."
        )

    late_fee = float(late_fee_setting.setting_value)
    days_for_suspension = int(suspension_days_setting.setting_value)
    today = datetime.date.today()
    overdue_invoices = (
        db.query(Invoice)
        .filter(Invoice.status == "pending", Invoice.due_date < today)
        .all()
    )

    processed_count, suspended_count = 0, 0
    for invoice in overdue_invoices:
        if invoice.late_fee == 0.0:
            invoice.late_fee = late_fee
            invoice.total_amount += late_fee
            processed_count += 1
        if (
            today - invoice.due_date.date()
        ).days >= days_for_suspension and invoice.subscription.status == "active":
            invoice.subscription.status = "suspended"
            suspended_count += 1
    db.commit()
    return {
        "message": "Proceso de vencidas completado.",
        "facturas_con_recargo": processed_count,
        "servicios_suspendidos": suspended_count,
    }


@billing_router.get(
    "/users/me/invoices", response_model=PaginatedResponse[InvoiceOut], tags=["Cliente"]
)
def get_my_invoices(
    authorization: str = Header(...),
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    month: int = Query(None, ge=1, le=12),
    year: int = Query(None, ge=2020),
    db: Session = Depends(get_db),
):
    token_data = Security.verify_token({"authorization": authorization})
    if not token_data.get("success"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=token_data.get("message")
        )

    user_id = token_data.get("user_id")
    logger.info(f"Usuario ID {user_id} solicitando sus facturas.")

    query = (
        db.query(Invoice).filter_by(user_id=user_id).order_by(Invoice.issue_date.desc())
    )
    if month:
        query = query.filter(extract("month", Invoice.issue_date) == month)
    if year:
        query = query.filter(extract("year", Invoice.issue_date) == year)

    total_items = query.count()
    invoices = query.offset((page - 1) * size).limit(size).all()

    return PaginatedResponse(
        total_items=total_items,
        total_pages=math.ceil(total_items / size),
        current_page=page,
        items=invoices,
    )
