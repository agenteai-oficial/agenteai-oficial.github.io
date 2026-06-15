@echo off
title Configurar CLAUDE x QUANT — Chaves da API
echo ============================================
echo  CONFIGURAR CHAVES DO SNIPER
echo ============================================
echo.
echo Para obter as chaves acesse:
echo  polymarket.com/settings ^> Chaves API do Relayer
echo.
echo ============================================

set /p POLY_KEY="API KEY (019ec8bd...): "
set /p POLY_ADDR="ENDERECO (0x1dc3b...): "

echo.
echo ============================================
echo  MODO DE EXECUCAO
echo ============================================
echo.
echo  [1] ALERT   — Avisa oportunidades, voce executa manualmente no site
echo  [2] DRY RUN — Simula trades sem dinheiro real (para testar)
echo  [3] LIVE    — Executa ordens reais (requer WALLET_PRIVATE_KEY)
echo.
set /p MODO="Escolha 1, 2 ou 3: "

if "%MODO%"=="1" set EXEC_MODE=alert
if "%MODO%"=="2" set EXEC_MODE=dry_run
if "%MODO%"=="3" (
    set EXEC_MODE=live
    echo.
    echo Para LIVE voce precisa da Private Key da MetaMask.
    echo MetaMask ^> Conta ^> ... ^> Account Details ^> Export Private Key
    echo.
    set /p PRIV_KEY="PRIVATE KEY da MetaMask (0x... ou deixe vazio): "
)

set /p ANTHROPIC="ANTHROPIC_API_KEY (opcional, Enter pula): "
set /p WEBHOOK="WEBHOOK_URL Discord/Slack (opcional, Enter pula): "

echo.
echo Salvando configuracao...

(
echo POLYMARKET_API_KEY=%POLY_KEY%
echo POLYMARKET_API_KEY_ADDRESS=%POLY_ADDR%
echo WALLET_PRIVATE_KEY=%PRIV_KEY%
echo ANTHROPIC_API_KEY=%ANTHROPIC%
echo WEBHOOK_URL=%WEBHOOK%
echo EXECUTION_MODE=%EXEC_MODE%
) > "%~dp0src\polymarket-sniper\.env"

echo.
echo [OK] Configuracao salva — Modo: %EXEC_MODE%
echo.
if "%MODO%"=="1" (
    echo No modo ALERT o bot avisa no terminal quando ha oportunidade.
    echo Voce acessa polymarket.com e executa manualmente.
)
echo.
echo Para iniciar: RODAR-LIVE.bat
pause
