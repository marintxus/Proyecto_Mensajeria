import json
import logging
from datetime import datetime
from websockets.exceptions import ConnectionClosedOK

from app import clientes_conectados, historial_clientes
from app.globals import CLAVE_CORRECTA_HASH
from app.utils.archivos import guardar_historial


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
            if not isinstance(datos, dict):
                raise ValueError("Mensaje no es un diccionario")
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

        historial_clientes[client_id] = {
            "nombre": nombre,
            "ultima_conexion": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        guardar_historial(historial_clientes)
        notificar_actualizacion(clientes_conectados, historial_clientes, forzar=True)
        logging.info(f"❌ {nombre} ({ip}) se ha desconectado.")


def construir_estado_clientes(clientes_conectados, historial_clientes):
    conectados = []
    desconectados = []

    for client_id, info in clientes_conectados.items():
        nombre = info.get("nombre", client_id)
        ultima = info.get("ultima_conexion", "?")
        conectados.append({
            "id": client_id,
            "nombre": nombre,
            "ultima_conexion": ultima
        })

    for client_id, datos in historial_clientes.items():
        if client_id not in clientes_conectados:
            desconectados.append({
                "id": client_id,
                "nombre": datos.get("nombre", client_id),
                "ultima_conexion": datos.get("ultima_conexion", "?")
            })

    return {
        "conectados": conectados,
        "desconectados": desconectados
    }


def notificar_actualizacion(clientes_conectados, historial_clientes, forzar=False):
    from app import socketio
    estado = construir_estado_clientes(clientes_conectados, historial_clientes)
    socketio.emit("actualizacion_estado", estado)
    logging.info(f"🔄 Notificando actualización: {len(estado['conectados'])} conectados, {len(estado['desconectados'])} desconectados")


# 🔁 Bucle periódico de actualización automática
import asyncio

async def bucle_actualizaciones():
    while True:
        notificar_actualizacion(clientes_conectados, historial_clientes)
        await asyncio.sleep(60)
