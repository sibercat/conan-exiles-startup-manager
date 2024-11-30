# Conan Exiles Startup Manager
A Python-based monitoring tool for Conan Exiles dedicated servers that provides server status monitoring with optional port management, process state detection, and Discord notifications.

## Key Features
- Server status monitoring with configurable Discord notifications via webhook
- Process state monitoring to ensure server is fully responsive
- Optional port management during startup/shutdown (prevents premature connections)
- Configurable startup delay after server load
- Real-time server status updates
- Detailed logging system
- Customizable notification messages

## Purpose
This tool helps server administrators by monitoring server status and optionally preventing players from connecting to the server before it's fully initialized. It monitors both the server log files and process state to ensure the server is truly ready. It can block premature connections through Windows Firewall and provides real-time status updates through Discord notifications.

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
        "process_monitoring": {
            "enabled": true,
            "check_interval": 5,
            "max_wait_time": 300,
            "notification_interval": 60
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
            "shutdown_notification": true,
            "monitor_stop_notification": true,
            "process_initializing_notification": true,
            "process_ready_notification": true,
            "process_timeout_notification": true,
            "process_status_updates": true,
            "port_block_notification": true,
            "port_allow_notification": true,
            "error_notification": true,
            "periodic_status_notification": true
        },
        "messages": {
            "startup": "[START] Server monitor starting up...",
            "loading": "[UPDATE] Server is starting up... Ports blocked for safety.",
            "ready": "[SUCCESS] Server is fully loaded and ready for connections!",
            "shutdown": "[WARNING] Server is shutting down...",
            "monitor_stop": "[STOP] Server monitor shutting down...",
            "process_not_responding": "[UPDATE] Server is still initializing, please wait...",
            "process_ready": "[UPDATE] Server process is now responding and ready!",
            "process_timeout": "[WARNING] Server initialization is taking longer than usual...",
            "port_blocked": "[UPDATE] Server ports have been blocked for safety",
            "port_allowed": "[UPDATE] Server ports have been opened for connections",
            "error": "[ERROR] An error occurred while monitoring the server",
            "periodic_status": "[INFO] Server is running normally. All systems operational."
        }
    }
}
```

## Features in Detail
### Process Monitoring
- Monitors server process state to ensure it's fully responsive
- Configurable check intervals and timeout periods
- Notifies when server becomes responsive or if initialization takes too long
- Can be customized through process_monitoring settings

### Port Management (Optional)
- Blocks configured ports during server startup
- Automatically allows connections once server is fully loaded and responsive
- Blocks ports again during shutdown
- Can be disabled if not needed

### Discord Integration
- Real-time status notifications via webhook
- Customizable messages for different server states
- Granular control over notification types
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
- Monitor the process_monitoring logs if server initialization seems slow

## Notes
- Administrator privileges are only required if firewall management is enabled
- Discord notifications work independently of firewall management
- The tool can be used purely for status monitoring if desired
- Process monitoring helps ensure the server is truly ready before allowing connections
