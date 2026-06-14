@echo off
title CLAUDE x QUANT — MODO LIVE
echo ============================================
echo  CLAUDE x QUANT — MODO LIVE (DINHEIRO REAL)
echo ============================================
echo.

if not exist "%~dp0src\polymarket-sniper\.env" (
    echo [ERRO] Chaves nao configuradas.
    echo Execute primeiro: CONFIGURAR-SNIPER.bat
    pause
    exit /b
)

cd /d "%~dp0src\polymarket-sniper"

echo Carregando configuracao...
for /f "usebackq tokens=1,* delims==" %%A in (".env") do (
    set "%%A=%%B"
)

echo.
echo [LIVE] Iniciando sniper com capital real...
echo Pressione Ctrl+C para parar.
echo.
python main.py
pause
