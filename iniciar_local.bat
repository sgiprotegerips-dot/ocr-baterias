@echo off
title Sala de Lectura Masiva - OCR/OMR Bateria
echo ========================================================
echo   Iniciando Sala de Lectura Masiva (Modo Local Python)
echo ========================================================
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] No se encontro el entorno virtual en .venv
    pause
    exit /b 1
)

echo Iniciando servidor Uvicorn en http://127.0.0.1:8000 ...
start http://127.0.0.1:8000
.\.venv\Scripts\python.exe run.py
pause
