@echo off
chcp 65001 >nul
title collab init
cd /d "%~dp0"
set PY=python
where python >nul 2>nul || set PY=py
if "%~1"=="" ( set PEOPLE=A,B,C ) else ( set PEOPLE=%~1 )
"%PY%" collab.py init --people %PEOPLE%
echo.
"%PY%" collab.py status
pause
