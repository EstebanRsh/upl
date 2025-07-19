# core/logging_config.py
import logging
import sys
from logging.handlers import TimedRotatingFileHandler

# Define el formato que tendrán las líneas de log.
# Formato: [Fecha y Hora] [Nivel del Log] [Módulo que lo genera]: Mensaje
LOG_FORMAT = "%(asctime)s - %(levelname)s - [%(name)s]: %(message)s"
LOG_FILE = "logs/app.log"  # El archivo donde se guardarán los logs


def setup_logging():
    """
    Configura el sistema de logging para la aplicación.
    Establece un manejador para la consola y otro para un archivo rotativo.
    """
    # Obtenemos el logger raíz. Todos los demás loggers heredarán de este.
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)  # Nivel mínimo de registro (INFO, WARNING, ERROR)

    # Creamos el formateador con el formato que definimos
    formatter = logging.Formatter(LOG_FORMAT)

    # 1. Manejador de Consola (para ver los logs en la terminal)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 2. Manejador de Archivo (para guardar los logs)
    # Rota cada día a medianoche y conserva los logs de los últimos 7 días.
    file_handler = TimedRotatingFileHandler(
        LOG_FILE, when="midnight", interval=1, backupCount=7, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    logging.info("El sistema de logging ha sido configurado.")
