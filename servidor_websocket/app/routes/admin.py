from flask import Blueprint, render_template, session, jsonify, request, redirect, flash, current_app, send_file
from app.utils.archivos import cargar_usuarios, guardar_usuarios
from app.utils.logger import log_accion
import json
import logging
import bcrypt
import os 
from datetime import datetime

admin_bp = Blueprint("admin", __name__)
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
LOGS_DIR = os.path.join(BASE_DIR, "logs")
@admin_bp.route("/")
def admin_panel():
    if session.get("usuario") == "admin" and session.get("acceso_admin"):
        # ✅ Solo se permite si ha venido de un login limpio
        session.pop("acceso_admin", None)  # Esto hace que solo dure 1 vez
        return render_template("admin.html")

    # ❌ Cualquier otra forma de llegar aquí → lo echamos fuera
    session.pop("usuario", None)
    session.pop("acceso_admin", None)
    flash("⚠️ Por seguridad, debes iniciar sesión nuevamente.")
    return redirect("/")

@admin_bp.route("/usuarios")
def listar_usuarios():
    if session.get("usuario") != "admin":
        return jsonify([])
    usuarios = cargar_usuarios()
    lista = [u["usuario"] for u in usuarios if u["usuario"].lower() != "admin"]
    return jsonify(lista)

@admin_bp.route("/eliminar_usuario", methods=["POST"])
def eliminar_usuario():
    if session.get("usuario") != "admin":
        return jsonify({"status": "error", "message": "Acceso denegado"}), 403

    data = request.get_json()
    usuario = data.get("usuario", "").strip().lower()

    if usuario == "admin":
        return jsonify({"status": "error", "message": "No se puede eliminar el admin"}), 400

    usuarios = cargar_usuarios()
    usuarios = [u for u in usuarios if u["usuario"].lower() != usuario]
    guardar_usuarios(usuarios)

    log_accion("admin", f"eliminó al usuario {usuario}")
    return jsonify({"status": "ok"})

@admin_bp.route("/crear_usuario", methods=["POST"])
def crear_usuario():
    if session.get("usuario") != "admin":
        return jsonify({"status": "error", "message": "Acceso denegado"}), 403

    data = request.get_json()
    nuevo = data.get("usuario", "").strip().lower()
    contra1 = data.get("contrasena1", "")
    contra2 = data.get("contrasena2", "")

    if not nuevo or not contra1 or not contra2:
        return jsonify({"status": "error", "message": "Campos incompletos"})

    if contra1 != contra2:
        return jsonify({"status": "error", "message": "Las contraseñas no coinciden"})

    usuarios = cargar_usuarios()
    if any(u["usuario"].lower() == nuevo for u in usuarios):
        return jsonify({"status": "error", "message": "Ese usuario ya existe"})

    hash_pwd = bcrypt.hashpw(contra1.encode(), bcrypt.gensalt()).decode()
    usuarios.append({"usuario": nuevo, "hash": hash_pwd})
    guardar_usuarios(usuarios)

    log_accion("admin", f"creó el usuario {nuevo}")
    return jsonify({"status": "ok", "message": "Usuario creado correctamente"})

@admin_bp.route("/cambiar_contrasena", methods=["POST"])
def cambiar_contrasena():
    if session.get("usuario") != "admin":
        return jsonify({"status": "error", "message": "Acceso denegado"}), 403

    data = request.get_json()
    usuario = data.get("usuario", "").strip().lower()
    nueva = data.get("nueva_clave", "")

    if not usuario or not nueva:
        return jsonify({"status": "error", "message": "Campos incompletos"})

    usuarios = cargar_usuarios()
    encontrado = False
    for u in usuarios:
        if u["usuario"].lower() == usuario:
            u["hash"] = bcrypt.hashpw(nueva.encode(), bcrypt.gensalt()).decode()
            encontrado = True
            break

    if not encontrado:
        return jsonify({"status": "error", "message": "Usuario no encontrado"})

    guardar_usuarios(usuarios)
    log_accion("admin", f"cambió la contraseña de {usuario}")
    return jsonify({"status": "ok"})

    # ✅ Arreglo aquí: sin carpeta logs/
logdir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "logs"))

@admin_bp.route("/logs")
def admin_logs():
    if session.get("usuario") != "admin":
        return jsonify([])

    fecha = request.args.get("fecha", "")
    usuario = request.args.get("usuario", "").lower()

    # Ruta absoluta del log
    if fecha:
        logfile = os.path.join(logdir, f"acciones.log.{fecha}")
    else:
        logfile = os.path.join(logdir, "acciones.log")

    try:
        with open(logfile, "r", encoding="utf-8") as f:
            lineas = f.readlines()[-100:]

        logs = []
        for linea in reversed(lineas):
            if fecha and fecha not in linea:
                continue
            if usuario and usuario not in linea.lower():
                continue
            logs.append(linea.strip())

        return jsonify(logs)
    except FileNotFoundError:
        current_app.logger.warning(f"⚠️ Log no encontrado: {logfile}")
        return jsonify([])
    except Exception as e:
        import traceback
        current_app.logger.error(f"❌ Error al leer logs: {e}")
        print(traceback.format_exc())
        return jsonify([])

@admin_bp.route("/descargar_log/<fecha>")
def descargar_log(fecha):
    if session.get("usuario") != "admin":
        return redirect("/")

    if fecha == "hoy":
        filename = "acciones.log"
    else:
        filename = f"acciones.log.{fecha}"

    ruta = os.path.join(LOGS_DIR, filename)  # ✅ RUTA ABSOLUTA

    if not os.path.exists(ruta):
        flash("Archivo no encontrado")
        return redirect("/admin")

    return send_file(ruta, as_attachment=True)

import csv
from flask import request, jsonify

from werkzeug.utils import secure_filename
import tempfile
from app.utils.archivos import importar_grupos_csv

@admin_bp.route("/importar_csv", methods=["POST"])
def importar_csv():
    if session.get("usuario") != "admin":
        return jsonify({"status": "error", "message": "Acceso denegado"}), 403

    archivo = request.files.get("archivo")
    if not archivo or not archivo.filename.endswith(".csv"):
        return jsonify({"status": "error", "message": "Archivo inválido"})

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".csv", mode="w", encoding="utf-8") as tmp:
            contenido = archivo.read().decode("utf-8")
            tmp.write(contenido)
            tmp_path = tmp.name

        resultado = importar_grupos_csv(tmp_path)
        log_accion("admin", resultado.lower())
        return jsonify({"status": "ok", "message": resultado})

    except Exception as e:
        import traceback
        traceback_str = traceback.format_exc()
        current_app.logger.error(f"❌ Error al importar CSV:\n{traceback_str}")
        return jsonify({"status": "error", "message": str(e)})
