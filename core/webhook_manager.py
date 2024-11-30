# core/webhook_manager.py
import json
import logging
import os
from logging.handlers import RotatingFileHandler
import requests
import sys

class WebhookManager:
    def __init__(self, config_path='config/config.json'):
        # Setup base paths
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.logs_dir = os.path.join(self.base_dir, 'logs')
        self.config_path = os.path.join(self.base_dir, config_path)
        
        # Setup logging
        self.setup_logging()
        self.logger = logging.getLogger('WebhookManager')
        
        # Load config
        self.config = self._load_config()
        
        # Load message control settings
        self.message_control = self._get_message_control()

    def setup_logging(self):
        """Setup logging configuration"""
        if not os.path.exists(self.logs_dir):
            os.makedirs(self.logs_dir)

        log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        log_file = os.path.join(self.logs_dir, 'webhook_manager.log')
        
        file_handler = RotatingFileHandler(
            log_file, 
            maxBytes=5*1024*1024,  # 5MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setFormatter(log_formatter)

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(log_formatter)

        logger = logging.getLogger('WebhookManager')
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            logger.addHandler(file_handler)
            logger.addHandler(console_handler)

    def _get_message_control(self):
        """Get message control settings from config"""
        default_controls = {
            "startup_notification": True,
            "loading_notification": True,
            "ready_notification": True,
            "shutdown_notification": True,
            "monitor_stop_notification": True
        }
        
        try:
            if 'server' in self.config and 'message_control' in self.config['server']:
                return {**default_controls, **self.config['server']['message_control']}
            return default_controls
        except Exception as e:
            self.logger.error(f"Error loading message control settings: {e}")
            return default_controls

    def _get_message_type(self, message):
        """Determine message type based on content"""
        message_types = {
            "[START": "startup_notification",
            "[UPDATE": "loading_notification",
            "[SUCCESS": "ready_notification",
            "[WARNING": "shutdown_notification",
            "[STOP": "monitor_stop_notification"
        }
        
        for prefix, msg_type in message_types.items():
            if message.startswith(prefix):
                return msg_type
        return None

    def _load_config(self):
        """Load configuration from json file"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as config_file:
                    config = json.load(config_file)
                    self.logger.info("Configuration loaded successfully")
                    return config
            else:
                self.logger.warning(f"Config file not found at {self.config_path}. Creating default config.")
                default_config = {
                    "discord_enabled": "false",
                    "discord_webhook_url": "",
                    "server": {
                        "name": "Conan Exiles Server",
                        "logs_directory": "",
                        "startup_delay": 30,
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
                os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
                with open(self.config_path, 'w', encoding='utf-8') as config_file:
                    json.dump(default_config, config_file, indent=2)
                self.logger.info("Created default configuration file")
                return default_config
        except Exception as e:
            self.logger.error(f"Error loading config: {e}")
            return {}

    def is_enabled(self):
        """Check if Discord integration is enabled"""
        enabled = self.config.get('discord_enabled', 'false').lower() == 'true'
        webhook_url = self.config.get('discord_webhook_url', '')
        
        if enabled and not webhook_url:
            self.logger.warning("Discord is enabled but webhook URL is missing")
            return False
            
        return enabled

    def send_message(self, message):
        """Send message to Discord webhook if the message type is enabled"""
        if not self.is_enabled():
            self.logger.info("Discord messaging is disabled. Message not sent.")
            return

        try:
            message_type = self._get_message_type(message)
            if message_type and not self.message_control.get(message_type, True):
                self.logger.info(f"Message type '{message_type}' is disabled. Message not sent.")
                return

            webhook_url = self.config.get('discord_webhook_url')
            payload = {'content': message}
            
            response = requests.post(webhook_url, json=payload)
            response.raise_for_status()
            
            self.logger.info(f"Message sent to Discord: {message}")
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error sending message to Discord webhook: {e}")

    def start(self):
        """Placeholder method for compatibility with existing code"""
        if self.is_enabled():
            self.logger.info("Webhook manager ready")

    def stop(self):
        """Placeholder method for compatibility with existing code"""
        self.logger.info("Webhook manager stopped")