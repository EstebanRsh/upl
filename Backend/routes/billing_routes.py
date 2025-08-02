# routes/billing_routes.py
import logging
import datetime
import os
import math
import shutil
from typing import Optional
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    Query,
    Header,
    Form,
    UploadFile,
    File,
)
from fastapi.responses import FileResponse
from sqlalchemy import extract, or_
from sqlalchemy.orm import Session, joinedload
from datetime import date

# --- 1. MODELOS DE LA BASE DE DATOS (ACTUALIZADOS) ---
from models.models import (
    Subscription,
    Invoice,
    User,
    Payment,
    UserDetail,
    InputPaymentAdmin,
    CompanySettings,  # <-- Usamos el nuevo modelo robusto y simple
)

# --- 2. SCHEMAS DE PYDANTIC ---
from schemas.invoice_schemas import InvoiceOut, InvoiceAdminOut, UpdateInvoiceStatus
from schemas.payment_schemas import PaymentAdminOut
from schemas.common_schemas import PaginatedResponse

# --- 3. SERVICIOS Y UTILIDADES ---
from auth.security import Security
from config.db import get_db
from services.payment_service import process_new_payment_admin, PaymentException


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


# --- LÓGICA DE LA API ---


@billing_router.get(
    "/admin/payments/all",
    response_model=PaginatedResponse[PaymentAdminOut],
    dependencies=[Depends(verify_admin_permission)],
    tags=["Admin"],
)
def get_all_payments_for_admin(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    search: Optional[str] = Query(None),
    month: Optional[int] = Query(None, ge=1, le=12),
    year: Optional[int] = Query(None, ge=2020),
    payment_method: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    try:
        query = db.query(Payment).order_by(Payment.payment_date.desc())
        query = query.join(User, Payment.user_id == User.id).join(
            UserDetail, User.id_userdetail == UserDetail.id
        )

        if search:
            search_term = f"%{search}%"
            search_filters = [
                UserDetail.firstname.ilike(search_term),
                UserDetail.lastname.ilike(search_term),
            ]
            if search.isdigit():
                search_filters.append(UserDetail.dni == int(search))
            query = query.filter(or_(*search_filters))

        if month:
            query = query.filter(extract("month", Payment.payment_date) == month)
        if year:
            query = query.filter(extract("year", Payment.payment_date) == year)
        if payment_method:
            query = query.filter(Payment.payment_method.ilike(f"%{payment_method}%"))

        total_items = query.count()
        payments_from_db = (
            query.options(joinedload(Payment.user).joinedload(User.userdetail))
            .offset((page - 1) * size)
            .limit(size)
            .all()
        )
        items_list = []
        for p in payments_from_db:
            if p.user and p.user.userdetail:
                items_list.append(
                    PaymentAdminOut(
                        id=p.id,
                        payment_date=p.payment_date,
                        amount=p.amount,
                        payment_method=p.payment_method,
                        invoice_id=p.invoice_id,
                        user={
                            "firstname": p.user.userdetail.firstname,
                            "lastname": p.user.userdetail.lastname,
                            "dni": p.user.userdetail.dni,
                        },
                    )
                )

        return PaginatedResponse(
            total_items=total_items,
            total_pages=math.ceil(total_items / size),
            current_page=page,
            items=items_list,
        )
    except Exception as e:
        logger.error(f"Error al obtener pagos para admin: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno del servidor.")


@billing_router.post(
    "/admin/payments/register",
    summary="Registrar un nuevo pago manualmente por un admin",
    dependencies=[Depends(verify_admin_permission)],
    tags=["Admin"],
)
def register_manual_payment(
    invoice_id: int = Form(...),
    amount: float = Form(...),
    payment_date: date = Form(...),
    payment_method: str = Form(...),
    receipt_file: UploadFile = File(None),
    db: Session = Depends(get_db),
):
    receipt_path = None
    if receipt_file:
        upload_folder = "uploads/receipts"
        os.makedirs(upload_folder, exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        file_extension = os.path.splitext(receipt_file.filename)[1]
        unique_filename = f"receipt_{invoice_id}_{timestamp}{file_extension}"
        file_path = os.path.join(upload_folder, unique_filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(receipt_file.file, buffer)
        receipt_path = file_path.replace("\\", "/")

    payment_data = InputPaymentAdmin(
        invoice_id=invoice_id,
        amount=amount,
        payment_date=payment_date,
        payment_method=payment_method,
        receipt_url=receipt_path,
    )
    try:
        result = process_new_payment_admin(payment_data, db)
        return result
    except PaymentException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


def generate_monthly_invoices_logic(db: Session):
    logger.info("Iniciando la lógica de generación de facturas mensuales.")

    settings = db.query(CompanySettings).first()
    if not settings:
        logger.error(
            "CRÍTICO: No se encontró la fila de configuración en la tabla company_settings."
        )
        return {"error": "La configuración del negocio no ha sido inicializada."}

    if not settings.auto_invoicing_enabled:
        return {
            "message": "Proceso omitido. La facturación automática está desactivada.",
            "facturas_generadas": 0,
        }

    payment_window_days = settings.payment_window_days
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
    logger.info(f"Facturas generadas: {generated_count}, omitidas: {skipped_count}.")
    return {
        "message": "Proceso de facturación mensual completado.",
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


@billing_router.post(
    "/admin/invoices/process-overdue",
    dependencies=[Depends(verify_admin_permission)],
    tags=["Admin"],
)
def process_overdue_invoices(db: Session = Depends(get_db)):
    settings = db.query(CompanySettings).first()
    if not settings:
        raise HTTPException(
            status_code=400,
            detail="La configuración del negocio no ha sido inicializada.",
        )

    late_fee = settings.late_fee_amount
    days_for_suspension = settings.days_for_suspension
    today = datetime.date.today()

    overdue_invoices = (
        db.query(Invoice)
        .filter(Invoice.status == "Pendiente", Invoice.due_date < today)
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
    "/admin/invoices/all",
    response_model=PaginatedResponse[InvoiceAdminOut],
    dependencies=[Depends(verify_admin_permission)],
    tags=["Admin"],
)
def get_all_invoices_for_admin(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    status: Optional[str] = Query(None),
    user_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    try:
        query = db.query(Invoice).order_by(Invoice.issue_date.desc())
        if status:
            query = query.filter(Invoice.status.ilike(f"%{status}%"))
        if user_id:
            query = query.filter(Invoice.user_id == user_id)
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
    invoice = (
        db.query(Invoice)
        .options(joinedload(Invoice.user).joinedload(User.userdetail))
        .filter(Invoice.id == invoice_id)
        .first()
    )
    if not invoice:
        raise HTTPException(status_code=404, detail="Factura no encontrada.")
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
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Factura no encontrada.")
    invoice.status = update_data.status
    db.commit()
    db.refresh(invoice)
    return get_invoice_by_id_for_admin(invoice_id=invoice_id, db=db)


@billing_router.get(
    "/users/me/invoices/{invoice_id}",
    response_model=InvoiceOut,
    tags=["Cliente"],
)
def get_my_invoice_by_id(
    invoice_id: int,
    authorization: str = Header(...),
    db: Session = Depends(get_db),
):
    token_data = Security.verify_token({"authorization": authorization})
    if not token_data.get("success"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=token_data.get("message"),
        )
    user_id = token_data.get("user_id")
    invoice = db.query(Invoice).filter_by(id=invoice_id, user_id=user_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Factura no encontrada")
    return invoice


@billing_router.post(
    "/users/me/invoices/{invoice_id}/upload-receipt",
    summary="Subir comprobante de pago del cliente",
    tags=["Cliente"],
)
def upload_user_receipt(
    invoice_id: int,
    file: UploadFile = File(...),
    authorization: str = Header(...),
    db: Session = Depends(get_db),
):
    token_data = Security.verify_token({"authorization": authorization})
    if not token_data.get("success"):
        raise HTTPException(status_code=401, detail=token_data.get("message"))
    user_id = token_data.get("user_id")
    invoice = db.query(Invoice).filter_by(id=invoice_id, user_id=user_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Factura no encontrada.")
    allowed_extensions = [".pdf", ".png", ".jpg", ".jpeg"]
    file_extension = os.path.splitext(file.filename)[1].lower()
    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Formato de archivo no permitido. Permitidos: {', '.join(allowed_extensions)}",
        )
    now = datetime.datetime.now()
    folder = f"uploads/user_receipts/{now.year}/{now.month:02d}"
    os.makedirs(folder, exist_ok=True)
    filename = f"user_receipt_{invoice.id}_{user_id}_{now.strftime('%Y%m%d%H%M%S')}{file_extension}"
    filepath = os.path.join(folder, filename)
    with open(filepath, "wb") as f:
        f.write(file.file.read())
    invoice.user_receipt_url = filepath.replace("\\", "/")
    invoice.status = "En Verificacion"
    db.commit()
    return {
        "message": "Comprobante subido correctamente y factura en verificación.",
        "path": filepath,
    }
