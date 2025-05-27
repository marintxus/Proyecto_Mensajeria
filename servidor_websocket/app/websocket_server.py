import asyncio
import websockets
import ssl
import json
import logging
from datetime import datetime
from websockets.exceptions import ConnectionClosedOK

from app import clientes_conectados, historial_clientes
from app.globals import CLAVE_CORRECTA_HASH
from app.utils.archivos import guardar_historial
from app.utils.helpers import notificar_actualizacion
from app.globals import clientes_conectados_por_nombre  # 👈 Import fuera del handler


async def manejar_cliente(websocket):
    logging.info("🧪 Código ACTUAL de manejar_cliente EJECUTÁNDOSE")
    ip = websocket.remote_address[0]
    client_id = None
    nombre = "Desconocido"

    try:
        mensaje = await websocket.recv()
        logging.info(f"🔁 Recibido mensaje inicial de {ip}: {mensaje}")

        try:
            datos = json.loads(mensaje)
        except Exception as e:
            logging.error(f"❌ Error al parsear JSON de {ip}: {e}")
            await websocket.send(json.dumps({"action": "error", "message": "Mensaje inválido"}))
            await websocket.close()
            return

        if datos.get("action") != "connect":
            logging.warning(f"❌ Acción no válida de {ip}: {datos}")
            await websocket.send(json.dumps({"action": "error", "message": "Acción no válida"}))
            await websocket.close()
            return

        clave_recibida = datos.get("clave", "").strip()
        nombre = datos.get("username", "Desconocido").strip()

        if clave_recibida != CLAVE_CORRECTA_HASH:
            logging.warning(f"❌ Cliente rechazado por clave inválida: {nombre} ({ip})")
            await websocket.send(json.dumps({"action": "error", "message": "Clave incorrecta"}))
            await websocket.close()
            return

        client_id = f"{ip}_{nombre}"

        # Cerrar anterior si ya existía
        if client_id in clientes_conectados:
            try:
                await clientes_conectados[client_id]["ws"].close()
            except:
                pass
            del clientes_conectados[client_id]

        clientes_conectados[client_id] = {
            "ws": websocket,
            "nombre": nombre,
            "ultima_conexion": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        historial_clientes[client_id] = {
            "nombre": nombre,
            "ultima_conexion": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        clientes_conectados_por_nombre[nombre.strip().lower()] = websocket

        guardar_historial(historial_clientes)
        notificar_actualizacion(clientes_conectados, historial_clientes, forzar=True)
        logging.info(f"✅ {nombre} ({ip}) se ha conectado.")

        await websocket.send(json.dumps({
            "action": "welcome",
            "message": f"Conexión aceptada, {nombre}"
        }))

        async for mensaje in websocket:
            logging.info(f"📩 Mensaje de {nombre}: {mensaje}")

    except ConnectionClosedOK:
        logging.info(f"ℹ️ Conexión cerrada correctamente por {nombre} ({ip})")
    except Exception as e:
        logging.error(f"❌ Error con {nombre} ({ip}): {e}")
    finally:
        if client_id and client_id in clientes_conectados:
            del clientes_conectados[client_id]

        if nombre.strip().lower() in clientes_conectados_por_nombre:
            del clientes_conectados_por_nombre[nombre.strip().lower()]

        historial_clientes[client_id] = {
            "nombre": nombre,
            "ultima_conexion": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        guardar_historial(historial_clientes)
        notificar_actualizacion(clientes_conectados, historial_clientes, forzar=True)
        logging.info(f"❌ {nombre} ({ip}) se ha desconectado.")


async def iniciar_websocket():
    ssl_context_ws = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ssl_context_ws.load_cert_chain(certfile="cert.pem", keyfile="key.pem")
    logging.info("🔐 Iniciando servidor WebSocket SEGURO (wss://) en puerto 8765")
    async with websockets.serve(manejar_cliente, "0.0.0.0", 8765, ssl=ssl_context_ws):
        await asyncio.Future()
