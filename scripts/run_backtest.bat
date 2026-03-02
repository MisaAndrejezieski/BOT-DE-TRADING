@echo off
echo ========================================
echo BACKTEST - Estratégia -2%%/+4%%
echo ========================================
echo.

call venv\Scripts\activate.bat

if "%1"=="" (
    set DAYS=90
) else (
    set DAYS=%1
)

echo Iniciando Backtest de %DAYS% dias...
python main_advanced.py --mode backtest --days %DAYS% --optimize

pause