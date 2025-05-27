import app.utils.logger  # 🔥 Activa la configuración del logger

from app import app, socketio
from threading import Thread
from app.websocket_server import iniciar_websocket
from app.utils.helpers import bucle_actualizaciones
import asyncio
import logging
logging.info("📢 Servidor iniciado y logger ya configurado.")
# ✅ Función asíncrona que lanza ambos servicios correctamente
async def iniciar_servicios_adicionales():
    asyncio.create_task(bucle_actualizaciones())            # 🔁 Corrección: ahora sí se ejecuta correctamente
    await iniciar_websocket()                               # ✅ Espera a que arranque el servidor WebSocket

# ✅ Lanza todo en un hilo para no bloquear Gunicorn
Thread(target=lambda: asyncio.run(iniciar_servicios_adicionales()), daemon=True).start()

app = app  # ✅ Requisito para que Gunicorn lo reconozca como app callable
