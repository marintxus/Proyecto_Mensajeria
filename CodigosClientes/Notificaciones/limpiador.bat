@echo off
setlocal
set "LOCKFILE=%APPDATA%\ClienteNotificaciones\instance.lock"

if exist "%LOCKFILE%" (
    del "%LOCKFILE%"
    echo [%date% %time%] Lock eliminado por tarea previa. >> "%APPDATA%\ClienteNotificaciones\log.txt"
)

exit /b 0
