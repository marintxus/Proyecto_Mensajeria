@echo off
setlocal EnableDelayedExpansion

:: === CONFIGURACIÓN DE RUTAS ===
set "CLIENTE_DIR=%APPDATA%\ClienteNotificaciones"
set "PYTHON_EXE=%CLIENTE_DIR%\venv\Scripts\pythonw.exe"
set "PYTHON_PIP=%CLIENTE_DIR%\venv\Scripts\python.exe"
set "CLIENT_PY=%CLIENTE_DIR%\cliente.py"
set "LIMPIADOR_BAT=%CLIENTE_DIR%\limpiador.bat"
set "LOGFILE=%CLIENTE_DIR%\install_log.txt"
set "SHORTCUT_PATH=%USERPROFILE%\Desktop\ClienteFarmacia.lnk"

:: === CREAR DIRECTORIO ===
if not exist "%CLIENTE_DIR%" mkdir "%CLIENTE_DIR%"
echo [%date% %time%] Instalación iniciada > "%LOGFILE%"

:: === PEDIR DATOS ===
set /p CLIENTE="Introduce el nombre del cliente (sin espacios): "
set /p CLAVE="Introduce la clave secreta: "

:: Guardar nombre en config.txt (clave se añadirá luego)
echo Usuario=%CLIENTE%> "%CLIENTE_DIR%\config.txt"

:: === CREAR ENTORNO VIRTUAL ===
echo [INFO] Creando entorno virtual... >> "%LOGFILE%"
python -m venv "%CLIENTE_DIR%\venv"
if errorlevel 1 (
    echo [ERROR] No se pudo crear el entorno virtual >> "%LOGFILE%"
    pause
    exit /b 1
)

:: === INSTALAR DEPENDENCIAS ===
echo [INFO] Instalando dependencias... >> "%LOGFILE%"
"%PYTHON_PIP%" -m pip install --upgrade pip >> "%LOGFILE%" 2>&1
"%PYTHON_PIP%" -m pip install websocket-client pystray pillow plyer psutil >> "%LOGFILE%" 2>&1

:: === COPIAR cliente.py ===
echo [INFO] Copiando cliente.py >> "%LOGFILE%"
copy /Y "%~dp0cliente.py" "%CLIENT_PY%" >> "%LOGFILE%" 2>&1

:: === COPIAR limpiador.bat ===
echo [INFO] Copiando limpiador.bat >> "%LOGFILE%"
copy /Y "%~dp0limpiador.bat" "%LIMPIADOR_BAT%" >> "%LOGFILE%" 2>&1

:: === CALCULAR HASH Y GUARDAR CLAVE ===
echo import hashlib > "%CLIENTE_DIR%\tmp_hash.py"
echo clave = "%CLAVE%" >> "%CLIENTE_DIR%\tmp_hash.py"
echo hash = hashlib.sha256(clave.encode()).hexdigest() >> "%CLIENTE_DIR%\tmp_hash.py"
echo with open(r"%CLIENTE_DIR%\config.txt", "a", encoding="utf-8") as f: f.write("Clave=" + hash + "\n") >> "%CLIENTE_DIR%\tmp_hash.py"

"%PYTHON_PIP%" "%CLIENTE_DIR%\tmp_hash.py"
del "%CLIENTE_DIR%\tmp_hash.py"

:: === CREAR TAREA: LIMPIADOR ===
echo [INFO] Registrando tarea ClienteFarmacia_Prelaunch >> "%LOGFILE%"
schtasks /delete /tn "ClienteFarmacia_Prelaunch" /f >nul 2>&1
schtasks /create /tn "ClienteFarmacia_Prelaunch" ^
  /tr "\"%LIMPIADOR_BAT%\"" ^
  /sc onlogon /rl highest /f >> "%LOGFILE%" 2>&1

:: === CREAR TAREA: CLIENTE (w/ delay) ===
echo [INFO] Registrando tarea ClienteFarmacia (con retardo) >> "%LOGFILE%"
schtasks /delete /tn "ClienteFarmacia" /f >nul 2>&1
schtasks /create /tn "ClienteFarmacia" ^
  /tr "\"%PYTHON_EXE%\" \"%CLIENT_PY%\"" ^
  /sc onlogon /delay 0001:0/rl highest /f >> "%LOGFILE%" 2>&1

:: === CREAR ACCESO DIRECTO EN ESCRITORIO ===
:: echo [INFO] Creando acceso directo >> "%LOGFILE%"
:: powershell -NoProfile -ExecutionPolicy Bypass -Command "$s=(New-Object -ComObject WScript.Shell).CreateShortcut('%SHORTCUT_PATH%');$s.TargetPath='%PYTHON_EXE%';$s.Arguments='\"%CLIENT_PY%\"';$s.IconLocation='%SystemRoot%\\System32\\shell32.dll,1';$s.Save()"

:: === EJECUTAR LIMPIADOR UNA VEZ ===
call "%LIMPIADOR_BAT%"

:: === FIN ===
echo [INFO] Instalación completada correctamente >> "%LOGFILE%"
echo ✅ Cliente instalado. Puedes reiniciar o ejecutar desde el acceso directo.
pause
