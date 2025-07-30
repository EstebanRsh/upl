# routes/billing_routes.py
import logging
import datetime
import os
import math
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Header
from fastapi.responses import FileResponse
from sqlalchemy import extract
from sqlalchemy.orm import Session, joinedload

# Modelos de la DB
from models.models import BusinessSettings, Subscription, Invoice, User

# Schemas de Pydantic
from schemas.invoice_schemas import InvoiceOut, InvoiceAdminOut, UpdateInvoiceStatus
from schemas.common_schemas import PaginatedResponse
from schemas.settings_schemas import Setting, SettingsUpdate

from auth.security import Security
from config.db import get_db

logger = logging.getLogger(__name__)
billing_router = APIRouter()


def verify_admin_permission(authorization: str = Header(...)):
    token_data = Security.verify_token({"authorization": authorization})
    if not token_data.get("success") or token_data.get("role") != "administrador":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos de administrador para realizar esta acción.",
        )
    return token_data


def generate_monthly_invoices_logic(db: Session):
    logger.info("Iniciando la lógica de generación de facturas mensuales.")
    automation_setting = (
        db.query(BusinessSettings)
        .filter_by(setting_name="auto_invoicing_enabled")
        .first()
    )
    if automation_setting and automation_setting.setting_value.lower() != "true":
        return {
            "message": "Proceso omitido. La facturación automática está desactivada.",
            "facturas_generadas": 0,
            "facturas_omitidas": 0,
        }

    payment_window_setting = (
        db.query(BusinessSettings).filter_by(setting_name="payment_window_days").first()
    )
    if not payment_window_setting:
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


@billing_router.get(
    "/admin/invoices/all",
    response_model=PaginatedResponse[InvoiceAdminOut],
    dependencies=[Depends(verify_admin_permission)],
    tags=["Admin"],
)
def get_all_invoices_for_admin(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    try:
        query = db.query(Invoice).order_by(Invoice.issue_date.desc())

        if status:
            query = query.filter(Invoice.status == status)

        total_items = query.count()
        invoices_from_db = (
            query.options(joinedload(Invoice.user).joinedload(User.userdetail))
            .offset((page - 1) * size)
            .limit(size)
            .all()
        )

        total_pages = math.ceil(total_items / size)

        items_list = []
        for inv in invoices_from_db:
            if inv.user and inv.user.userdetail:
                invoice_data = {
                    "id": inv.id,
                    "issue_date": inv.issue_date,
                    "due_date": inv.due_date,
                    "base_amount": inv.base_amount,
                    "late_fee": inv.late_fee,
                    "total_amount": inv.total_amount,
                    "status": inv.status,
                    "receipt_pdf_url": inv.receipt_pdf_url,
                    "user": {
                        "username": inv.user.username,
                        "firstname": inv.user.userdetail.firstname,
                        "lastname": inv.user.userdetail.lastname,
                    },
                }
                items_list.append(invoice_data)

        return PaginatedResponse(
            total_items=total_items,
            total_pages=total_pages,
            current_page=page,
            items=items_list,
        )
    except Exception as e:
        logger.error(f"Error al obtener facturas para admin: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno del servidor.")


@billing_router.post(
    "/admin/invoices/generate-monthly",
    summary="Generar facturas mensuales manualmente",
    dependencies=[Depends(verify_admin_permission)],
    tags=["Admin"],
)
def generate_monthly_invoices_manual(db: Session = Depends(get_db)):
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
    invoice = db.query(Invoice).filter_by(id=invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Factura no encontrada")
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
    full_file_path = invoice.receipt_pdf_url
    if not os.path.exists(full_file_path):
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


@billing_router.get(
    "/admin/invoices/{invoice_id}",
    response_model=InvoiceAdminOut,
    dependencies=[Depends(verify_admin_permission)],
    tags=["Admin"],
)
def get_invoice_by_id_for_admin(invoice_id: int, db: Session = Depends(get_db)):
    """Obtiene una factura específica por su ID para el panel de admin."""
    invoice = (
        db.query(Invoice)
        .options(joinedload(Invoice.user).joinedload(User.userdetail))
        .filter(Invoice.id == invoice_id)
        .first()
    )
    if not invoice:
        raise HTTPException(status_code=404, detail="Factura no encontrada.")

    # Es importante construir la respuesta manualmente para que coincida con el schema
    if invoice.user and invoice.user.userdetail:
        return InvoiceAdminOut(
            id=invoice.id,
            issue_date=invoice.issue_date,
            due_date=invoice.due_date,
            base_amount=invoice.base_amount,
            late_fee=invoice.late_fee,
            total_amount=invoice.total_amount,
            status=invoice.status,
            receipt_pdf_url=invoice.receipt_pdf_url,
            user={
                "username": invoice.user.username,
                "firstname": invoice.user.userdetail.firstname,
                "lastname": invoice.user.userdetail.lastname,
            },
        )
    raise HTTPException(
        status_code=500, detail="Error de datos internos del usuario de la factura."
    )


@billing_router.put(
    "/admin/invoices/{invoice_id}/status",
    response_model=InvoiceAdminOut,
    dependencies=[Depends(verify_admin_permission)],
    tags=["Admin"],
)
def update_invoice_status(
    invoice_id: int,
    update_data: UpdateInvoiceStatus,
    db: Session = Depends(get_db),
):
    """Actualiza el estado de una factura (ej. 'pending' -> 'paid')."""
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Factura no encontrada.")

    # Aquí podrías añadir lógica extra, como verificar que el estado es válido
    invoice.status = update_data.status
    db.commit()
    db.refresh(invoice)

    # Devolvemos la factura actualizada para que el frontend pueda refrescar los datos
    return get_invoice_by_id_for_admin(invoice_id=invoice_id, db=db)
