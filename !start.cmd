@echo off
title Initial start window
cd /d "%~dp0"
echo You can close this window...
powershell Start-Process python -ArgumentList "server_monitor.py" -Verb RunAs -Wait
pause >nul
