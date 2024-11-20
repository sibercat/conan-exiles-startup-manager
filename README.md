# Conan Exiles Startup Manager

A Python-based monitoring tool for Conan Exiles dedicated servers that prevents premature connections by managing ports during server startup and shutdown processes. Includes Discord integration for server status notifications.

## Key Features
- Prevents player connections until server is fully loaded
- Automatically manages server ports during startup/shutdown
- Real-time server status monitoring via Discord notifications
- Log file monitoring for server state changes

## Managed Ports
- 7777 TCP/UDP (Game Port)
- 7778 UDP
- 27015 UDP (Query Port)
- 25575 TCP (RCON Port)

## Purpose
This tool helps server administrators by preventing players from connecting to the server before it's fully initialized, avoiding potential connection issues and ensuring smoother server starts. Provides real-time status updates through Discord notifications.

## Requirements
- Windows OS
- Python 3.7+
- Administrator privileges
- Discord Bot (optional for notifications)

## Setup
1. Install requirements:
   pip install -r requirements.txt
