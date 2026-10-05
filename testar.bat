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

echo [INFO] Ativando VENV e rodando script de testes...
call venv\Scripts\activate
python tests\teste_integracao.py

echo.
echo ===================================================
echo     TESTE FINALIZADO
echo ===================================================
pause
