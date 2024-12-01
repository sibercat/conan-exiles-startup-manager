# Conan Exiles Startup Manager
A Python-based monitoring tool for Conan Exiles dedicated servers that provides server status monitoring with optional port management, zombie process detection, and Discord notifications.

## Key Features
- Server status monitoring with configurable Discord notifications via webhook
- Optional port management during startup/shutdown (prevents premature connections)
- Zombie process detection and auto-kill functionality
- Configurable startup delay after server load
- Real-time server status updates
- Detailed logging system
- Customizable notification messages

## Purpose
This tool helps server administrators by monitoring server status, detecting zombie processes, and optionally preventing players from connecting to the server before it's fully initialized. It can block premature connections through Windows Firewall and provides real-time status updates through Discord notifications.

## Requirements
- Windows OS
- Python 3.7+
- Administrator privileges (only if firewall management is enabled)
- Discord webhook URL (optional for notifications)

## Setup
1. Install requirements:
   ```
   pip install -r requirements.txt
   ```
2. Configure the tool:
   - Edit the following settings in `config.json`:
     - Set `discord_enabled` to "true" or "false"
     - Add your Discord webhook URL if using Discord notifications
     - Set `firewall_enabled` to true/false (requires admin if true)
     - Configure zombie detection settings if desired
     - Adjust other settings as needed (startup delay, ports, messages)
3. Start the monitor:
   - Run `!start.cmd`
   - Select your Conan Exiles server log directory when prompted

## Configuration Options
```json
{
    "discord_enabled": "true",
    "discord_webhook_url": "your-webhook-url-here",
    "server": {
        "name": "Conan Exiles Server",
        "logs_directory": "",
        "startup_delay": 30,
        "firewall_enabled": false,
        "zombie_detection": {
            "enabled": true,
            "timeout_minutes": 5,
            "auto_kill": true,
            "check_interval_seconds": 30
        },
        "ports": [
            {"port": 7777, "proto": "UDP"},
            {"port": 7777, "proto": "TCP"},
            {"port": 7778, "proto": "UDP"},
            {"port": 27015, "proto": "UDP"},
            {"port": 25575, "proto": "TCP"}
        ],
        "message_control": {
            "startup_notification": true,
            "loading_notification": true,
            "ready_notification": true,
            "shutdown_warning_notification": true,
            "network_shutdown_notification": true,
            "shutdown_final_notification": true,
            "monitor_stop_notification": true,
            "zombie_detected_notification": true,
            "zombie_killed_notification": true
        },
        "messages": {
            "startup": "[START] Server monitor starting up...",
            "loading": "[UPDATE] Server is starting up... Ports blocked for safety.",
            "ready": "[SUCCESS] Server is fully loaded and ready for connections!",
            "shutdown_warning": "[WARNING] Server is preparing to shut down...",
            "network_shutdown": "[WARNING] Server network is shutting down...",
            "shutdown_final": "[WARNING] Server has stopped...",
            "monitor_stop": "[STOP] Server monitor shutting down...",
            "zombie_detected": "[WARNING] Server process is not responding (zombie state detected)!",
            "zombie_killed": "[UPDATE] Zombie process was forcefully terminated."
        }
    }
}
```

## Features in Detail
### Port Management (Optional)
- Blocks configured ports during server startup
- Automatically allows connections once server is fully loaded
- Blocks ports again during shutdown
- Can be disabled if not needed

### Zombie Process Detection
- Monitors server process for unresponsive/zombie states
- Configurable timeout period before declaring process as zombie
- Optional automatic termination of zombie processes
- Discord notifications for zombie detection and termination
- Can be enabled/disabled as needed

### Discord Integration
- Real-time status notifications via webhook
- Customizable messages for different server states
- Notifications for zombie process detection
- Can be enabled/disabled as needed
- No bot token required, just webhook URL

### Startup Delay
- Configurable delay after server load detection
- Ensures server is fully ready before allowing connections
- Can be set to 0 to disable

### Logging
- Detailed logging of all operations
- Rotating log files to manage disk space
- Console output for real-time monitoring

## Troubleshooting
- If using firewall management, ensure the script runs with admin privileges
- Check logs in the `logs` directory for detailed information
- Verify Discord webhook URL if notifications aren't working
- If zombie detection seems incorrect, try adjusting the timeout period

## Notes
- Administrator privileges are only required if firewall management is enabled
- Discord notifications work independently of firewall and zombie detection
- The tool can be used purely for status monitoring if desired
- Zombie detection can help prevent server hanging issues during shutdown
