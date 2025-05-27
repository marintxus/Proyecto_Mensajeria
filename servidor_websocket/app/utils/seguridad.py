import os
import logging
import bcrypt
from app.utils.archivos import cargar_usuarios

CLAVE_FILE = "datos/clave_secreta.txt"

def cargar_clave_correcta():
    if os.path.exists(CLAVE_FILE):
        with open(CLAVE_FILE, "r") as f:
            return f.read().strip()
    logging.critical("❌ No se encontró el archivo 'clave_secreta.txt'. El servidor NO puede arrancar sin él.")
    exit(1)


def usuario_valido(usuario, contrasena):
    usuario = usuario.strip().lower()
    for entry in cargar_usuarios():
        if entry["usuario"].lower() == usuario:
            return bcrypt.checkpw(contrasena.encode(), entry["hash"].encode())
    return False
