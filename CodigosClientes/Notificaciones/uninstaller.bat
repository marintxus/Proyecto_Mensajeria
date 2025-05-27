@echo off
setlocal EnableDelayedExpansion

set "CLIENTE_DIR=%APPDATA%\ClienteNotificaciones"
set "SHORTCUT_PATH=%USERPROFILE%\Desktop\ClienteFarmacia.lnk"
set "LOGFILE=%TEMP%\uninstall_cliente_log.txt"
set "PID_FILE=%CLIENTE_DIR%\instance.lock"

echo [%date% %time%] Iniciando desinstalación... > "%LOGFILE%"

:: 1. Eliminar tareas programadas
echo Eliminando tareas programadas... >> "%LOGFILE%"
schtasks /delete /tn "ClienteFarmacia" /f >> "%LOGFILE%" 2>&1
schtasks /delete /tn "ClienteFarmacia_Prelaunch" /f >> "%LOGFILE%" 2>&1

:: 2. Cerrar el cliente si está activo
if exist "%PID_FILE%" (
    set /p PID=<"%PID_FILE%"
    echo Matando proceso con PID !PID! >> "%LOGFILE%"
    taskkill /PID !PID! /F >nul 2>> "%LOGFILE%"
    del "%PID_FILE%" >nul 2>> "%LOGFILE%"
) else (
    echo No se encontró archivo de PID. Buscando proceso pythonw.exe... >> "%LOGFILE%"
    for /f "tokens=2 delims=," %%a in ('tasklist /FI "IMAGENAME eq pythonw.exe" /FO CSV /NH') do (
        echo Intentando matar proceso %%a >> "%LOGFILE%"
        taskkill /PID %%a /F >nul 2>> "%LOGFILE%"
    )
)

:: 3. Eliminar acceso directo
if exist "%SHORTCUT_PATH%" (
    echo Eliminando acceso directo... >> "%LOGFILE%"
    del "%SHORTCUT_PATH%" >> "%LOGFILE%" 2>&1
) else (
    echo Acceso directo no encontrado. >> "%LOGFILE%"
)

:: 4. Esperar un momento para liberar archivos
timeout /t 2 >nul

:: 5. Eliminar carpeta del cliente
if exist "%CLIENTE_DIR%" (
    echo Eliminando carpeta del cliente... >> "%LOGFILE%"
    rmdir /s /q "%CLIENTE_DIR%" >> "%LOGFILE%" 2>&1
) else (
    echo Carpeta de cliente no encontrada. >> "%LOGFILE%"
)

echo [%date% %time%] ✅ Desinstalación completada. >> "%LOGFILE%"
echo Cliente desinstalado correctamente.
echo Puedes consultar el log aquí: %LOGFILE%
pause
