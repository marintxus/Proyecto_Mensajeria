import os
import sys
import json
import getpass
import bcrypt
from pathlib import Path
import hashlib

# === CONFIGURACIÓN ===
USUARIOS_PATH = Path(__file__).parent / "datos" / "usuarios.json"
CLAVE_PATH = Path(__file__).parent / "datos" / "clave_secreta.txt"
SERVICIO = "gunicorn_websocket"

def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verificar_password(password, hash_almacenado):
    return bcrypt.checkpw(password.encode(), hash_almacenado.encode())

def hash_sha256(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verificar_contraseña_admin():
    if not USUARIOS_PATH.exists():
        print("❌ Archivo de usuarios no encontrado.")
        sys.exit(1)

    with open(USUARIOS_PATH, "r", encoding="utf-8") as f:
        usuarios = json.load(f)

    admin = next((u for u in usuarios if u.get("usuario") == "admin"), None)
    if not admin:
        print("❌ No existe el usuario 'admin'.")
        sys.exit(1)

    for intento in range(3):
        clave = getpass.getpass("Introduce la contraseña de admin: ")
        if verificar_password(clave, admin["hash"]):
            return True
        else:
            print("❌ Contraseña incorrecta.")
    print("🚫 Demasiados intentos fallidos.")
    return False

def reiniciar_servicio():
    os.system(f"sudo systemctl restart {SERVICIO}")
    print("🔄 Servicio reiniciado.")

def parar_servicio():
    os.system(f"sudo systemctl stop {SERVICIO}")
    print("⏹️ Servicio detenido.")

def arrancar_servicio():
    os.system(f"sudo systemctl start {SERVICIO}")
    print("▶️ Servicio arrancado.")

def cambiar_contraseña_admin():
    with open(CLAVE_PATH, "r+", encoding="utf-8") as f:
        usuarios = json.load(f)

        admin = next((u for u in usuarios if u.get("usuario") == "admin"), None)
        if not admin:
            print("❌ Usuario admin no encontrado.")
            return

        nueva = getpass.getpass("Introduce la nueva contraseña para 'admin': ")
        repetir = getpass.getpass("Repite la nueva contraseña: ")

        if nueva != repetir:
            print("❌ Las contraseñas no coinciden.")
            return

        admin["hash"] = hash_password(nueva)
        f.seek(0)
        json.dump(usuarios, f, indent=4)
        f.truncate()
        print("✅ Contraseña del admin actualizada correctamente.")

def estado_servicio():
    print("📄 Estado del servicio:\n")
    os.system(f"systemctl status {SERVICIO} --no-pager")

def cambiar_clave_clientes():
    print("⚠️ Esta acción actualizará la clave de acceso de TODOS los clientes.")
    confirmar1 = input("¿Estás seguro? (s/n): ").strip().lower()
    if confirmar1 != "s":
        print("❌ Cancelado.")
        return
    confirmar2 = input("⚠️ Esto requiere reconfigurar todos los clientes. ¿Continuar? (s/n): ").strip().lower()
    if confirmar2 != "s":
        print("❌ Cancelado.")
        return

    clave = getpass.getpass("Introduce la nueva clave de acceso: ")
    repetir = getpass.getpass("Repite la nueva clave: ")

    if clave != repetir:
        print("❌ Las claves no coinciden.")
        return

    hash_clave = hashlib.sha256(clave.encode()).hexdigest()

    with open("clave_secreta.txt", "w", encoding="utf-8") as f:
        f.write(hash_clave + "\n")

    print("✅ Clave global actualizada correctamente.")

# === MENÚ ===
def mostrar_menu():
    while True:
        print("\n📋 Opciones disponibles:")
        print("1. Reiniciar servicio")
        print("2. Parar servicio")
        print("3. Arrancar servicio")
        print("4. Cambiar contraseña del admin")
        print("5. Cambiar clave de acceso de los clientes")
        print("6. Ver estado del servicio")
        print("0. Salir")

        opcion = input("Selecciona una opción: ").strip()
        if opcion == "1":
            reiniciar_servicio()
        elif opcion == "2":
            parar_servicio()
        elif opcion == "3":
            arrancar_servicio()
        elif opcion == "4":
            cambiar_contraseña_admin()
        elif opcion == "5":
            cambiar_clave_clientes()
        elif opcion == "6":
            estado_servicio()
        elif opcion == "0":
            print("👋 Cerrando el panel.")
            break
        else:
            print("❌ Opción no válida.")

# === EJECUCIÓN PRINCIPAL ===
if __name__ == "__main__":
    print("🔒 Acceso local permitido.")
    mostrar_menu()
