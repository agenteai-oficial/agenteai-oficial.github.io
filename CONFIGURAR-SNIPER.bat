@echo off
title Configurar CLAUDE x QUANT — Chaves da API
echo ============================================
echo  CONFIGURAR CHAVES DO SNIPER
echo ============================================
echo.
echo Voce precisara de:
echo  1. API KEY    — polymarket.com/settings ^> Chaves API
echo  2. ENDERECO   — o mesmo (0x...)
echo  3. PRIVATE KEY — MetaMask ^> Conta ^> Exportar chave privada
echo.
echo ============================================
echo  AVISO DE SEGURANCA — LEIA COM ATENCAO
echo ============================================
echo.
echo A chave privada (private key) da MetaMask da acesso
echo TOTAL a todos os fundos dessa carteira.
echo.
echo  - Use UMA CARTEIRA SEPARADA so para o bot
echo  - Coloque APENAS o valor que aceita perder
echo  - NUNCA compartilhe o arquivo .env com ninguem
echo  - O arquivo fica em: src\polymarket-sniper\.env
echo.
echo ============================================
echo.

set /p POLY_KEY="1. Cole sua API KEY (019ec8bd...): "
set /p POLY_ADDR="2. Cole seu ENDERECO (0x...): "
set /p PRIV_KEY="3. Cole sua PRIVATE KEY da MetaMask (0x...): "
set /p ANTHROPIC="4. ANTHROPIC_API_KEY (opcional, Enter pula): "

echo.
echo Salvando configuracao...

(
echo POLYMARKET_API_KEY=%POLY_KEY%
echo POLYMARKET_API_KEY_ADDRESS=%POLY_ADDR%
echo WALLET_PRIVATE_KEY=%PRIV_KEY%
echo ANTHROPIC_API_KEY=%ANTHROPIC%
echo EXECUTION_MODE=live
) > "%~dp0src\polymarket-sniper\.env"

echo.
echo [OK] Configuracao salva em src\polymarket-sniper\.env
echo.
echo NUNCA compartilhe este arquivo ou a private key!
echo.
echo Proximo passo:
echo   pip install py-clob-client
echo   python src\polymarket-sniper\dashboard.py
echo.
pause
