# 🧠 Proyecto: Panel de Notificaciones en Tiempo Real

## 📍 Descripción general

Este sistema permite a un grupo de técnicos enviar mensajes **en tiempo real** a clientes conectados mediante WebSockets. Está desarrollado con **Flask** y **WebSockets**, incluye una interfaz web profesional y cuenta con panel de administración, logs de actividad, seguridad robusta y gestión completa de usuarios, grupos y frases.

## 🚀 Tecnologías usadas

- **Backend**: Python 3, Flask, WebSockets, Flask-SocketIO
- **Frontend**: HTML5, CSS3, JavaScript moderno (sin frameworks), Bootstrap Icons
- **Seguridad**:
  - Login con contraseñas cifradas (`bcrypt`)
  - Certificado SSL propio (HTTPS/WSS)
  - Protección de rutas por sesión
  - Clave secreta SHA-256 en clientes
- **Persistencia**: Archivos `.json` y `.log`
- **Sistema operativo objetivo**: Ubuntu 22.04+

## 🧠 Funcionalidades principales

### ✅ Para usuarios normales (`index.html`)

- Login visual seguro con modal
- Ver clientes conectados / desconectados
- Enviar mensajes:
  - Globales
  - Privados
  - A grupos
- Gestión de frases predefinidas
- Gestión visual de grupos (crear, editar, borrar, info)
- Atajos de teclado: **Enter** confirma / **Escape** cancela
- Animación de carga inicial

### 🔐 Panel de administración (`/admin`)

- Acceso exclusivo para `admin`
- Crear, editar y eliminar usuarios (excepto admin)
- Ver logs filtrados por fecha, usuario o texto
- Ver destinatarios reales de cada mensaje enviado
- Redirección segura: no se puede acceder escribiendo la URL

### 🧾 Sistema de logs

- Logs diarios rotados automáticamente: `acciones.log`, `acciones.log.YYYY-MM-DD`
- Registro detallado de:
  - Login/logout
  - Mensajes enviados (globales, privados, grupos)
  - Gestión de usuarios
  - Cambios de sesión

## 📁 Estructura del proyecto

```
servidor_websocket/
├── app/
│   ├── __init__.py
│   ├── routes/
│   │   ├── main.py
│   │   ├── api.py
│   │   └── admin.py
│   ├── utils/
│   │   ├── seguridad.py
│   │   ├── gestion_json.py
│   │   ├── logs.py
│   │   └── helpers.py
│   └── websocket_server.py
├── static/
│   ├── style.css
│   ├── script.js
│   └── admin.js
├── templates/
│   ├── index.html
│   └── admin.html
├── datos/
│   ├── usuarios.json
│   ├── frases.json
│   ├── grupos.json
│   └── historial_clientes.json
├── logs/
│   └── acciones.log
├── cert.pem / key.pem
├── servidor.py
├── websocket.service
└── README.md
```

## 🖥️ Como servicio (opcional)

```bash
sudo cp websocket.service /etc/systemd/system/
sudo systemctl daemon-reexec
sudo systemctl enable websocket.service
sudo systemctl start websocket.service
```

## 👤 Usuario por defecto

```json
{
  "admin": "$2b$12$.... (bcrypt hash)"
}
```

> ⚠️ `admin` no puede ser eliminado ni editado desde la web

## 🔐 Seguridad avanzada

- Sesiones no persistentes (requiere login en cada pestaña)
- Control total desde backend: sin acceso sin login válido
- Clientes WebSocket validados con clave hash SHA-256
- Servidor protegido con SSL y reconexión automática

## 📌 Mejoras futuras

- Descarga de logs por fecha (botón)
- Importación de grupos desde CSV
- Ejecución con Gunicorn 