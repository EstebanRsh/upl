# routes/billing_routes.py
# -----------------------------------------------------------------------------
# RUTAS DE FACTURACIÓN Y REGLAS DE NEGOCIO
# -----------------------------------------------------------------------------
# Este módulo se encarga de la lógica de facturación de alto nivel:
# 1. Configurar reglas de negocio que afectan a la facturación (ej. días de pago).
# 2. Generar facturas mensuales de forma masiva para todos los clientes activos.
# 3. Permitir la descarga de los recibos PDF una vez que una factura ha sido pagada.
# -----------------------------------------------------------------------------
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse, FileResponse
from sqlalchemy.orm import Session
from models.models import (
    BusinessSettings,
    Setting,
    Subscription,
    Invoice,
    User,
)
from auth.security import is_admin, get_current_user
import datetime
import os
from sqlalchemy import extract
from config.db import get_db

# Creación de un router específico para las rutas de facturación.
billing_router = APIRouter()


@billing_router.post(
    "/admin/settings/set",
    summary="Establecer una regla de negocio",
    description="**Permisos requeridos: `administrador`**.<br>Crea o actualiza una regla de negocio en el sistema, como los días de pago o el monto de la multa por mora.",
)
def set_business_setting(
    setting_data: Setting,
    admin_user: dict = Depends(is_admin),
    db: Session = Depends(get_db),
):
    """
    Crea o actualiza una regla de negocio en la base de datos.
    Permite cambiar parámetros del sistema sin necesidad de modificar el código.
    """
    try:
        # Busca si la configuración (ej. 'payment_window_days') ya existe.
        setting = (
            db.query(BusinessSettings)
            .filter(BusinessSettings.setting_name == setting_data.setting_name)
            .first()
        )

        if setting:
            # Si existe, la actualiza con los nuevos valores.
            setting.setting_value = setting_data.setting_value
            setting.description = setting_data.description
        else:
            # Si no existe, crea un nuevo registro.
            setting = BusinessSettings(
                setting_name=setting_data.setting_name,
                setting_value=setting_data.setting_value,
                description=setting_data.description,
            )
            db.add(setting)

        db.commit()
        return {
            "message": f"Configuración '{setting_data.setting_name}' guardada exitosamente."
        }
    except Exception as e:
        db.rollback()
        return JSONResponse(status_code=500, content={"error": str(e)})


@billing_router.post(
    "/admin/invoices/generate-monthly",
    summary="Generar facturas mensuales",
    description="**Permisos requeridos: `administrador`**.<br>Ejecuta el proceso masivo que crea las facturas para todas las suscripciones activas. Evita la creación de duplicados si ya existe una factura para el mes actual.",
)
def generate_monthly_invoices(
    admin_user: dict = Depends(is_admin), db: Session = Depends(get_db)
):
    """
    Genera las facturas mensuales para todas las suscripciones activas.
    AÑADIDA LA LÓGICA PARA EVITAR DUPLICADOS.
    """
    try:
        # 1. Obtiene la regla de negocio para la fecha de vencimiento.
        payment_window_setting = (
            db.query(BusinessSettings)
            .filter(BusinessSettings.setting_name == "payment_window_days")
            .first()
        )
        if not payment_window_setting:
            raise HTTPException(
                status_code=400,
                detail="La regla 'payment_window_days' no está configurada.",
            )
        payment_window_days = int(payment_window_setting.setting_value)

        # 2. Busca todas las suscripciones que estén 'activas'.
        active_subscriptions = (
            db.query(Subscription).filter(Subscription.status == "active").all()
        )

        generated_count = 0
        skipped_count = 0
        today = datetime.date.today()

        for sub in active_subscriptions:
            # --- VERIFICACIÓN ANTI-DUPLICADOS ---
            # Revisa si ya existe una factura para esta suscripción en el mes y año actual.
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
                continue  # Si ya existe, salta a la siguiente suscripción.

            # 3. Si no hay factura existente, crea una nueva.
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
        return {
            "message": "Proceso completado.",
            "facturas_generadas": generated_count,
            "facturas_omitidas_por_duplicado": skipped_count,
        }
    except Exception as e:
        db.rollback()
        return JSONResponse(status_code=500, content={"error": str(e)})


@billing_router.get(
    "/invoices/{invoice_id}/download",
    summary="Descargar recibo de factura en PDF",
    description="""
Permite descargar el recibo en PDF de una factura específica.

**Permisos:**
- **Cliente**: Puede descargar **únicamente los recibos de sus propias** facturas pagadas.
- **Administrador**: Puede descargar el recibo de **cualquier** factura pagada.
""",
)
def download_invoice_pdf(
    invoice_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Permite a un administrador o al dueño de la factura descargar el PDF del recibo.
    """
    try:
        # 1. Busca la factura en la base de datos.
        invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
        if not invoice:
            raise HTTPException(status_code=404, detail="Factura no encontrada")

        # 2. Verifica los permisos: solo el admin o el propio usuario pueden descargar.
        token_user_id = current_user.get("user_id")
        token_user_role = current_user.get("role")
        if token_user_role != "administrador" and token_user_id != invoice.user_id:
            raise HTTPException(
                status_code=403, detail="No tienes permiso para descargar esta factura."
            )

        # 3. Comprueba que el recibo PDF existe (la URL se guarda cuando se paga la factura).
        if not invoice.receipt_pdf_url:
            raise HTTPException(
                status_code=404,
                detail="Esta factura no tiene un recibo PDF asociado (probablemente no ha sido pagada).",
            )

        # 4. Construye la ruta completa al archivo PDF en el servidor.
        file_path = os.path.join("facturas", invoice.receipt_pdf_url)
        if not os.path.exists(file_path):
            raise HTTPException(
                status_code=404,
                detail="El archivo PDF del recibo no fue encontrado en el servidor.",
            )

        # Devuelve el archivo usando 'FileResponse', que se encarga de servir el archivo
        # con las cabeceras HTTP correctas.
        return FileResponse(
            path=file_path,
            media_type="application/pdf",
            filename=f"recibo_{invoice_id}.pdf",
        )
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@billing_router.post(
    "/admin/invoices/process-overdue",
    summary="Procesar facturas vencidas",
    description="**Permisos requeridos: `administrador`**.<br>Ejecuta el proceso que busca facturas vencidas, les aplica el cargo por mora correspondiente y suspende el servicio si se excede el plazo configurado.",
)
def process_overdue_invoices(
    admin_user: dict = Depends(is_admin), db: Session = Depends(get_db)
):
    """
    Busca facturas vencidas, aplica cargos por mora y suspende servicios si es necesario.
    """
    try:
        # 1. Obtiene las reglas de negocio para cargos por mora y días para suspensión.
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
                detail="Faltan reglas de negocio para 'late_fee_amount' o 'days_for_suspension'.",
            )

        late_fee_amount = float(late_fee_setting.setting_value)
        days_for_suspension = int(suspension_days_setting.setting_value)
        today = datetime.date.today()

        # 2. Busca facturas pendientes y vencidas
        overdue_invoices = (
            db.query(Invoice)
            .filter(Invoice.status == "pending", Invoice.due_date < today)
            .all()
        )

        processed_count = 0
        suspended_count = 0
        for invoice in overdue_invoices:
            # 3. Aplica cargo por mora si aún no se ha hecho
            if invoice.late_fee == 0.0:
                invoice.late_fee = late_fee_amount
                invoice.total_amount += late_fee_amount
                processed_count += 1

            # 4. Verifica si se debe suspender el servicio
            days_overdue = (today - invoice.due_date.date()).days
            if days_overdue >= days_for_suspension:
                subscription = db.get(Subscription, invoice.subscription_id)
                if subscription and subscription.status == "active":
                    subscription.status = "suspended"
                    suspended_count += 1

        db.commit()
        return {
            "message": "Proceso de facturas vencidas completado.",
            "facturas_con_recargo": processed_count,
            "servicios_suspendidos": suspended_count,
        }
    except Exception as e:
        db.rollback()
        return JSONResponse(status_code=500, content={"error": str(e)})
