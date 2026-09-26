@echo off
title Sala de Lectura Masiva - Docker Desktop
echo ========================================================
echo   Iniciando Sala de Lectura Masiva con Docker Compose
echo ========================================================
cd /d "%~dp0"

echo Verificando si Docker esta en ejecucion...
docker info >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ADVERTENCIA] Docker Desktop no responde o no esta iniciado.
    echo Asegurate de que Docker Desktop este abierto y el motor Linux este activo.
    echo Si acabas de habilitar WSL, recuerda reiniciar tu PC.
    echo.
    pause
    exit /b 1
)

echo Levantando contenedores (PostgreSQL + Bateria App)...
docker compose up -d --build

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================================
    echo   La aplicacion esta corriendo en Docker Desktop!
    echo   URL Local: http://localhost:8001
    echo   Base de datos Postgres: localhost:5435
    echo ========================================================
    timeout /t 5 >nul
    echo.
    echo Extrayendo URL publica de Cloudflare Tunnel:
    docker logs bateria_tunnel 2>&1 | findstr /C:"trycloudflare.com"
    echo.
    echo ========================================================
    start http://localhost:8001
) else (
    echo [ERROR] Hubo un problema al levantar los contenedores con Docker.
)
pause
