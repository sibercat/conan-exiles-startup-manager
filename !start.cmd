@echo off
powershell Start-Process python -ArgumentList "server_monitor.py" -Verb RunAs
pause