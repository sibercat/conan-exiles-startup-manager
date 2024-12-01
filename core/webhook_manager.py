# core/webhook_manager.py
import json
import os
from typing import Dict, Any, Optional
import requests
from core.logging_utils import LoggerSetup

class WebhookManager:
    # Default configuration
    DEFAULT_CONFIG = {
            "discord_enabled": "false",
            "discord_webhook_url": "",
            "server": {
                "name": "Conan Exiles Server",
                "logs_directory": "",
                "startup_delay": 30,
                "firewall_enabled": False,
                "ports": [
                    {"port": 7777, "proto": "UDP"},
                    {"port": 7777, "proto": "TCP"},
                    {"port": 7778, "proto": "UDP"},
                    {"port": 27015, "proto": "UDP"},
                    {"port": 25575, "proto": "TCP"}
                ],
                "message_control": {
                    "startup_notification": True,
                    "loading_notification": True,
                    "ready_notification": True,
                    "shutdown_notification": True,
                    "monitor_stop_notification": True
                },
                "messages": {
                    "startup": "[START] Server monitor starting up...",
                    "loading": "[UPDATE] Server is starting up... Ports blocked for safety.",
                    "ready": "[SUCCESS] Server is fully loaded and ready for connections!",
                    "shutdown": "[WARNING] Server is shutting down...",
                    "monitor_stop": "[STOP] Server monitor shutting down..."
                }
            }
        }

    def __init__(self, config_path: str = 'config/config.json'):
        # Setup base paths
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.logs_dir = os.path.join(self.base_dir, 'logs')
        self.config_path = os.path.join(self.base_dir, config_path)
        
        # Initialize logger
        self.logger = LoggerSetup.setup_logger(
            'WebhookManager',
            self.logs_dir,
            'webhook_manager.log'
        )
        
        # Load config and message control settings
        self.config = self._load_config()
        self.message_control = self._get_message_control()

    def _load_config(self) -> Dict[str, Any]:
        """
        Load configuration from json file or create default if not exists
        
        Returns:
            Dict[str, Any]: Configuration dictionary
        """
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as config_file:
                    config = json.load(config_file)
                    self.logger.info("Configuration loaded successfully")
                    return config
            else:
                self.logger.warning(f"Config file not found at {self.config_path}. Creating default config.")
                os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
                with open(self.config_path, 'w', encoding='utf-8') as config_file:
                    json.dump(self.DEFAULT_CONFIG, config_file, indent=2)
                self.logger.info("Created default configuration file")
                return self.DEFAULT_CONFIG.copy()
        except Exception as e:
            self.logger.error(f"Error loading config: {e}")
            return self.DEFAULT_CONFIG.copy()

    def _get_message_control(self) -> Dict[str, bool]:
        """
        Get message control settings from config
        
        Returns:
            Dict[str, bool]: Message control settings
        """
        try:
            if 'server' in self.config and 'message_control' in self.config['server']:
                return {**self.DEFAULT_CONFIG['server']['message_control'], 
                       **self.config['server']['message_control']}
            return self.DEFAULT_CONFIG['server']['message_control'].copy()
        except Exception as e:
            self.logger.error(f"Error loading message control settings: {e}")
            return self.DEFAULT_CONFIG['server']['message_control'].copy()

    def _get_message_type(self, message: str) -> Optional[str]:
        """
        Determine message type based on content
        
        Args:
            message (str): Message content
            
        Returns:
            Optional[str]: Message type if identified, None otherwise
        """
        for prefix, msg_type in self.MESSAGE_TYPES.items():
            if message.startswith(prefix):
                return msg_type
        return None

    def is_enabled(self) -> bool:
        """
        Check if Discord integration is enabled
        
        Returns:
            bool: True if Discord integration is enabled and configured
        """
        enabled = self.config.get('discord_enabled', 'false').lower() == 'true'
        webhook_url = self.config.get('discord_webhook_url', '')
        
        if enabled and not webhook_url:
            self.logger.warning("Discord is enabled but webhook URL is missing")
            return False
            
        return enabled

    def send_message(self, message: str) -> bool:
        """
        Send message to Discord webhook if enabled and message type is allowed
        
        Args:
            message (str): Message to send
            
        Returns:
            bool: True if message was sent successfully, False otherwise
        """
        if not self.is_enabled():
            self.logger.info("Discord messaging is disabled. Message not sent.")
            return False

        try:
            message_type = self._get_message_type(message)
            if message_type and not self.message_control.get(message_type, True):
                self.logger.info(f"Message type '{message_type}' is disabled. Message not sent.")
                return False

            webhook_url = self.config.get('discord_webhook_url')
            response = requests.post(webhook_url, json={'content': message})
            response.raise_for_status()
            
            self.logger.info(f"Message sent to Discord: {message}")
            return True
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error sending message to Discord webhook: {e}")
            return False

    def start(self) -> None:
        """Initialize webhook manager"""
        if self.is_enabled():
            self.logger.info("Webhook manager started and ready")

    def stop(self) -> None:
        """Cleanup webhook manager resources"""
        self.logger.info("Webhook manager stopped")
