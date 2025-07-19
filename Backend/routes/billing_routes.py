# routes/billing_routes.py
# -----------------------------------------------------------------------------
# RUTAS DE FACTURACIÓN Y REGLAS DE NEGOCIO
# -----------------------------------------------------------------------------
# routes/billing_routes.py
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
from auth.security import is_admin, get_current_user
from config.db import get_db

logger = logging.getLogger(__name__)
billing_router = APIRouter()


@billing_router.post("/admin/settings/set")
def set_business_setting(
    setting_data: Setting,
    admin_user: dict = Depends(is_admin),
    db: Session = Depends(get_db),
):
    logger.info(
        f"Admin '{admin_user.get('sub')}' estableciendo regla de negocio: '{setting_data.setting_name}'."
    )
    try:
        setting = (
            db.query(BusinessSettings)
            .filter(BusinessSettings.setting_name == setting_data.setting_name)
            .first()
        )
        if setting:
            setting.setting_value = setting_data.setting_value
            setting.description = setting_data.description
        else:
            setting = BusinessSettings(
                setting_name=setting_data.setting_name,
                setting_value=setting_data.setting_value,
                description=setting_data.description,
            )
            db.add(setting)
        db.commit()
        logger.info(f"Regla de negocio '{setting_data.setting_name}' guardada.")
        return {
            "message": f"Configuración '{setting_data.setting_name}' guardada exitosamente."
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Error en set_business_setting: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno del servidor.")


@billing_router.post("/admin/invoices/generate-monthly")
def generate_monthly_invoices(
    admin_user: dict = Depends(is_admin), db: Session = Depends(get_db)
):
    logger.info(
        f"Admin '{admin_user.get('sub')}' ha iniciado la generación de facturas mensuales."
    )
    try:
        payment_window_setting = (
            db.query(BusinessSettings)
            .filter(BusinessSettings.setting_name == "payment_window_days")
            .first()
        )
        if not payment_window_setting:
            logger.warning(
                "La regla de negocio 'payment_window_days' no está configurada."
            )
            raise HTTPException(
                status_code=400,
                detail="La regla 'payment_window_days' no está configurada.",
            )
        # ... (lógica sin cambios) ...
        payment_window_days = int(payment_window_setting.setting_value)
        active_subscriptions = (
            db.query(Subscription).filter(Subscription.status == "active").all()
        )
        logger.info(
            f"Se encontraron {len(active_subscriptions)} suscripciones activas."
        )
        generated_count = 0
        skipped_count = 0
        today = datetime.date.today()
        for sub in active_subscriptions:
            existing_invoice = (
                db.query(Invoice)
                .filter(
                    Invoice.subscription_id == sub.id,
                    extract("year", Invoice.issue_date) == today.year,
                    extract("month", Invoice.issue_date) == today.month,
                )
                .first()
            )
            if existing_invoice:
                skipped_count += 1
                continue
            issue_date = today
            due_date = issue_date + datetime.timedelta(days=payment_window_days)
            new_invoice = Invoice(
                user_id=sub.user_id,
                subscription_id=sub.id,
                due_date=due_date,
                base_amount=sub.plan.price,
                total_amount=sub.plan.price,
            )
            db.add(new_invoice)
            generated_count += 1
        db.commit()
        logger.info(
            f"Proceso de facturación completado. Generadas: {generated_count}, Omitidas: {skipped_count}."
        )
        return {
            "message": "Proceso completado.",
            "facturas_generadas": generated_count,
            "facturas_omitidas_por_duplicado": skipped_count,
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(
            f"Error inesperado en generate_monthly_invoices: {e}", exc_info=True
        )
        raise HTTPException(status_code=500, detail="Error interno del servidor.")


@billing_router.get("/invoices/{invoice_id}/download")
def download_invoice_pdf(
    invoice_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    logger.info(
        f"Usuario '{current_user.get('sub')}' solicitando descarga del recibo para la factura ID: {invoice_id}."
    )
    try:
        invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
        if not invoice:
            logger.warning(
                f"Intento de descarga de factura no existente (ID: {invoice_id})."
            )
            raise HTTPException(status_code=404, detail="Factura no encontrada")
        # ... (lógica de permisos y comprobación sin cambios) ...
        token_user_id = current_user.get("user_id")
        token_user_role = current_user.get("role")
        if token_user_role != "administrador" and token_user_id != invoice.user_id:
            logger.warning(f"Acceso no autorizado a factura ID {invoice_id}.")
            raise HTTPException(
                status_code=403, detail="No tienes permiso para descargar esta factura."
            )
        if not invoice.receipt_pdf_url:
            logger.warning(f"Factura ID {invoice_id} no tiene un recibo PDF.")
            raise HTTPException(
                status_code=404, detail="Esta factura no tiene un recibo PDF asociado."
            )
        file_path = invoice.receipt_pdf_url
        if not os.path.exists(file_path):
            logger.error(f"Archivo PDF no encontrado en el servidor: {file_path}")
            raise HTTPException(
                status_code=404,
                detail="El archivo PDF del recibo no fue encontrado en el servidor.",
            )
        logger.info(f"Enviando archivo PDF para la factura ID: {invoice_id}.")
        return FileResponse(
            path=file_path,
            media_type="application/pdf",
            filename=os.path.basename(file_path),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error inesperado en download_invoice_pdf (ID: {invoice_id}): {e}",
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="Error interno del servidor.")


@billing_router.post("/admin/invoices/process-overdue")
def process_overdue_invoices(
    admin_user: dict = Depends(is_admin), db: Session = Depends(get_db)
):
    logger.info(
        f"Admin '{admin_user.get('sub')}' ha iniciado el procesamiento de facturas vencidas."
    )
    try:
        # ... (lógica sin cambios) ...
        late_fee_setting = (
            db.query(BusinessSettings).filter_by(setting_name="late_fee_amount").first()
        )
        suspension_days_setting = (
            db.query(BusinessSettings)
            .filter_by(setting_name="days_for_suspension")
            .first()
        )
        if not late_fee_setting or not suspension_days_setting:
            logger.error("Faltan reglas de negocio para procesar vencidas.")
            raise HTTPException(
                status_code=400,
                detail="Faltan reglas de negocio para 'late_fee_amount' o 'days_for_suspension'.",
            )
        late_fee_amount = float(late_fee_setting.setting_value)
        days_for_suspension = int(suspension_days_setting.setting_value)
        today = datetime.date.today()
        overdue_invoices = (
            db.query(Invoice)
            .filter(Invoice.status == "pending", Invoice.due_date < today)
            .all()
        )
        logger.info(f"Se encontraron {len(overdue_invoices)} facturas vencidas.")
        processed_count = 0
        suspended_count = 0
        for invoice in overdue_invoices:
            if invoice.late_fee == 0.0:
                invoice.late_fee = late_fee_amount
                invoice.total_amount += late_fee_amount
                processed_count += 1
            days_overdue = (today - invoice.due_date.date()).days
            if days_overdue >= days_for_suspension:
                subscription = db.get(Subscription, invoice.subscription_id)
                if subscription and subscription.status == "active":
                    subscription.status = "suspended"
                    suspended_count += 1
        db.commit()
        logger.info(
            f"Proceso de vencidas completado. Con recargo: {processed_count}, Suspendidos: {suspended_count}."
        )
        return {
            "message": "Proceso de facturas vencidas completado.",
            "facturas_con_recargo": processed_count,
            "servicios_suspendidos": suspended_count,
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(
            f"Error inesperado en process_overdue_invoices: {e}", exc_info=True
        )
        raise HTTPException(status_code=500, detail="Error interno del servidor.")


@billing_router.get(
    "/users/me/invoices",
    response_model=PaginatedResponse[InvoiceOut],
    summary="Consultar mi historial de facturas",
    description="**Permisos requeridos: `autenticado`**.<br>Devuelve una lista paginada de todas las facturas del usuario.",
    tags=["Cliente"],
)
def get_my_invoices(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user_id = current_user.get("user_id")
    logger.info(
        f"Usuario ID {user_id} solicitando su historial de facturas (Página: {page})."
    )
    try:
        query = (
            db.query(Invoice)
            .filter(Invoice.user_id == user_id)
            .order_by(Invoice.issue_date.desc())
        )

        total_items = query.count()
        offset = (page - 1) * size
        invoices_query = query.offset(offset).limit(size).all()
        total_pages = math.ceil(total_items / size)

        return PaginatedResponse(
            total_items=total_items,
            total_pages=total_pages,
            current_page=page,
            items=invoices_query,
        )
    except Exception as e:
        logger.error(
            f"Error al obtener facturas para usuario ID {user_id}: {e}", exc_info=True
        )
        raise HTTPException(status_code=500, detail="Error al obtener tus facturas.")
