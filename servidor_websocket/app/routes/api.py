from flask import Blueprint, request, jsonify, session
from app.utils.seguridad import usuario_valido
from app.utils.logger import log_accion
from app.utils.archivos import (
    guardar_historial, guardar_grupos, cargar_frases,
    guardar_frases, cargar_usuarios, cargar_grupos, importar_grupos_csv
)
from app.utils.helpers import construir_estado_clientes
# from app.routes.websocket import clientes_conectados_por_nombre
from app.broadcast import broadcast_wrapper
from app import socketio
from app.globals import clientes_conectados, historial_clientes, grupos
import asyncio
import json
import logging
import os
from werkzeug.utils import secure_filename
import logging
from threading import Thread

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
api_bp = Blueprint("api", __name__, url_prefix="/api")


@api_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    usuario = data.get("usuario", "").strip().lower()
    contrasena = data.get("contrasena", "")

    if usuario_valido(usuario, contrasena):
        session["usuario"] = usuario
        if usuario == "admin":
            session["acceso_admin"] = True
        if usuario != "admin":
            log_accion(usuario, "ha iniciado sesión")
        return jsonify({"status": "ok"})

    return jsonify({"status": "error", "message": "Credenciales incorrectas"}), 401


@api_bp.route("/logout", methods=["POST"])
def logout():
    usuario = session.get("usuario")
    session.pop("usuario", None)
    session.pop("acceso_admin", None)
    if usuario != "admin":
        log_accion(usuario, "ha cerrado sesión")
    return jsonify({"status": "ok"})


@api_bp.route("/enviar_mensaje", methods=["POST"])
def enviar_mensaje():
    if not session.get("usuario"):
        return jsonify({"status": "error", "message": "No autorizado"}), 403

    data = request.get_json()
    mensaje = data.get("mensaje", "")
    destino = data.get("destino")
    emisor = session.get("usuario", "sistema")

    # ✅ Registrar la acción antes de enviar
    if destino == "GLOBAL" or not destino:
        log_accion(emisor, f"envió mensaje global: '{mensaje}'")
    else:
        log_accion(emisor, f"envió mensaje a {destino}: '{mensaje}'")

    socketio.start_background_task(broadcast_wrapper, mensaje, destino, emisor)
    return jsonify({"status": "ok"})

@api_bp.route("/eliminar_cliente", methods=["POST"])
def eliminar_cliente():
    if not session.get("usuario"):
        return jsonify({"status": "error", "message": "No autorizado"}), 403

    data = request.get_json()
    client_id = data.get("id")
    if client_id in historial_clientes:
        del historial_clientes[client_id]
        guardar_historial(historial_clientes)
        log_accion(session["usuario"], f"elimina cliente del historial: {client_id}")
        return jsonify({"status": "ok"})

    return jsonify({"status": "error", "message": "Cliente no encontrado"}), 404

@api_bp.route("/grupos", methods=["GET"])
def obtener_grupos():
    if not session.get("usuario"):
        return jsonify([])

    grupos_actualizados = cargar_grupos()
    return jsonify([
        {"nombre": nombre, "miembros": miembros}
        for nombre, miembros in grupos_actualizados.items()
    ])

@api_bp.route("/crear_grupo", methods=["POST"])
def crear_grupo():
    if not session.get("usuario"):
        return jsonify({"status": "error", "message": "No autorizado"}), 403

    data = request.get_json()
    nombre = data.get("nombre", "").strip()
    miembros = [m.strip() for m in data.get("miembros", []) if m.strip()]

    if not nombre:
        return jsonify({"status": "error", "message": "Falta el nombre del grupo"}), 400

    nombre_normalizado = nombre.lower()
    if nombre_normalizado in [g.lower() for g in grupos]:
        return jsonify({"status": "error", "message": f"Ya existe un grupo llamado '{nombre}'"}), 400

    # ✅ Validar duplicados dentro del grupo
    vistos = set()
    for m in miembros:
        if m.lower() in vistos:
            return jsonify({"status": "error", "message": f"Usuario repetido: '{m}'"}), 400
        vistos.add(m.lower())

    # ✅ Validar que existan (como ya tenías)
    miembros_validos = set(v["nombre"] for v in historial_clientes.values())
    no_validos = [m for m in miembros if m not in miembros_validos]
    if no_validos:
        return jsonify({"status": "error", "message": f"Usuarios no válidos: {', '.join(no_validos)}"}), 400

    grupos[nombre] = miembros
    guardar_grupos(grupos)
    log_accion(session["usuario"], f"crea grupo: {nombre} con miembros {miembros}")
    return jsonify({"status": "ok"})

@api_bp.route("/info_grupo_detallado")
def info_grupo_detallado():
    nombre = request.args.get("nombre", "").strip().lower()
    if not nombre:
        return jsonify({"error": "Nombre de grupo no especificado"}), 400

    ruta = os.path.join(BASE_DIR, "datos", "grupos.json")
    if not os.path.exists(ruta):
        return jsonify({"error": "No hay grupos disponibles"}), 404

    with open(ruta, "r", encoding="utf-8") as f:
        grupos = json.load(f)

    miembros = grupos.get(nombre)
    if not miembros:
        return jsonify({"error": "Grupo no encontrado"}), 404

    from app.utils.archivos import historial_clientes, clientes_conectados  # asegúrate de importar esto

    lista = []
    for m in miembros:
        m_limpio = m.strip().lower()
        if m_limpio in clientes_conectados:
            lista.append({"nombre": m, "estado": "conectado", "ultima_conexion": historial_clientes.get(m_limpio, "")})
        elif m_limpio in historial_clientes:
            lista.append({"nombre": m, "estado": "desconectado", "ultima_conexion": historial_clientes[m_limpio]})
        else:
            lista.append({"nombre": m, "estado": "no_existe", "ultima_conexion": None})

    return jsonify({"nombre": nombre, "miembros": lista})

@api_bp.route("/editar_grupo", methods=["POST"])
def editar_grupo():
    if not session.get("usuario"):
        return jsonify({"status": "error", "message": "No autorizado"}), 403

    data = request.get_json()
    nombre_actual = data.get("nombre_actual", "").strip()
    nuevo_nombre = data.get("nuevo_nombre", "").strip()
    nuevos_miembros = [m.strip() for m in data.get("miembros", []) if m.strip()]

    # 🔍 Buscar grupo real ignorando mayúsculas
    grupo_real = next((g for g in grupos if g.lower() == nombre_actual.lower()), None)
    if not grupo_real:
        return jsonify({"status": "error", "message": "Grupo no encontrado"}), 404

    # 🚫 Validar duplicados dentro del grupo
    vistos = set()
    for m in nuevos_miembros:
        if m.lower() in vistos:
            return jsonify({"status": "error", "message": f"Usuario repetido: '{m}'"}), 400
        vistos.add(m.lower())

    # ✅ Dejamos pasar usuarios aunque no existan todavía
    miembros_validos = set(v["nombre"] for v in historial_clientes.values())
    no_validos = [m for m in nuevos_miembros if m not in miembros_validos]

    if no_validos:
        logging.info(f"⚠️ Usuarios añadidos que aún no existen: {no_validos}")
        # Los aceptamos igualmente

    # ✏️ Si cambia el nombre del grupo
    if nuevo_nombre and nuevo_nombre != grupo_real:
        nuevo_nombre_normalizado = nuevo_nombre.lower()
        nombres_existentes = [g.lower() for g in grupos if g.lower() != grupo_real.lower()]
        if nuevo_nombre_normalizado in nombres_existentes:
            return jsonify({"status": "error", "message": f"Ya existe un grupo llamado '{nuevo_nombre}'"}), 400
        grupos[nuevo_nombre] = nuevos_miembros
        del grupos[grupo_real]
        log_accion(session["usuario"], f"renombra grupo: {grupo_real} → {nuevo_nombre}")
    else:
        grupos[grupo_real] = nuevos_miembros
        log_accion(session["usuario"], f"edita grupo: {grupo_real} nuevos miembros {nuevos_miembros}")

    guardar_grupos(grupos)
    return jsonify({"status": "ok"})

@api_bp.route("/eliminar_grupo", methods=["POST"])
def eliminar_grupo():
    if not session.get("usuario"):
        return jsonify({"status": "error", "message": "No autorizado"}), 403

    data = request.get_json()
    nombre = data.get("nombre", "").strip().lower()

    for g in list(grupos):
        if g.lower() == nombre:
            del grupos[g]
            guardar_grupos(grupos)
            log_accion(session["usuario"], f"elimina grupo: {g}")
            return jsonify({"status": "ok"})

    return jsonify({"status": "error", "message": "Grupo no encontrado"}), 404

from flask import request, session, jsonify
import json

@api_bp.route("/enviar_grupo", methods=["POST"])
def enviar_a_grupo():
    if not session.get("usuario"):
        return jsonify({"status": "error", "message": "No autorizado"}), 403

    data = request.get_json()
    grupo = data.get("grupo")
    mensaje = data.get("mensaje", "")
    emisor = session.get("usuario", "sistema")

    if grupo not in grupos:
        return jsonify({"status": "error", "message": "Grupo no encontrado"}), 404

    miembros = grupos[grupo]

    async def proceso_envio():
        destinatarios_reales = []
        for miembro in miembros:
            nombre = miembro.strip().lower()
            client_id = next((cid for cid, info in historial_clientes.items()
                              if info["nombre"].strip().lower() == nombre), None)
            if client_id:
                ws = clientes_conectados.get(client_id, {}).get("ws")
                if ws:
                    try:
                        await ws.send(json.dumps({"action": "notify", "message": mensaje}))
                        logging.info(f"✅ Mensaje enviado a '{nombre}'")
                        destinatarios_reales.append(historial_clientes[client_id]["nombre"])
                    except Exception as e:
                        logging.warning(f"❌ Error al enviar a '{nombre}': {e}")
                else:
                    logging.warning(f"❌ Cliente '{nombre}' no conectado")
            else:
                logging.warning(f"❌ Cliente '{nombre}' no encontrado en historial")

        log_accion(emisor, f"envió mensaje a grupo {grupo}: '{mensaje}' → destinatarios reales: {', '.join(destinatarios_reales)}")

    asyncio.get_event_loop().create_task(proceso_envio())
    return jsonify({"status": "ok"})

@api_bp.route("/info_grupo", methods=["GET"])
def info_grupo():
    if not session.get("usuario"):
        return jsonify({"status": "error", "message": "No autorizado"}), 403

    nombre_grupo = request.args.get("nombre", "").strip().lower()
    grupo_real = next((g for g in grupos if g.lower() == nombre_grupo), None)
    if not grupo_real:
        return jsonify({"status": "error", "message": "Grupo no encontrado"}), 404

    miembros_info = []

    for nombre_miembro in grupos[grupo_real]:
        nombre_miembro_limpio = nombre_miembro.strip().lower()
        encontrado = False
        conectado = False
        ultima_conexion = None

        # Recorremos el historial buscando coincidencia real por nombre (ignorando ID)
        for client_data in historial_clientes.values():
            if client_data["nombre"].strip().lower() == nombre_miembro_limpio:
                encontrado = True
                ultima_conexion = client_data.get("ultima_conexion", None)
                break  # ya está, lo encontramos

        # Si está conectado, su client_id estará en clientes_conectados
        for client_id, client_ws in clientes_conectados.items():
            client_name = historial_clientes.get(client_id, {}).get("nombre", "").strip().lower()
            if client_name == nombre_miembro_limpio:
                conectado = True
                break

        estado = "conectado" if conectado else "desconectado" if encontrado else "no_existe"

        miembros_info.append({
            "nombre": nombre_miembro,
            "estado": estado,
            "ultima_conexion": ultima_conexion
        })

    return jsonify({"nombre": grupo_real, "miembros": miembros_info})

@api_bp.route("/frases", methods=["GET"])
def obtener_frases():
    if not session.get("usuario"):
        return jsonify([])
    return jsonify(cargar_frases())

@api_bp.route("/frases", methods=["POST"])
def actualizar_frases():
    if not session.get("usuario"):
        return jsonify({"status": "error", "message": "No autorizado"}), 403

    data = request.get_json()
    frases = data.get("frases", [])

    # 🔍 Limpiar frases vacías y duplicadas (ignorando mayúsculas)
    frases_limpias = []
    vistas = set()
    for f in frases:
        limpia = f.strip()
        if limpia and limpia.lower() not in vistas:
            frases_limpias.append(limpia)
            vistas.add(limpia.lower())

    guardar_frases(frases_limpias)
    log_accion(session["usuario"], "actualizó las frases predefinidas (limpieza aplicada)")
    return jsonify({"status": "ok"})

@api_bp.route("/estado_clientes", methods=["GET"])
def estado_clientes():
    if not session.get("usuario"):
        return jsonify({"error": "No autorizado"}), 401

    try:
        estado = construir_estado_clientes(clientes_conectados, historial_clientes)
        return jsonify(estado)
    except Exception as e:
        import traceback
        print("❌ Error en /estado_clientes:\n", traceback.format_exc())
        return jsonify({
            "conectados": [],
            "desconectados": [],
            "error": "Error interno en el servidor"
        }), 500

@api_bp.route("/importar_csv_grupos", methods=["POST"])
def importar_csv_grupos():
    if not session.get("usuario") or session.get("usuario") != "admin":
        return jsonify({"status": "error", "message": "No autorizado"}), 403

    if "archivo" not in request.files:
        return jsonify({"status": "error", "message": "Falta archivo CSV"}), 400

    archivo = request.files["archivo"]
    if archivo.filename == "":
        return jsonify({"status": "error", "message": "Archivo vacío"}), 400

    filename = secure_filename(archivo.filename)
    ruta_temporal = os.path.join("/tmp", filename)
    archivo.save(ruta_temporal)

    try:
        mensaje = importar_grupos_csv(ruta_temporal)
        os.remove(ruta_temporal)
        log_accion("admin", f"importó grupos desde CSV: {filename}")
        return jsonify({"status": "ok", "mensaje": mensaje})
    except Exception as e:
        os.remove(ruta_temporal)
        return jsonify({"status": "error", "message": str(e)}), 400
