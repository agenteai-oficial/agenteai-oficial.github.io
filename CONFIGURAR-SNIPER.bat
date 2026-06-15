@echo off
title Configurar CLAUDE x QUANT — Chaves da API
echo ============================================
echo  CONFIGURAR CHAVES DO SNIPER
echo ============================================
echo.
echo Antes de continuar, voce precisa de:
echo  1. Conta na Polymarket (polymarket.com)
echo  2. KYC aprovado (documento de identidade)
echo  3. Carteira MetaMask com USDC na rede Polygon
echo  4. API Keys geradas em: polymarket.com/settings/api
echo.
echo ============================================

set /p POLY_KEY="Cole sua Chave API (019ec8bd...): "
set /p POLY_ADDR="Cole seu Endereco (0x1dc3b...): "
set /p ANTHROPIC="Cole sua ANTHROPIC_API_KEY (opcional): "

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
echo Para iniciar o bot em MODO REAL, rode: RODAR-LIVE.bat
pause
