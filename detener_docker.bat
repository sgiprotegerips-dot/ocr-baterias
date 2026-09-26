@echo off
title Detener Sala de Lectura Masiva - Docker
echo Deteniendo contenedores de Docker...
cd /d "%~dp0"
docker compose down
echo Contenedores detenidos.
pause
