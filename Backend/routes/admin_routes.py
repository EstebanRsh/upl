# routes/admin_routes.py
# -----------------------------------------------------------------------------
# RUTAS DE ADMINISTRACIÓN
# -----------------------------------------------------------------------------

import logging
import math
from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from config.db import get_db
from auth.security import is_admin, Security
from models.models import (
    User,
    UserDetail,
    Subscription,
    Invoice,
    Payment,
    DashboardStats,
    InputUser,
    UpdateUserDetail,
    PaginatedResponse,
    UserOut,
    BusinessSettings,
    ClientStatusSummary,
    InvoiceStatusSummary,
)
from schemas.settings_schemas import Setting, SettingsUpdate

logger = logging.getLogger(__name__)
admin_router = APIRouter()


@admin_router.post("/users/add", status_code=status.HTTP_201_CREATED)
def add_user(
    user_data: InputUser,
    db: Session = Depends(get_db),
    admin_user: dict = Depends(is_admin),
):
    logger.info(
        f"Admin '{admin_user.get('sub')}' iniciando creación de usuario '{user_data.username}'."
    )
    try:
        # ... (lógica sin cambios) ...
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
            username=user_data.username,
            password=hashed_password,
            email=user_data.email,
            role="cliente",
        )
        new_user.userdetail = new_user_detail
        db.add(new_user)
        db.commit()
        logger.info(f"Usuario '{user_data.username}' creado exitosamente.")
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


@admin_router.get("/users/all", response_model=PaginatedResponse[UserOut])
def get_all_users(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    username: Optional[str] = Query(None),
    admin_user: dict = Depends(is_admin),
    db: Session = Depends(get_db),
):
    logger.info(f"Admin '{admin_user.get('sub')}' solicitó la lista de usuarios.")
    try:
        # ... (lógica sin cambios) ...
        query = db.query(User).join(User.userdetail)
        if username:
            query = query.filter(User.username.ilike(f"{username}%"))
        total_items = query.count()
        offset = (page - 1) * size
        users_query = query.offset(offset).limit(size).all()
        total_pages = math.ceil(total_items / size)
        items_list = [
            UserOut(
                username=user.username,
                email=user.email,
                dni=user.userdetail.dni,
                firstname=user.userdetail.firstname,
                lastname=user.userdetail.lastname,
                address=user.userdetail.address,
                phone=user.userdetail.phone,
                role=user.role,
            )
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


@admin_router.put("/users/{user_id}/details")
def update_user_details(
    user_id: int,
    user_data: UpdateUserDetail,
    admin_user: dict = Depends(is_admin),
    db: Session = Depends(get_db),
):
    logger.info(
        f"Admin '{admin_user.get('sub')}' actualizando detalles para el usuario ID: {user_id}."
    )
    try:
        user_to_update = db.query(User).filter(User.id == user_id).first()
        if not user_to_update or not user_to_update.userdetail:
            logger.warning(
                f"Intento de actualizar un usuario no existente (ID: {user_id})."
            )
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        update_data = user_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(user_to_update.userdetail, key, value)
        db.commit()
        logger.info(f"Detalles del usuario ID {user_id} actualizados correctamente.")
        return {
            "message": f"Detalles del usuario con ID {user_id} actualizados exitosamente."
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(
            f"Error inesperado en update_user_details (ID: {user_id}): {e}",
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="Error interno del servidor.")


@admin_router.delete("/users/{user_id}")
def delete_user(
    user_id: int, admin_user: dict = Depends(is_admin), db: Session = Depends(get_db)
):
    token_user_id = admin_user.get("user_id")
    logger.info(
        f"Admin '{admin_user.get('sub')}' solicitando eliminar usuario ID: {user_id}."
    )
    try:
        if token_user_id == user_id:
            logger.warning(
                f"Admin '{admin_user.get('sub')}' intentó eliminarse a sí mismo."
            )
            raise HTTPException(
                status_code=400,
                detail="Un administrador no puede eliminarse a sí mismo.",
            )
        user_to_delete = db.query(User).filter(User.id == user_id).first()
        if not user_to_delete:
            logger.warning(
                f"Intento de eliminar un usuario no existente (ID: {user_id})."
            )
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        db.delete(user_to_delete)
        db.commit()
        logger.info(f"Usuario ID {user_id} eliminado exitosamente.")
        return {
            "message": f"Usuario con ID {user_id} y todos sus datos han sido eliminados."
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(
            f"Error inesperado en delete_user (ID: {user_id}): {e}", exc_info=True
        )
        raise HTTPException(status_code=500, detail="Error interno del servidor.")


@admin_router.get("/settings", response_model=list[Setting])
def get_business_settings(
    db: Session = Depends(get_db), _current_user: dict = Depends(is_admin)
):
    logger.info(f"Admin solicitó las configuraciones de la empresa.")
    try:
        settings = db.query(BusinessSettings).all()
        return settings
    except Exception as e:
        logger.error(f"Error inesperado en get_business_settings: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Error al obtener las configuraciones."
        )


@admin_router.put("/settings", status_code=200)
def update_business_settings(
    update_data: SettingsUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(is_admin),
):
    logger.info(
        f"Admin '{current_user.get('sub')}' está actualizando las configuraciones."
    )
    try:
        for setting_item in update_data.settings:
            db_setting = (
                db.query(BusinessSettings)
                .filter(BusinessSettings.setting_name == setting_item.setting_name)
                .first()
            )
            if db_setting:
                db_setting.setting_value = setting_item.setting_value
                logger.info(f"Configuración '{setting_item.setting_name}' actualizada.")
            else:
                new_setting = BusinessSettings(
                    setting_name=setting_item.setting_name,
                    setting_value=setting_item.setting_value,
                )
                db.add(new_setting)
                logger.info(
                    f"Nueva configuración '{setting_item.setting_name}' creada."
                )
        db.commit()
        return {"message": "Configuraciones actualizadas exitosamente"}
    except Exception as e:
        db.rollback()
        logger.error(
            f"Error inesperado en update_business_settings: {e}", exc_info=True
        )
        raise HTTPException(
            status_code=500, detail="Error al actualizar las configuraciones."
        )


@admin_router.get(
    "/dashboard",
    response_model=DashboardStats,
    summary="Obtener estadísticas del panel de control",
    description="**Permisos requeridos: `administrador`**.<br>Devuelve un resumen de las métricas clave del negocio.",
)
def get_dashboard_stats(
    admin_user: dict = Depends(is_admin),
    db: Session = Depends(get_db),
):
    logger.info(
        f"Admin '{admin_user.get('sub')}' solicitando estadísticas del panel de control."
    )
    try:
        now = datetime.utcnow()
        current_month = now.month
        current_year = now.year

        # 1. Resumen de Clientes
        active_clients = (
            db.query(Subscription)
            .filter(Subscription.status == "active")
            .distinct(Subscription.user_id)
            .count()
        )
        suspended_clients = (
            db.query(Subscription)
            .filter(Subscription.status == "suspended")
            .distinct(Subscription.user_id)
            .count()
        )
        total_clients = db.query(User).filter(User.role == "cliente").count()

        client_summary = ClientStatusSummary(
            active_clients=active_clients,
            suspended_clients=suspended_clients,
            total_clients=total_clients,
        )
        logger.info("Estadísticas de clientes calculadas.")

        # 2. Resumen de Facturas
        pending_invoices = (
            db.query(Invoice)
            .filter(Invoice.status == "pending", Invoice.due_date >= now.date())
            .count()
        )
        paid_invoices = db.query(Invoice).filter(Invoice.status == "paid").count()
        overdue_invoices = (
            db.query(Invoice)
            .filter(Invoice.status == "pending", Invoice.due_date < now.date())
            .count()
        )

        invoice_summary = InvoiceStatusSummary(
            pending=pending_invoices,
            paid=paid_invoices,
            overdue=overdue_invoices,
            total=pending_invoices + paid_invoices + overdue_invoices,
        )
        logger.info("Estadísticas de facturas calculadas.")

        # 3. Ingresos del Mes Actual
        # Suma los montos de los pagos realizados en el mes y año actual.
        monthly_revenue_query = (
            db.query(func.sum(Payment.amount))
            .filter(
                extract("month", Payment.payment_date) == current_month,
                extract("year", Payment.payment_date) == current_year,
            )
            .scalar()
        )
        monthly_revenue = monthly_revenue_query or 0.0
        logger.info(f"Ingresos del mes calculados: {monthly_revenue}")

        # 4. Nuevas Suscripciones del Mes
        new_subscriptions_this_month = (
            db.query(Subscription)
            .filter(
                extract("month", Subscription.subscription_date) == current_month,
                extract("year", Subscription.subscription_date) == current_year,
            )
            .count()
        )
        logger.info(f"Nuevas suscripciones del mes: {new_subscriptions_this_month}")

        # Construcción de la respuesta final
        return DashboardStats(
            client_summary=client_summary,
            invoice_summary=invoice_summary,
            monthly_revenue=round(monthly_revenue, 2),
            new_subscriptions_this_month=new_subscriptions_this_month,
        )

    except Exception as e:
        logger.error(
            f"Error al calcular las estadísticas del panel de control: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=500, detail="Error interno al generar las estadísticas."
        )
