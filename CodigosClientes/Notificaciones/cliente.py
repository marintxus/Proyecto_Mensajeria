import os
import sys
import time
import json
import threading
import tkinter as tk
from tkinter import ttk
import subprocess
import websocket
from pystray import Icon, MenuItem as item, Menu
from PIL import Image, ImageDraw
import traceback
import ssl

APP_DIR = os.path.join(os.getenv("APPDATA"), "ClienteNotificaciones")
CONFIG_FILE = os.path.join(APP_DIR, "config.txt")
LOG_FILE = os.path.join(APP_DIR, "log.txt")
LOCK_FILE = os.path.join(APP_DIR, "instance.lock")

USERNAME = "UsuarioDesconocido"
CLAVE_HASH = ""

if os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("Usuario="):
                USERNAME = line.split("=")[1].strip()
            elif line.startswith("Clave="):
                CLAVE_HASH = line.split("=")[1].strip()

SERVER_URL = "wss://172.17.204.80:8765"
tray_icon = None

def log(msg):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{ts}] {msg}\n")

def log_exception(e):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[ERROR] {time.strftime('%Y-%m-%d %H:%M:%S')} - {str(e)}\n")
        f.write(traceback.format_exc() + "\n")

def check_single_instance():
    if os.path.exists(LOCK_FILE):
        log("Ya hay una instancia en ejecución. Abortando.")
        sys.exit(0)
    with open(LOCK_FILE, "w") as f:
        f.write(str(os.getpid()))

def cleanup_lock():
    if os.path.exists(LOCK_FILE):
        os.remove(LOCK_FILE)

class ClienteFarmacia:
    def __init__(self, master):
        self.master = master
        self.master.withdraw()

        self.ws = None
        self.connected = False
        self.tray_icon = None
        self.tray_running = False
        self.create_tray_icon("red")

        threading.Thread(target=self.try_connect_once, daemon=True).start()

    def create_tray_icon(self, color):
        global tray_icon
        if tray_icon and self.tray_running:
            try:
                tray_icon.stop()
                self.tray_running = False
                time.sleep(0.5)
            except:
                pass

        icon = self.generate_circle_icon(color)
        menu = Menu(item("Salir", self.exit_all))
        tray_icon = Icon("ClienteFarmacia", icon, menu=menu)
        threading.Thread(target=self._run_tray_icon, daemon=True).start()

    def _run_tray_icon(self):
        global tray_icon
        self.tray_running = True
        tray_icon.run()

    def generate_circle_icon(self, color):
        size = (64, 64)
        image = Image.new("RGBA", size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(image)
        draw.ellipse((8, 8, 56, 56), fill=(0, 255, 0) if color == "green" else (255, 0, 0))
        return image

    def try_connect_once(self):
        time.sleep(2)
        while True:
            try:
                log(f"Intentando conectar a {SERVER_URL} como {USERNAME}")
                self.ws = websocket.create_connection(
                    SERVER_URL,
                    sslopt={"cert_reqs": ssl.CERT_NONE}
                )
                self.ws.send(json.dumps({
                    "action": "connect",
                    "username": USERNAME,
                    "clave": CLAVE_HASH
                }))
                self.set_connected(True)
                log("Conectado y mensaje enviado.")

                while self.ws.connected:
                    try:
                        msg = self.ws.recv()
                        if not msg.strip():
                            continue
                        log(f"💬 Mensaje recibido en tiempo real: {msg}")
                        self.handle_message(msg)
                    except websocket.WebSocketConnectionClosedException:
                        log("⚠️ Conexión cerrada inesperadamente.")
                        self.set_connected(False)
                        break
                    except Exception as e:
                        log(f"❌ Error en recv(): {e}")
                        break

            except Exception as e:
                log_exception(e)
                self.set_connected(False)

            time.sleep(30)  # Reintento cada 30 seg

    def handle_message(self, raw):
        try:
            data = json.loads(raw)
            if not isinstance(data, dict):
                log("❌ Respuesta no válida: no es un objeto JSON.")
                return

            action = data.get("action")
            if action == "notify":
                mensaje = data.get("message", "")
                self.master.after(0, lambda: self.show_alert(mensaje))
            elif action == "restart":
                self.master.after(0, lambda: self.show_alert("Reinicio en 5 segundos..."))
                time.sleep(2)
                subprocess.Popen(["shutdown", "/r", "/t", "5"])
            elif action == "welcome":
                log("✅ Mensaje de bienvenida recibido correctamente.")
            elif action == "error":
                log(f"⚠️ Error del servidor: {data.get('message')}")
        except Exception as e:
            log(f"❌ Excepción al procesar mensaje: {e}")

    def show_alert(self, msg):
        alert = tk.Toplevel()
        alert.title("Mensaje Urgente")
        alert.attributes("-topmost", True)
        alert.configure(bg="red" if "urgente" in msg.lower() else "white")
        alert.geometry(f"{int(alert.winfo_screenwidth()*0.8)}x{int(alert.winfo_screenheight()*0.8)}+100+100")
        alert.resizable(False, False)

        estilo = {
            "font": ("Segoe UI", 24, "bold"),
            "bg": alert["bg"],
            "fg": "white" if "urgente" in msg.lower() else "black",
            "wraplength": int(alert.winfo_screenwidth()*0.7),
            "justify": "center"
        }

        frame = tk.Frame(alert, bg=alert["bg"])
        frame.pack(expand=True, fill="both", padx=40, pady=40)

        label = tk.Label(frame, text=msg, **estilo)
        label.pack(expand=True)

        cerrar_btn = ttk.Button(frame, text="Cerrar", command=alert.destroy)
        cerrar_btn.pack(pady=20)

        alert.lift()
        alert.grab_set()

    def set_connected(self, state):
        self.connected = state
        self.create_tray_icon("green" if state else "red")

    def exit_all(self, icon=None, item=None):
        if self.ws:
            try:
                self.ws.close()
            except:
                pass
        if tray_icon:
            tray_icon.stop()
        cleanup_lock()
        self.master.destroy()
        sys.exit(0)

def main():
    try:
        check_single_instance()
        root = tk.Tk()
        app = ClienteFarmacia(root)
        root.mainloop()
    except Exception as e:
        log_exception(e)
        cleanup_lock()

if __name__ == "__main__":
    main()
