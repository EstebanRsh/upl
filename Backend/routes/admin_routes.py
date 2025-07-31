# routes/admin_routes.py
import logging
import math
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, HTTPException, status, Header
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
from datetime import datetime
from sqlalchemy import func, extract

from config.db import get_db
from auth.security import Security

from models.models import (
    User,
    UserDetail,
    InputUser,
    UpdateUserDetail,
    BusinessSettings,
    Subscription,
    Payment,
    Invoice,
)
from schemas.common_schemas import PaginatedResponse
from schemas.user_schemas import UserOut
from schemas.settings_schemas import (
    Setting,
    SettingsUpdate,
    DashboardStats,
    ClientStatusSummary,
    InvoiceStatusSummary,
)

logger = logging.getLogger(__name__)
admin_router = APIRouter(prefix="/admin", tags=["Admin"])


class InvoiceStatusUpdate(BaseModel):
    status: str


def verify_admin_permission(authorization: str = Header(...)):
    token_data = Security.verify_token({"authorization": authorization})
    if not token_data.get("success") or token_data.get("role") != "administrador":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos de administrador.",
        )
    return token_data


# --- GESTIÓN DE CLIENTES ---


@admin_router.get(
    "/users/all",
    response_model=PaginatedResponse[UserOut],
    summary="Obtener lista paginada de todos los clientes",
    dependencies=[Depends(verify_admin_permission)],
)
def get_all_users(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    username: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    logger.info("Solicitando la lista de usuarios.")
    try:
        query = (
            db.query(User).join(User.userdetail).filter(UserDetail.type == "cliente")
        )
        if username:
            query = query.filter(User.username.ilike(f"{username}%"))

        total_items = query.count()
        offset = (page - 1) * size
        users_from_db = (
            query.options(joinedload(User.userdetail)).offset(offset).limit(size).all()
        )
        total_pages = math.ceil(total_items / size)

        items_list = []
        for user in users_from_db:
            if user.userdetail:
                items_list.append(
                    UserOut(
                        id=user.id,
                        username=user.username,
                        email=user.email,
                        dni=user.userdetail.dni,
                        firstname=user.userdetail.firstname,
                        lastname=user.userdetail.lastname,
                        address=user.userdetail.address,
                        barrio=user.userdetail.barrio,
                        city=user.userdetail.city,
                        phone=user.userdetail.phone,
                        phone2=user.userdetail.phone2,
                        role=user.userdetail.type,
                    )
                )

        return PaginatedResponse(
            total_items=total_items,
            total_pages=total_pages,
            current_page=page,
            items=items_list,
        )
    except Exception as e:
        logger.error(f"Error inesperado en get_all_users: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno del servidor.")


@admin_router.get(
    "/users/{dni}",
    response_model=UserOut,
    summary="Obtener los datos de un único cliente por DNI",
    dependencies=[Depends(verify_admin_permission)],
)
def get_user_by_dni(dni: str, db: Session = Depends(get_db)):
    """
    CORRECCIÓN: Se reescribió la consulta para que sea más robusta y directa,
    evitando el error de 'InstrumentedList'.
    """
    logger.info(f"Buscando usuario con DNI: {dni}")

    # Se busca directamente en la tabla User, uniendo con UserDetail
    user = db.query(User).join(UserDetail).filter(UserDetail.dni == dni).first()

    if not user or not user.userdetail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado con el DNI proporcionado.",
        )

    ud = user.userdetail
    return UserOut(
        id=user.id,
        username=user.username,
        email=user.email,
        dni=ud.dni,
        firstname=ud.firstname,
        lastname=ud.lastname,
        address=ud.address,
        barrio=ud.barrio,
        city=ud.city,
        phone=ud.phone,
        phone2=ud.phone2,
        role=ud.type,
    )


@admin_router.post(
    "/users/add",
    status_code=status.HTTP_201_CREATED,
    summary="Añadir un nuevo cliente",
    dependencies=[Depends(verify_admin_permission)],
)
def add_user(user_data: InputUser, db: Session = Depends(get_db)):
    # Esta función no presentaba errores
    try:
        if db.query(User).filter(User.username == user_data.username).first():
            raise HTTPException(
                status_code=409, detail="El nombre de usuario ya existe."
            )
        if (
            user_data.email
            and db.query(User).filter(User.email == user_data.email).first()
        ):
            raise HTTPException(status_code=409, detail="El email ya está en uso.")
        if db.query(UserDetail).filter(UserDetail.dni == user_data.dni).first():
            raise HTTPException(
                status_code=409, detail=f"El DNI '{user_data.dni}' ya está registrado."
            )

        new_user_detail = UserDetail(
            dni=user_data.dni,
            firstname=user_data.firstname,
            lastname=user_data.lastname,
            type="cliente",
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
        new_user.userdetail = new_user_detail
        db.add(new_user)
        db.commit()
        return {"message": "Cliente agregado exitosamente"}
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail=f"Error de integridad. DNI '{user_data.dni}' ya registrado.",
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Error al agregar usuario: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno del servidor.")


@admin_router.put(
    "/users/{user_id}/details",
    summary="Actualizar detalles de un cliente",
    dependencies=[Depends(verify_admin_permission)],
)
def update_user_details(
    user_id: int, user_data: UpdateUserDetail, db: Session = Depends(get_db)
):
    # Esta función no presentaba errores
    user_to_update = db.query(User).filter(User.id == user_id).first()
    if not user_to_update or not user_to_update.userdetail:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    update_data = user_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(user_to_update.userdetail, key, value)
    db.commit()
    return {"message": f"Detalles del usuario con ID {user_id} actualizados."}


@admin_router.delete(
    "/users/{user_id}",
    summary="Eliminar un cliente",
    dependencies=[Depends(verify_admin_permission)],
)
def delete_user(
    user_id: int,
    token_data: dict = Depends(verify_admin_permission),
    db: Session = Depends(get_db),
):
    # Esta función no presentaba errores
    requesting_user_id = token_data.get("user_id")
    if requesting_user_id == user_id:
        raise HTTPException(
            status_code=400, detail="Un administrador no puede eliminarse a sí mismo."
        )
    user_to_delete = db.query(User).filter(User.id == user_id).first()
    if not user_to_delete:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    db.delete(user_to_delete)
    db.commit()
    return {"message": f"Usuario con ID {user_id} ha sido eliminado."}


# --- GESTIÓN DE FACTURAS Y PAGOS ---


@admin_router.put(
    "/invoices/{invoice_id}/status",
    status_code=status.HTTP_200_OK,
    summary="Aprobar o rechazar el pago de una factura",
    dependencies=[Depends(verify_admin_permission)],
)
def update_invoice_status(
    invoice_id: int, update_data: InvoiceStatusUpdate, db: Session = Depends(get_db)
):
    # Esta función no presentaba errores
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Factura no encontrada.")

    valid_statuses = ["pagado", "rechazado"]
    new_status = update_data.status.lower()

    if new_status not in valid_statuses:
        raise HTTPException(
            status_code=400, detail="Estado no válido. Use 'Pagado' o 'Rechazado'."
        )

    invoice.status = new_status.capitalize()

    if new_status == "pagado":
        existing_payment = (
            db.query(Payment).filter(Payment.invoice_id == invoice_id).first()
        )
        if not existing_payment:
            new_payment = Payment(
                user_id=invoice.user_id,
                invoice_id=invoice.id,
                amount=invoice.amount,
                payment_date=datetime.utcnow(),
                payment_method="manual_approval",
            )
            db.add(new_payment)

    db.commit()
    return {"message": f"El estado de la factura {invoice_id} ha sido actualizado."}


# --- CONFIGURACIÓN Y DASHBOARD ---


@admin_router.get(
    "/settings",
    response_model=List[Setting],
    summary="Obtener las configuraciones del negocio",
    dependencies=[Depends(verify_admin_permission)],
)
def get_business_settings(db: Session = Depends(get_db)):
    return db.query(BusinessSettings).all()


@admin_router.put(
    "/settings",
    status_code=200,
    summary="Actualizar las configuraciones del negocio",
    dependencies=[Depends(verify_admin_permission)],
)
def update_business_settings(
    update_data: SettingsUpdate, db: Session = Depends(get_db)
):
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


@admin_router.get(
    "/dashboard",
    response_model=DashboardStats,
    summary="Obtener estadísticas del panel de control",
    dependencies=[Depends(verify_admin_permission)],
)
def get_dashboard_stats(db: Session = Depends(get_db)):
    # Esta función ahora está corregida
    now = datetime.utcnow()
    total_clients = db.query(UserDetail).filter(UserDetail.type == "cliente").count()
    active_clients = (
        db.query(Subscription.user_id)
        .filter(Subscription.status == "active")
        .distinct()
        .count()
    )
    suspended_clients = (
        db.query(Subscription.user_id)
        .filter(Subscription.status == "suspended")
        .distinct()
        .count()
    )

    client_summary = ClientStatusSummary(
        active_clients=active_clients,
        suspended_clients=suspended_clients,
        total_clients=total_clients,
    )

    pending_invoices = (
        db.query(Invoice).filter(Invoice.status.ilike("pendiente%")).count()
    )
    paid_invoices = db.query(Invoice).filter(Invoice.status == "Pagado").count()
    overdue_invoices = (
        db.query(Invoice)
        .filter(Invoice.status.ilike("pendiente%"), Invoice.due_date < now.date())
        .count()
    )

    invoice_summary = InvoiceStatusSummary(
        pending=pending_invoices,
        paid=paid_invoices,
        overdue=overdue_invoices,
        total=db.query(Invoice).count(),
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

    # CORRECCIÓN: Usamos 'subscription_date' en lugar de 'start_date'
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


@admin_router.get(
    "/users/id/{user_id}",
    response_model=UserOut,
    summary="Obtener los datos de un único cliente por ID",
    dependencies=[Depends(verify_admin_permission)],
)
def get_user_by_id(user_id: int, db: Session = Depends(get_db)):
    """
    Obtiene toda la información de un usuario específico buscando por su ID.
    Este es el método preferido para la página de 'Editar Cliente'.
    """
    logger.info(f"Buscando usuario con ID: {user_id}")

    user = db.query(User).filter(User.id == user_id).first()

    if not user or not user.userdetail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado con el ID proporcionado.",
        )

    ud = user.userdetail
    return UserOut(
        id=user.id,
        username=user.username,
        email=user.email,
        dni=ud.dni,
        firstname=ud.firstname,
        lastname=ud.lastname,
        address=ud.address,
        barrio=ud.barrio,
        city=ud.city,
        phone=ud.phone,
        phone2=ud.phone2,
        role=ud.type,
    )
