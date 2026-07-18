@echo off
title Marea Activa - Servidor Backend

:: 1. Abre automáticamente el navegador en la documentación interactiva de Swagger UI
start "" "http://127.0.0.1:8000/docs"

:: 2. Levanta el servidor usando el Python correcto del entorno virtual de forma explícita
.\.venv\Scripts\python -m uvicorn src.main:app --reload --reload-dir src

pause
