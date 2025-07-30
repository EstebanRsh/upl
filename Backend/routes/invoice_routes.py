# Backend/routes/invoice_routes.py
import logging
import shutil
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Header
from sqlalchemy.orm import Session
from models.models import Invoice
from auth.security import Security
from config.db import get_db
import os

logger = logging.getLogger(__name__)
invoice_router = APIRouter()

# Crear el directorio si no existe
UPLOAD_DIRECTORY = "./uploads/receipts"
os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)


@invoice_router.post(
    "/invoices/{invoice_id}/upload-receipt",
    summary="Subir comprobante de pago para una factura",
    tags=["Cliente"],
)
def upload_receipt(
    invoice_id: int,
    file: UploadFile = File(...),
    authorization: str = Header(...),
    db: Session = Depends(get_db),
):
    token_data = Security.verify_token({"authorization": authorization})
    if not token_data.get("success"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=token_data.get("message")
        )

    user_id = token_data.get("user_id")
    logger.info(
        f"Usuario ID {user_id} subiendo comprobante para factura ID {invoice_id}."
    )

    invoice = db.query(Invoice).filter_by(id=invoice_id, user_id=user_id).first()
    if not invoice:
        raise HTTPException(
            status_code=404, detail="Factura no encontrada o no pertenece al usuario."
        )

    if invoice.status == "paid":
        raise HTTPException(status_code=400, detail="Esta factura ya ha sido pagada.")

    try:
        # Generar un nombre de archivo único para evitar colisiones
        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"receipt_{invoice_id}_{user_id}{file_extension}"
        file_path = os.path.join(UPLOAD_DIRECTORY, unique_filename)

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Actualizar la factura para indicar que el pago está pendiente de revisión
        invoice.status = "in_review"
        invoice.receipt_pdf_url = (
            file_path  # Guardamos la ruta para referencia del admin
        )
        db.commit()

        logger.info(f"Comprobante para factura {invoice_id} guardado en '{file_path}'.")
        return {
            "message": "Comprobante subido exitosamente. Será verificado a la brevedad."
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Error al subir el comprobante para la factura {invoice_id}: {e}")
        raise HTTPException(status_code=500, detail="Error al procesar el archivo.")
    finally:
        file.file.close()
