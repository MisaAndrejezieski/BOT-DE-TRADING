@echo off
echo ========================================
echo PAPER TRADING - Estratégia -2%%/+4%%
echo ========================================
echo.

call venv\Scripts\activate.bat

if "%1"=="" (
    set DAYS=30
) else (
    set DAYS=%1
)

echo Iniciando Paper Trading por %DAYS% dias...
python main_advanced.py --mode paper --days %DAYS%

pause