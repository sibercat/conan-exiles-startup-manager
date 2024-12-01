# core/config_manager.py

import os
import json
from typing import List, Dict
from core.default_config import DEFAULT_CONFIG, DEFAULT_SERVER_CONFIG

class ConfigManager:
    def __init__(self, config_path: str, logger):
        self.config_path = config_path
        self.logger = logger
        self.config = self._load_config()

    def _load_config(self) -> dict:
        """Load configuration from json file or return default if not exists"""
        try:
            with open(self.config_path, 'r') as config_file:
                return json.load(config_file)
        except Exception as e:
            self.logger.error(f"Error loading config: {e}")
            return DEFAULT_CONFIG.copy()

    def get_firewall_enabled(self) -> bool:
        """Get firewall enabled setting"""
        return self.config.get('server', {}).get('firewall_enabled', 
            DEFAULT_SERVER_CONFIG['firewall_enabled'])

    def get_zombie_config(self) -> dict:
        """Get zombie detection configuration"""
        return self.config.get('server', {}).get('zombie_detection', 
            DEFAULT_SERVER_CONFIG['zombie_detection'])

    def get_ports(self) -> List[Dict[str, str]]:
        """Get configured ports"""
        return self.config.get('server', {}).get('ports', 
            DEFAULT_SERVER_CONFIG['ports'])

    def get_startup_delay(self) -> int:
        """Get server startup delay"""
        return int(self.config.get('server', {}).get('startup_delay', 
            DEFAULT_SERVER_CONFIG['startup_delay']))

    def get_messages(self) -> Dict[str, str]:
        """Get configured messages"""
        return self.config.get('server', {}).get('messages', 
            DEFAULT_SERVER_CONFIG['messages'])