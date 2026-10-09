@echo off
echo ===================================================
echo     AMBIENTE DE TESTE ISOLADO - TARADUTOR
echo ===================================================
echo.

if not exist venv\ (
    echo [ERRO] Virtual Environment não encontrado. Rode o iniciar.bat primeiro.
    pause
    exit /b
)

echo [INFO] Ativando VENV e rodando testes unitarios com pytest...
call venv\Scripts\activate
pytest tests\unit -v

echo.
echo ===================================================
echo     TESTE FINALIZADO
echo ===================================================
pause
