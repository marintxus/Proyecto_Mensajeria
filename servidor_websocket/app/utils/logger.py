import logging
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler

# === Logging del servidor ===
LOG_FILE = "logs/servidor.log"
log_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

log_handler = RotatingFileHandler(LOG_FILE, maxBytes=5*1024*1024, backupCount=10)
log_handler.setFormatter(log_formatter)

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(log_formatter)

# 🚨 Corrección clave: sobrescribir handlers anteriores de Gunicorn
logger_raiz = logging.getLogger()
logger_raiz.setLevel(logging.INFO)
logger_raiz.handlers.clear()  # Elimina handlers preconfigurados (como los de Gunicorn)
logger_raiz.addHandler(log_handler)
logger_raiz.addHandler(stream_handler)

# === Logging de acciones de usuario ===
acciones_logger = logging.getLogger("acciones")
acciones_logger.setLevel(logging.INFO)

acciones_handler = TimedRotatingFileHandler(
    "logs/acciones.log", when="midnight", interval=1, backupCount=30
)
acciones_handler.setFormatter(logging.Formatter("%(asctime)s - %(message)s"))

acciones_logger.addHandler(acciones_handler)

def log_accion(usuario, mensaje):
    acciones_logger.info(f"{usuario} - {mensaje}")
