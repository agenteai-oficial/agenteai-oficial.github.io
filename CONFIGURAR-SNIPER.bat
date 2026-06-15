@echo off
title Configurar CLAUDE x QUANT — Chaves da API
echo ============================================
echo  CONFIGURAR CHAVES DO SNIPER
echo ============================================
echo.
echo Para obter as 4 chaves acesse:
echo  polymarket.com/settings  ^> Chaves API
echo  Clique em "+ Criar novo" e COPIE TODAS as 4 informacoes
echo.
echo  1. API KEY (019ec8bd...)
echo  2. API SECRET (base64, começa com aA...)
echo  3. PASSPHRASE (sua senha da API)
echo  4. ENDERECO DA CARTEIRA (0x1dc3b...)
echo.
echo ATENCAO: O Secret e Passphrase aparecem SO UMA VEZ ao criar.
echo Se nao tem, crie uma nova chave e copie tudo agora.
echo ============================================
echo.

set /p POLY_KEY="1. Cole sua API KEY: "
set /p POLY_SECRET="2. Cole sua API SECRET: "
set /p POLY_PASS="3. Cole sua PASSPHRASE: "
set /p POLY_ADDR="4. Cole seu ENDERECO (0x...): "
set /p ANTHROPIC="ANTHROPIC_API_KEY (opcional, Enter para pular): "

echo.
echo Salvando configuracao...

(
echo POLYMARKET_API_KEY=%POLY_KEY%
echo POLYMARKET_API_SECRET=%POLY_SECRET%
echo POLYMARKET_PASSPHRASE=%POLY_PASS%
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
