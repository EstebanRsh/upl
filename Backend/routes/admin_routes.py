# routes/admin_routes.py
# -----------------------------------------------------------------------------
# RUTAS DE ADMINISTRACIÓN
# -----------------------------------------------------------------------------
# routes/admin_routes.py
import logging
import math
from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from config.db import get_db
from auth.security import get_current_user
from auth.security import has_permission, Security
from models.models import (
    User,
    UserDetail,
    Subscription,
    Invoice,
    Payment,
    Role,
    DashboardStats,
    ClientStatusSummary,
    InvoiceStatusSummary,
    InputUser,
    UpdateUserDetail,
    PaginatedResponse,
    UserOut,
    BusinessSettings,
)
from schemas.settings_schemas import Setting, SettingsUpdate

logger = logging.getLogger(__name__)
admin_router = APIRouter()


@admin_router.post(
    "/users/add",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(has_permission("users:create"))],
)
def add_user(user_data: InputUser, db: Session = Depends(get_db)):
    logger.info(f"Iniciando creación de usuario '{user_data.username}'.")
    try:
        client_role = db.query(Role).filter(Role.name == "Cliente").first()
        if not client_role:
            logger.error(
                "El rol por defecto 'Cliente' no se encontró en la base de datos."
            )
            raise HTTPException(
                status_code=500,
                detail="Error de configuración del servidor: rol de cliente no encontrado.",
            )

        new_user_detail = UserDetail(
            dni=user_data.dni,
            firstname=user_data.firstname,
            lastname=user_data.lastname,
            address=user_data.address,
            phone=user_data.phone,
            city=user_data.city,
            barrio=user_data.barrio,
            phone2=user_data.phone2,
        )
        hashed_password = Security.get_password_hash(user_data.password)
        new_user = User(
            username=user_data.username, password=hashed_password, email=user_data.email
        )
        new_user.role_obj = client_role
        new_user.userdetail = new_user_detail
        db.add(new_user)
        db.commit()
        logger.info(
            f"Usuario '{user_data.username}' creado exitosamente con el rol 'Cliente'."
        )
        return {"message": "Cliente agregado exitosamente"}
    except IntegrityError:
        db.rollback()
        logger.warning(
            f"Conflicto al crear usuario. Username '{user_data.username}' o email '{user_data.email}' ya existen."
        )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"El usuario '{user_data.username}' o el email '{user_data.email}' ya existen.",
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error inesperado en add_user: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno del servidor.")


@admin_router.get(
    "/users/all",
    response_model=PaginatedResponse[UserOut],
    dependencies=[Depends(has_permission("users:read_all"))],
)
def get_all_users(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    username: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    logger.info(f"Solicitando la lista de usuarios.")
    try:
        query = db.query(User).join(User.userdetail)
        if username:
            query = query.filter(User.username.ilike(f"{username}%"))
        total_items = query.count()
        offset = (page - 1) * size
        users_query = query.offset(offset).limit(size).all()
        total_pages = math.ceil(total_items / size)
        items_list = [
            UserOut.model_validate(user.userdetail)
            for user in users_query
            if user.userdetail
        ]
        return PaginatedResponse(
            total_items=total_items,
            total_pages=total_pages,
            current_page=page,
            items=items_list,
        )
    except Exception as e:
        logger.error(f"Error inesperado en get_all_users: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno del servidor.")


@admin_router.put(
    "/users/{user_id}/details", dependencies=[Depends(has_permission("users:update"))]
)
def update_user_details(
    user_id: int, user_data: UpdateUserDetail, db: Session = Depends(get_db)
):
    logger.info(f"Actualizando detalles para el usuario ID: {user_id}.")
    try:
        user_to_update = db.query(User).filter(User.id == user_id).first()
        if not user_to_update or not user_to_update.userdetail:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        update_data = user_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(user_to_update.userdetail, key, value)
        db.commit()
        logger.info(f"Detalles del usuario ID {user_id} actualizados.")
        return {"message": f"Detalles del usuario con ID {user_id} actualizados."}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(
            f"Error en update_user_details (ID: {user_id}): {e}", exc_info=True
        )
        raise HTTPException(status_code=500, detail="Error interno del servidor.")


@admin_router.delete(
    "/users/{user_id}", dependencies=[Depends(has_permission("users:delete"))]
)
def delete_user(
    user_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    logger.info(
        f"Usuario '{current_user.get('sub')}' solicitando eliminar usuario ID: {user_id}."
    )
    try:
        if current_user.get("user_id") == user_id:
            raise HTTPException(
                status_code=400, detail="Un usuario no puede eliminarse a sí mismo."
            )
        user_to_delete = db.query(User).filter(User.id == user_id).first()
        if not user_to_delete:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        db.delete(user_to_delete)
        db.commit()
        logger.info(f"Usuario ID {user_id} eliminado exitosamente.")
        return {"message": f"Usuario con ID {user_id} ha sido eliminado."}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error en delete_user (ID: {user_id}): {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno del servidor.")


@admin_router.get(
    "/settings",
    response_model=list[Setting],
    dependencies=[Depends(has_permission("roles:manage"))],
)
def get_business_settings(db: Session = Depends(get_db)):
    logger.info("Solicitando las configuraciones de la empresa.")
    try:
        return db.query(BusinessSettings).all()
    except Exception as e:
        logger.error(f"Error en get_business_settings: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Error al obtener las configuraciones."
        )


@admin_router.put(
    "/settings", status_code=200, dependencies=[Depends(has_permission("roles:manage"))]
)
def update_business_settings(
    update_data: SettingsUpdate, db: Session = Depends(get_db)
):
    logger.info("Actualizando las configuraciones de la empresa.")
    try:
        for setting_item in update_data.settings:
            db_setting = (
                db.query(BusinessSettings)
                .filter_by(setting_name=setting_item.setting_name)
                .first()
            )
            if db_setting:
                db_setting.setting_value = setting_item.setting_value
            else:
                db.add(BusinessSettings(**setting_item.model_dump()))
        db.commit()
        return {"message": "Configuraciones actualizadas exitosamente"}
    except Exception as e:
        db.rollback()
        logger.error(f"Error en update_business_settings: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Error al actualizar las configuraciones."
        )


@admin_router.get(
    "/dashboard",
    response_model=DashboardStats,
    summary="Obtener estadísticas del panel de control",
    dependencies=[Depends(has_permission("users:read_all"))],
)
def get_dashboard_stats(db: Session = Depends(get_db)):
    logger.info("Solicitando estadísticas del panel de control.")
    try:
        now = datetime.utcnow()
        active_clients = (
            db.query(Subscription)
            .filter_by(status="active")
            .distinct(Subscription.user_id)
            .count()
        )
        suspended_clients = (
            db.query(Subscription)
            .filter_by(status="suspended")
            .distinct(Subscription.user_id)
            .count()
        )
        total_clients = db.query(User).join(Role).filter(Role.name == "Cliente").count()
        client_summary = ClientStatusSummary(
            active_clients=active_clients,
            suspended_clients=suspended_clients,
            total_clients=total_clients,
        )

        pending_invoices = (
            db.query(Invoice)
            .filter_by(status="pending")
            .filter(Invoice.due_date >= now.date())
            .count()
        )
        paid_invoices = db.query(Invoice).filter_by(status="paid").count()
        overdue_invoices = (
            db.query(Invoice)
            .filter_by(status="pending")
            .filter(Invoice.due_date < now.date())
            .count()
        )
        invoice_summary = InvoiceStatusSummary(
            pending=pending_invoices,
            paid=paid_invoices,
            overdue=overdue_invoices,
            total=pending_invoices + paid_invoices + overdue_invoices,
        )

        monthly_revenue = (
            db.query(func.sum(Payment.amount))
            .filter(
                extract("month", Payment.payment_date) == now.month,
                extract("year", Payment.payment_date) == now.year,
            )
            .scalar()
            or 0.0
        )
        new_subscriptions = (
            db.query(Subscription)
            .filter(
                extract("month", Subscription.subscription_date) == now.month,
                extract("year", Subscription.subscription_date) == now.year,
            )
            .count()
        )

        return DashboardStats(
            client_summary=client_summary,
            invoice_summary=invoice_summary,
            monthly_revenue=round(monthly_revenue, 2),
            new_subscriptions_this_month=new_subscriptions,
        )
    except Exception as e:
        logger.error(
            f"Error al calcular las estadísticas del panel de control: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=500, detail="Error interno al generar las estadísticas."
        )


@admin_router.put(
    "/settings/billing/automation",
    summary="Activa o desactiva la facturación automática",
    dependencies=[Depends(has_permission("roles:manage"))],
)
def set_billing_automation(is_enabled: bool, db: Session = Depends(get_db)):
    setting_name = "auto_invoicing_enabled"
    logger.info(f"Cambiando el estado de la facturación automática a: {is_enabled}.")

    setting = db.query(BusinessSettings).filter_by(setting_name=setting_name).first()

    if setting:
        setting.setting_value = str(is_enabled).lower()
    else:
        new_setting = BusinessSettings(
            setting_name=setting_name,
            setting_value=str(is_enabled).lower(),
            description="Controla si la generación de facturas se ejecuta automáticamente cada mes.",
        )
        db.add(new_setting)

    db.commit()

    return {
        "message": f"Facturación automática {'activada' if is_enabled else 'desactivada'}."
    }
