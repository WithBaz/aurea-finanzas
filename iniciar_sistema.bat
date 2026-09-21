@echo off
chcp 65001 > nul
title AUREA - Sistema Financiero Personal en COP
cls
echo =====================================================================
echo           AUREA: Administracion Unificada de Recursos y Ahorro
echo                  Plataforma Financiera para iPhone & Web
echo =====================================================================
echo.

cd /d "%~dp0"

REM 1. Verificar o crear entorno virtual Python
if not exist ".venv" (
    echo [1/4] Creando entorno virtual Python .venv...
    python -m venv .venv
    echo [2/4] Instalando dependencias desde requirements.txt...
    call .venv\Scripts\activate.bat
    python -m pip install --upgrade pip
    pip install -r requirements.txt
) else (
    echo [1/4] Entorno virtual .venv detectado. Activando...
    call .venv\Scripts\activate.bat
)

REM 2. Poblar datos iniciales si no existen
echo [2/4] Verificando base de datos y catálogo de comercios en COP...
python -m backend.app.seed

REM 3. Ejecutar pruebas automatizadas de integridad
echo [3/4] Ejecutando suite de pruebas automatizadas...
pytest -q
if %ERRORLEVEL% NEQ 0 (
    echo [ALERTA] Algunas pruebas fallaron, pero continuaremos con el arranque...
)

REM 4. Lanzar navegador y servidor Uvicorn
echo [4/4] Levantando servidor AUREA en http://127.0.0.1:8000 ...
start "" http://127.0.0.1:8000
start "" http://127.0.0.1:8000/docs

uvicorn backend.app.main:app --reload --port 8000
pause
