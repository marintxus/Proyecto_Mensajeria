from flask import Blueprint, render_template, session, jsonify, redirect, send_from_directory, flash, render_template
from app.globals import clientes_conectados, historial_clientes
from app.utils.helpers import construir_estado_clientes

main_bp = Blueprint("main", __name__)

@main_bp.route("/")
def index():
    # ⚠️ Cada vez que se accede, borra la sesión
    session.pop("usuario", None)
    session.pop("acceso_admin", None)
    return render_template("index.html")


@main_bp.route("/usuario_actual")
def usuario_actual():
    return jsonify({"usuario": session.get("usuario")})

@main_bp.route("/verificar_sesion")
def verificar_sesion():
    return jsonify({"logueado": bool(session.get("usuario"))})

@main_bp.route("/estado_clientes")
def estado_clientes():
    if not session.get("usuario"):
        return jsonify({"error": "No autorizado"}), 403

    estado = construir_estado_clientes(clientes_conectados, historial_clientes)
    return jsonify(estado)

from flask import current_app

@main_bp.route("/favicon.ico")
def favicon():
    return send_from_directory(
        current_app.static_folder,
        "favicon.ico",
        mimetype="image/vnd.microsoft.icon"
    )
