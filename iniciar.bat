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

echo [INFO] Verificando dependencias...
pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org -r requirements.txt

echo.
echo [INFO] Iniciando aplicacao...
python TaradutorLegendas26.py

pause
