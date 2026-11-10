@echo off
rem PixelDigest: prepara o Python na primeira vez e abre o programa.
rem Tudo e configurado dentro do programa (botao Configurar ou F10).
rem Uso: run.bat            abre o programa
rem      run.bat --demo     abre com empresas de exemplo
cd /d "%~dp0"
set PYTHONUTF8=1
if not exist .venv\Scripts\python.exe (
  echo Preparando o PixelDigest pela primeira vez...
  py -3 -m venv .venv 2>nul || python -m venv .venv
  if errorlevel 1 ( echo Instale o Python 3.12+ em python.org e rode de novo. & pause & exit /b 1 )
  .venv\Scripts\python -m pip install -q --upgrade pip
)
rem instala as bibliotecas de novo so quando o requirements.txt mudar
fc /b requirements.txt .venv\req.ok >nul 2>&1 || (
  echo Instalando bibliotecas...
  .venv\Scripts\python -m pip install -q -r requirements.txt && copy /y requirements.txt .venv\req.ok >nul
)
.venv\Scripts\python -m pixeldigest %*
if errorlevel 1 pause
