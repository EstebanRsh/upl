# routes/billing_routes.py
# -----------------------------------------------------------------------------
# RUTAS DE FACTURACIÓN Y REGLAS DE NEGOCIO
# -----------------------------------------------------------------------------
import logging
import datetime
import os
import math
from fastapi import APIRouter, Depends, HTTPException, status, Query
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
from auth.security import has_permission, get_current_user
from config.db import get_db

logger = logging.getLogger(__name__)
billing_router = APIRouter()

# -----------------------------------------------------------------------------
# LÓGICA DE NEGOCIO (Separada para poder reutilizarla)
# -----------------------------------------------------------------------------


def generate_monthly_invoices_logic(db: Session):
    """
    Contiene la lógica principal para generar facturas.
    Puede ser llamada por un job automático o un endpoint manual.
    """
    logger.info("Iniciando la lógica de generación de facturas mensuales.")

    # 1. Comprobar si la automatización está activada
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

    # 2. Lógica de generación de facturas
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


# -----------------------------------------------------------------------------
# TAREA y ENDPOINTS
# -----------------------------------------------------------------------------


def generate_monthly_invoices_job(db: Session):
    """
    Esta es la función que el scheduler de app.py llamará.
    """
    logger.info("Ejecutando TAREA PROGRAMADA: Generación de facturas mensuales.")
    try:
        generate_monthly_invoices_logic(db)
    except Exception as e:
        logger.error(f"Error en la tarea programada de facturación: {e}", exc_info=True)
    finally:
        db.close()
    logger.info("Tarea programada de facturación finalizada.")


@billing_router.post(
    "/admin/invoices/generate-monthly",
    summary="Generar facturas mensuales manualmente",
    dependencies=[Depends(has_permission("billing:generate_invoices"))],
)
def generate_monthly_invoices_manual(db: Session = Depends(get_db)):
    """
    Endpoint para que un administrador ejecute la facturación manualmente.
    """
    logger.info("Invocación MANUAL de la generación de facturas.")
    result = generate_monthly_invoices_logic(db)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@billing_router.post(
    "/admin/settings/set", dependencies=[Depends(has_permission("roles:manage"))]
)
def set_business_setting(setting_data: Setting, db: Session = Depends(get_db)):
    logger.info(f"Estableciendo regla de negocio: '{setting_data.setting_name}'.")
    try:
        setting = (
            db.query(BusinessSettings)
            .filter_by(setting_name=setting_data.setting_name)
            .first()
        )
        if setting:
            setting.setting_value = setting_data.setting_value
            setting.description = setting_data.description
        else:
            db.add(BusinessSettings(**setting_data.model_dump()))
        db.commit()
        return {"message": f"Configuración '{setting_data.setting_name}' guardada."}
    except Exception as e:
        db.rollback()
        logger.error(f"Error en set_business_setting: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno del servidor.")


@billing_router.get("/invoices/{invoice_id}/download")
def download_invoice_pdf(
    invoice_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    logger.info(
        f"Usuario '{current_user.get('sub')}' solicitando descarga de factura ID: {invoice_id}."
    )
    try:
        invoice = db.query(Invoice).filter_by(id=invoice_id).first()
        if not invoice:
            raise HTTPException(status_code=404, detail="Factura no encontrada")

        user_has_permission = (
            "users:read_all" in current_user.get("permissions", set())
            or current_user.get("user_id") == invoice.user_id
        )
        if not user_has_permission:
            raise HTTPException(
                status_code=403, detail="No tienes permiso para descargar esta factura."
            )

        if not invoice.receipt_pdf_url or not os.path.exists(invoice.receipt_pdf_url):
            raise HTTPException(
                status_code=404, detail="El archivo PDF del recibo no fue encontrado."
            )

        return FileResponse(
            path=invoice.receipt_pdf_url,
            media_type="application/pdf",
            filename=os.path.basename(invoice.receipt_pdf_url),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error en download_invoice_pdf (ID: {invoice_id}): {e}", exc_info=True
        )
        raise HTTPException(status_code=500, detail="Error interno del servidor.")


@billing_router.post(
    "/admin/invoices/process-overdue",
    dependencies=[Depends(has_permission("billing:process_overdue"))],
)
def process_overdue_invoices(db: Session = Depends(get_db)):
    logger.info("Iniciando el procesamiento de facturas vencidas.")
    try:
        late_fee_setting = (
            db.query(BusinessSettings).filter_by(setting_name="late_fee_amount").first()
        )
        suspension_days_setting = (
            db.query(BusinessSettings)
            .filter_by(setting_name="days_for_suspension")
            .first()
        )
        if not late_fee_setting or not suspension_days_setting:
            raise HTTPException(
                status_code=400,
                detail="Faltan reglas de negocio para procesar vencidas.",
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
            if (today - invoice.due_date.date()).days >= days_for_suspension:
                invoice.subscription.status = "suspended"
                suspended_count += 1

        db.commit()
        return {
            "message": "Proceso de vencidas completado.",
            "facturas_con_recargo": processed_count,
            "servicios_suspendidos": suspended_count,
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error en process_overdue_invoices: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno del servidor.")


@billing_router.get(
    "/users/me/invoices", response_model=PaginatedResponse[InvoiceOut], tags=["Cliente"]
)
def get_my_invoices(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user_id = current_user.get("user_id")
    logger.info(
        f"Usuario ID {user_id} solicitando historial de facturas (Página: {page})."
    )
    try:
        query = (
            db.query(Invoice)
            .filter_by(user_id=user_id)
            .order_by(Invoice.issue_date.desc())
        )
        total_items = query.count()
        invoices = query.offset((page - 1) * size).limit(size).all()
        return PaginatedResponse(
            total_items=total_items,
            total_pages=math.ceil(total_items / size),
            current_page=page,
            items=invoices,
        )
    except Exception as e:
        logger.error(
            f"Error al obtener facturas para usuario ID {user_id}: {e}", exc_info=True
        )
        raise HTTPException(status_code=500, detail="Error al obtener tus facturas.")
