@echo off
echo ===================================================
echo     Iniciando Tradutor Automatico de Legendas
echo ===================================================
echo.

if not exist venv\ (
    echo [INFO] Criando ambiente virtual...
    python -m venv venv
)

echo [INFO] Ativando ambiente virtual...
call venv\Scripts\activate

fc /b requirements.txt venv\.req_cache >nul 2>&1
if errorlevel 1 (
    echo [INFO] Instalando/atualizando dependencias...
    pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org -r requirements.txt
    copy /y requirements.txt venv\.req_cache >nul
) else (
    echo [INFO] Dependencias atualizadas. Pulando instalacao...
)

echo.
echo [INFO] Iniciando aplicacao...
python TaradutorLegendas26.py

pause
