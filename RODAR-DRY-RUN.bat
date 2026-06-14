@echo off
title CLAUDE x QUANT — Dry Run
echo ============================================
echo  CLAUDE x QUANT — Polymarket Sniper
echo  MODO: DRY RUN (sem dinheiro real)
echo ============================================
echo.

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRO] Python nao encontrado.
    echo.
    echo Instale em: https://www.python.org/downloads/
    echo Marque a opcao "Add Python to PATH" durante a instalacao.
    echo.
    pause
    exit /b
)

cd /d "%~dp0src\polymarket-sniper"

echo [1/2] Instalando dependencias...
pip install -r requirements-dryrun.txt -q

echo [2/2] Iniciando bot em modo dry_run...
echo.
set EXECUTION_MODE=dry_run
python main.py
pause
