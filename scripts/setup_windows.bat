@echo off
echo ========================================
echo Configurando Bot de Trading no Windows
echo Estratégia: -2%% para COMPRA, +4%% para VENDA
echo ========================================
echo.

REM Verifica se Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo ERRO: Python nao encontrado!
    echo Por favor, instale o Python 3.8 ou superior
    echo Baixe em: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Cria ambiente virtual
echo Criando ambiente virtual...
python -m venv venv

REM Ativa ambiente virtual
echo Ativando ambiente virtual...
call venv\Scripts\activate.bat

REM Atualiza pip
echo Atualizando pip...
python -m pip install --upgrade pip

REM Instala dependências
echo Instalando dependências...
pip install -r requirements.txt

REM Cria estrutura de pastas
echo Criando estrutura de pastas...
mkdir data\logs 2>nul
mkdir data\history 2>nul
mkdir data\exports 2>nul
mkdir ml\models 2>nul
mkdir backtest\results 2>nul
mkdir reports 2>nul

REM Copia arquivo de exemplo
if not exist .env (
    echo Criando arquivo .env a partir do exemplo...
    copy .env.example .env
    echo.
    echo ⚠️  NÃO ESQUEÇA de editar o arquivo .env com suas configurações!
)

echo.
echo ========================================
echo ✅ Configuracao concluida com sucesso!
echo ========================================
echo.
echo Proximos passos:
echo 1. Edite o arquivo .env com suas configurações
echo 2. Execute: python main_advanced.py --mode paper --days 30
echo 3. Para testar: python main_advanced.py --mode backtest --days 90
echo.
pause