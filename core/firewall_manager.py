# core/firewall_manager.py

import subprocess
from typing import List, Dict
from core.default_config import CONSTANTS

class FirewallManager:
    def __init__(self, logger, enabled: bool = True):
        self.logger = logger
        self.enabled = enabled
        self.rule_prefix = CONSTANTS["RULE_NAME_PREFIX"]

    def block_ports(self, ports: List[Dict[str, str]]) -> None:
        """Block configured ports using Windows Firewall"""
        if not self.enabled:
            self.logger.info("Firewall management disabled, skipping port blocking.")
            return

        try:
            for port_info in ports:
                rule_name = f"{self.rule_prefix}_{port_info['port']}_{port_info['proto']}"
                cmd = f'netsh advfirewall firewall add rule name="{rule_name}" dir=in action=block protocol={port_info["proto"]} localport={port_info["port"]}'
                subprocess.run(cmd, shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.logger.info("All ports blocked successfully.")
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Error blocking ports: {e}")

    def allow_ports(self, ports: List[Dict[str, str]]) -> None:
        """Allow configured ports by removing blocking rules"""
        if not self.enabled:
            self.logger.info("Firewall management disabled, skipping port allowing.")
            return

        try:
            for port_info in ports:
                rule_name = f"{self.rule_prefix}_{port_info['port']}_{port_info['proto']}"
                cmd = f'netsh advfirewall firewall delete rule name="{rule_name}"'
                subprocess.run(cmd, shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.logger.info("All ports allowed successfully.")
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Error allowing ports: {e}")