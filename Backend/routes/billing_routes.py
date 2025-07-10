# routes/billing_routes.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse, FileResponse
from models.models import (
    session,
    BusinessSettings,
    Setting,
    Subscription,
    Invoice,
    User,
)
from auth.security import is_admin, get_current_user
import datetime
import os

billing_router = APIRouter()


@billing_router.post("/admin/settings/set")
def set_business_setting(setting_data: Setting, admin_user: dict = Depends(is_admin)):
    """
    Crea o actualiza una regla de negocio en la base de datos.
    """
    try:
        # Busca si la configuración ya existe
        setting = (
            session.query(BusinessSettings)
            .filter(BusinessSettings.setting_name == setting_data.setting_name)
            .first()
        )

        if setting:
            # Si existe, la actualiza
            setting.setting_value = setting_data.setting_value
            setting.description = setting_data.description
        else:
            # Si no existe, la crea
            setting = BusinessSettings(
                setting_name=setting_data.setting_name,
                setting_value=setting_data.setting_value,
                description=setting_data.description,
            )
            session.add(setting)

        session.commit()
        return {
            "message": f"Configuración '{setting_data.setting_name}' guardada exitosamente."
        }

    except Exception as e:
        session.rollback()
        return JSONResponse(status_code=500, content={"error": str(e)})
    finally:
        session.close()


@billing_router.post("/admin/invoices/generate-monthly")
def generate_monthly_invoices(admin_user: dict = Depends(is_admin)):
    """
    Genera las facturas mensuales para todas las suscripciones activas.
    """
    try:
        # 1. Obtener las reglas de negocio necesarias
        payment_window_setting = (
            session.query(BusinessSettings)
            .filter(BusinessSettings.setting_name == "payment_window_days")
            .first()
        )
        if not payment_window_setting:
            raise HTTPException(
                status_code=400,
                detail="La regla 'payment_window_days' no está configurada.",
            )

        payment_window_days = int(payment_window_setting.setting_value)

        # 2. Buscar todas las suscripciones activas
        active_subscriptions = (
            session.query(Subscription).filter(Subscription.status == "active").all()
        )

        generated_count = 0
        for sub in active_subscriptions:
            # 3. Crear una nueva factura para cada suscripción
            issue_date = datetime.date.today()
            due_date = issue_date + datetime.timedelta(days=payment_window_days)

            new_invoice = Invoice(
                user_id=sub.user_id,
                subscription_id=sub.id,
                due_date=due_date,
                base_amount=sub.plan.price,
                total_amount=sub.plan.price,
            )
            session.add(new_invoice)
            generated_count += 1

        session.commit()
        return {
            "message": f"Proceso completado. Se generaron {generated_count} facturas."
        }

    except Exception as e:
        session.rollback()
        return JSONResponse(status_code=500, content={"error": str(e)})
    finally:
        session.close()


@billing_router.get("/invoices/{invoice_id}/download")
def download_invoice_pdf(
    invoice_id: int, current_user: dict = Depends(get_current_user)
):
    """
    Permite a un administrador o al dueño de la factura descargar el PDF del recibo.
    """
    try:
        # 1. Buscar la factura en la base de datos
        invoice = session.query(Invoice).filter(Invoice.id == invoice_id).first()

        if not invoice:
            raise HTTPException(status_code=404, detail="Factura no encontrada")

        # 2. Verificar permisos
        token_user_id = current_user.get("user_id")
        token_user_role = current_user.get("role")

        if token_user_role != "administrador" and token_user_id != invoice.user_id:
            raise HTTPException(
                status_code=403, detail="No tienes permiso para descargar esta factura."
            )

        # 3. Comprobar que el recibo PDF existe
        if not invoice.receipt_pdf_url:
            raise HTTPException(
                status_code=404,
                detail="Esta factura no tiene un recibo PDF asociado (probablemente no ha sido pagada).",
            )

        # 4. Construir la ruta completa al archivo y devolverlo
        # La ruta base es la carpeta 'facturas' en la raíz de tu proyecto
        file_path = os.path.join("facturas", invoice.receipt_pdf_url)

        if not os.path.exists(file_path):
            raise HTTPException(
                status_code=404,
                detail="El archivo PDF del recibo no fue encontrado en el servidor.",
            )

        return FileResponse(
            path=file_path,
            media_type="application/pdf",
            filename=f"recibo_{invoice_id}.pdf",
        )

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
    finally:
        session.close()
