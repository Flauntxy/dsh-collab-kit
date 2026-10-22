@echo off
chcp 65001 >nul
title collab waiter
cd /d "%~dp0"
set PY=python
where python >nul 2>nul || set PY=py
set WHO=%~1
if "%WHO%"=="" set WHO=A
echo Waiting for flag of %WHO% ... (Ctrl+C to stop)
echo NOTE: this window is detached from any AI session, it will NOT wake a conversation.
"%PY%" collab.py wait --as %WHO% --timeout 14400
echo.
echo Flag raised. Next:  %PY% collab.py poll --as %WHO%
pause
