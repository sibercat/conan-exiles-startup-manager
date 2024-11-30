@echo off
title Initial start window
cd /d "%~dp0"
echo Checking firewall settings...

:: Check if firewall is enabled in config
powershell -Command "if ((Get-Content 'config/config.json' | ConvertFrom-Json).server.firewall_enabled) { exit 1 } else { exit 0 }"

if %errorlevel%==1 (
    echo Firewall management is enabled - starting with admin privileges...
    powershell Start-Process python -ArgumentList "server_monitor.py" -Verb RunAs -Wait
) else (
    echo Firewall management is disabled - starting normally...
    python server_monitor.py
)

pause >nul
