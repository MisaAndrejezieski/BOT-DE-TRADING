@echo off
echo ========================================
echo ⚠️  ATENCAO - MODO REAL
echo Estratégia: -2%% para COMPRA, +4%% para VENDA
echo ========================================
echo.
echo Voce esta prestes a usar DINHEIRO REAL!
echo.
echo Verifique:
echo 1. API keys estao corretas no .env
echo 2. Sandbox mode = false
echo 3. Stop loss configurado (-3%%)
echo 4. Limite de trades configurado (3/dia)
echo.
set /p confirm="Digite 'SIM' para continuar: "

if not "%confirm%"=="SIM" (
    echo Operacao cancelada.
    pause
    exit /b
)

call venv\Scripts\activate.bat
python main_advanced.py --mode real

pause