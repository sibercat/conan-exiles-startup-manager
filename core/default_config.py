"""Default configuration values for the Conan Exiles Server Monitor"""

# Server configurations
DEFAULT_PORTS = [
    {"port": 7777, "proto": "UDP"},
    {"port": 7777, "proto": "TCP"},
    {"port": 7778, "proto": "UDP"},
    {"port": 27015, "proto": "UDP"},
    {"port": 25575, "proto": "TCP"}
]

DEFAULT_SERVER_CONFIG = {
    "name": "Conan Exiles Server",
    "logs_directory": "",
    "startup_delay": 30,
    "firewall_enabled": False,
    "zombie_detection": {
        "enabled": True,
        "timeout_minutes": 5,
        "auto_kill": True,
        "check_interval_seconds": 30
    },
    "ports": DEFAULT_PORTS,
    "message_control": {
        "startup_notification": True,
        "loading_notification": True,
        "ready_notification": True,
        "shutdown_warning_notification": True,
        "network_shutdown_notification": True,
        "shutdown_final_notification": True,
        "monitor_stop_notification": True,
        "zombie_detected_notification": True,
        "zombie_killed_notification": True
    },
    "messages": {
        "startup": "[START] Server monitor starting up...",
        "loading": "[UPDATE] Server is starting up...",
        "ready": "[SUCCESS] Server is fully loaded and ready for connections!",
        "shutdown_warning": "[WARNING] Server is preparing to shut down...",
        "network_shutdown": "[WARNING] Server network is shutting down...",
        "shutdown_final": "[WARNING] Server has stopped...",
        "monitor_stop": "[STOP] Server monitor shutting down...",
        "zombie_detected": "[WARNING] Server process is not responding (zombie state detected)!",
        "zombie_killed": "[UPDATE] Zombie process was forcefully terminated."
    }
}

# Discord webhook configurations
DEFAULT_DISCORD_CONFIG = {
    "discord_enabled": "false",
    "discord_webhook_url": ""
}

# Combined default configuration
DEFAULT_CONFIG = {
    **DEFAULT_DISCORD_CONFIG,
    "server": DEFAULT_SERVER_CONFIG
}

# Constants used throughout the application
CONSTANTS = {
    "RULE_NAME_PREFIX": "GameServerControl",
    "SERVER_PROCESS_NAME": "ConanSandboxServer-Win64-Shipping.exe",
    "LOG_PATTERNS": {
        "SERVER_STARTING": "Entered application state 'ConanSandboxStarting'",
        "LOAD_COMPLETE": "WorldPersistenceDone",
        "SERVER_EXIT_WARNING": "LogWindows: FPlatformMisc::RequestExit(0)",
        "SERVER_NETWORK_DOWN": "LogNet: World NetDriver shutdown",
        "SERVER_STOPPED": "Entered application state 'ConanSandboxStopped'"
    }
}