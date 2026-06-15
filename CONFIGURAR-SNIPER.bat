@echo off
title Configurar CLAUDE x QUANT — Chaves da API
echo ============================================
echo  CONFIGURAR CHAVES DO SNIPER
echo ============================================
echo.
echo Para obter as chaves acesse:
echo  polymarket.com/settings ^> Chaves API do Relayer
echo.
echo  1. API KEY  (019ec8bd-80bd-7013-bd8e-...)
echo  2. ENDERECO (0x1dc3b401f3...)
echo.
echo ============================================
echo.

set /p POLY_KEY="1. Cole sua API KEY: "
set /p POLY_ADDR="2. Cole seu ENDERECO (0x...): "
set /p ANTHROPIC="ANTHROPIC_API_KEY (opcional, Enter para pular): "

echo.
echo Salvando configuracao...

(
echo POLYMARKET_API_KEY=%POLY_KEY%
echo POLYMARKET_API_KEY_ADDRESS=%POLY_ADDR%
echo ANTHROPIC_API_KEY=%ANTHROPIC%
echo EXECUTION_MODE=live
) > "%~dp0src\polymarket-sniper\.env"

echo.
echo [OK] Configuracao salva em src\polymarket-sniper\.env
echo.
echo ATENCAO: NUNCA compartilhe este arquivo .env com ninguem!
echo.
echo Para iniciar o bot: RODAR-LIVE.bat
pause
