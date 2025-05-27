import asyncio
import json
import logging
from app import clientes_conectados, historial_clientes
from app.utils.logger import log_accion

async def broadcast_message(mensaje, destino=None, emisor="sistema"):
    payload = json.dumps({"action": "notify", "message": mensaje})
    destinatarios = []

    if destino and destino != "GLOBAL":
        info = clientes_conectados.get(destino)
        ws = info["ws"] if info else None
        if ws:
            try:
                await ws.send(payload)
                nombre = historial_clientes.get(destino, {}).get("nombre", destino)
                destinatarios.append(nombre)
                logging.info(f"✅ Mensaje enviado a {destino}")
            except Exception as e:
                logging.error(f"❌ Error al enviar a {destino}: {e}")
    else:
        for client_id, info in list(clientes_conectados.items()):
            ws = info.get("ws")
            if not ws:
                continue
            try:
                await ws.send(payload)
                nombre = historial_clientes.get(client_id, {}).get("nombre", client_id)
                destinatarios.append(nombre)
                logging.info(f"✅ Mensaje enviado a {client_id}")
            except Exception as e:
                logging.error(f"❌ Error al enviar a {client_id}: {e}")

    # Registrar en log de acciones
    if destino == "GLOBAL" or not destino:
        if destinatarios:
            log_accion(emisor, f"envía mensaje global: '{mensaje}' → destinatarios reales: {', '.join(destinatarios)}")
        else:
            log_accion(emisor, f"envía mensaje global: '{mensaje}' → ❌ no había clientes conectados")
    elif destinatarios:
        log_accion(emisor, f"envía mensaje a {destinatarios[0]}: '{mensaje}'")
    else:
        log_accion(emisor, f"intentó enviar mensaje a {destino}, pero no se entregó: '{mensaje}'")

def broadcast_wrapper(mensaje, destino, emisor):
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    loop.create_task(broadcast_message(mensaje, destino, emisor))
