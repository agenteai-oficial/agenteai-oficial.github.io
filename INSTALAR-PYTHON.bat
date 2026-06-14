@echo off
title Instalador — Python para CLAUDE x QUANT
echo ============================================
echo  Instalando Python para o Sniper
echo ============================================
echo.

python --version >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Python ja esta instalado:
    python --version
    echo.
    goto :instalar_deps
)

echo [1/2] Baixando Python 3.12...
curl -L -o "%TEMP%\python-installer.exe" "https://www.python.org/ftp/python/3.12.4/python-3.12.4-amd64.exe"

echo [2/2] Instalando Python (adiciona ao PATH automaticamente)...
"%TEMP%\python-installer.exe" /quiet InstallAllUsers=1 PrependPath=1 Include_pip=1

echo.
echo [OK] Python instalado. Reinicie o PowerShell se necessario.
echo.

:instalar_deps
echo Instalando dependencias do sniper...
cd /d "%~dp0src\polymarket-sniper"
pip install numpy scipy fastapi uvicorn py-clob-client anthropic -q
echo.
echo ============================================
echo  PRONTO! Agora rode: RODAR-DRY-RUN.bat
echo  Ou, com suas chaves: RODAR-LIVE.bat
echo ============================================
pause
