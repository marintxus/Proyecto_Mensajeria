import os
from flask import Flask
from flask_socketio import SocketIO
from flask_cors import CORS

# Asegurarse de que Flask encuentra bien las carpetas
base_dir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__,
            template_folder=os.path.join(base_dir, "..", "templates"),
            static_folder=os.path.join(base_dir, "..", "static"))

CORS(app)
app.secret_key = "superclaveultrasecreta"
socketio = SocketIO(app, cors_allowed_origins="*")

# Importar variables globales y cargar datos
from app.globals import clientes_conectados, historial_clientes, grupos
from app.utils.archivos import cargar_historial, cargar_grupos  # ✅ necesario

# ✅ Cargar los datos del historial y grupos al iniciar
historial_clientes.update(cargar_historial())
grupos.update(cargar_grupos())

# Importar rutas
from app.routes.main import main_bp
from app.routes.api import api_bp
from app.routes.admin import admin_bp

app.register_blueprint(main_bp)
app.register_blueprint(api_bp, url_prefix="/api")
app.register_blueprint(admin_bp, url_prefix="/admin")
