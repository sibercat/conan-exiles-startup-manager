# core/discord_manager.py
import discord
from discord import Intents
import json
import logging
import os
import asyncio
from logging.handlers import RotatingFileHandler
import threading
from queue import Queue
import sys

class DiscordManager:
   def __init__(self, config_path='config/config.json'):
       # Setup base paths
       self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
       self.logs_dir = os.path.join(self.base_dir, 'logs')
       self.config_path = os.path.join(self.base_dir, config_path)
       self.client = None
       self.message_queue = Queue()
       self.discord_thread = None
       self.running = False
       
       # Setup logging
       self.setup_logging()
       self.logger = logging.getLogger('DiscordManager')
       
       # Load config
       self.config = self._load_config()
       
       # Setup Discord client if enabled
       if self.is_enabled():
           self._setup_client()
           self.logger.info("Discord manager initialized and enabled")
       else:
           self.logger.info("Discord manager initialized but disabled")

   def setup_logging(self):
       """Setup logging configuration"""
       if not os.path.exists(self.logs_dir):
           os.makedirs(self.logs_dir)

       log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
       log_file = os.path.join(self.logs_dir, 'discord_manager.log')
       
       # Setup file handler with UTF-8 encoding
       file_handler = RotatingFileHandler(
           log_file, 
           maxBytes=5*1024*1024,  # 5MB
           backupCount=5,
           encoding='utf-8'
       )
       file_handler.setFormatter(log_formatter)

       # Setup console handler for stdout
       console_handler = logging.StreamHandler(sys.stdout)
       console_handler.setFormatter(log_formatter)

       logger = logging.getLogger('DiscordManager')
       logger.setLevel(logging.INFO)

       if not logger.handlers:
           logger.addHandler(file_handler)
           logger.addHandler(console_handler)

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
                   "discord_bot_token": "",
                   "discord_channel_id": "",
                   "server": {
                       "name": "Conan Exiles Server",
                       "logs_directory": ""
                   }
               }
               # Create config directory if it doesn't exist
               os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
               # Create default config file
               with open(self.config_path, 'w', encoding='utf-8') as config_file:
                   json.dump(default_config, config_file, indent=2)
               self.logger.info("Created default configuration file")
               return default_config
       except Exception as e:
           self.logger.error(f"Error loading config: {e}")
           return {}

   def _setup_client(self):
       """Setup Discord client with appropriate intents"""
       try:
           intents = discord.Intents.default()
           intents.typing = False
           intents.presences = False
           
           self.client = discord.Client(intents=intents)
           
           @self.client.event
           async def on_ready():
               self.logger.info(f'Discord bot {self.client.user.name} is ready.')
               print(f'Discord bot {self.client.user.name} is ready.')
               # Start processing messages once the client is ready
               self.bg_task = asyncio.create_task(self._process_message_queue())

           @self.client.event
           async def on_error(event, *args, **kwargs):
               self.logger.error(f'Discord error in {event}: {args} {kwargs}')

       except Exception as e:
           self.logger.error(f"Error setting up Discord client: {e}")

   async def _process_message_queue(self):
       """Process messages in the queue"""
       while True:
           try:
               if not self.running:
                   break
                   
               if not self.message_queue.empty():
                   message = self.message_queue.get()
                   channel = self.client.get_channel(int(self.config.get('discord_channel_id', '0')))
                   if channel:
                       await channel.send(message)
                       self.logger.info(f"Message sent to Discord: {message}")
                   else:
                       self.logger.error("Discord channel not found")
                   self.message_queue.task_done()
               await asyncio.sleep(1)
           except Exception as e:
               self.logger.error(f"Error processing message queue: {e}")
               await asyncio.sleep(5)  # Wait longer on error

   def is_enabled(self):
       """Check if Discord integration is enabled"""
       enabled = self.config.get('discord_enabled', 'false').lower() == 'true'
       token = self.config.get('discord_bot_token', '')
       channel = self.config.get('discord_channel_id', '')
       
       if enabled and not (token and channel):
           self.logger.warning("Discord is enabled but token or channel ID is missing")
           return False
           
       return enabled

   def send_message(self, message):
       """Add message to the queue"""
       if self.is_enabled() and self.running:
           try:
               self.message_queue.put(message)
               self.logger.info(f"Message added to queue: {message}")
           except Exception as e:
               self.logger.error(f"Error adding message to queue: {e}")
       else:
           self.logger.info("Discord messaging is disabled or not running. Message not sent.")

   def start(self):
       """Start the Discord client in a separate thread"""
       if self.is_enabled():
           def run_client():
               try:
                   self.running = True
                   asyncio.run(self._start_client())
               except Exception as e:
                   self.logger.error(f"Error in Discord client thread: {e}")
               finally:
                   self.running = False

           self.discord_thread = threading.Thread(target=run_client, daemon=True)
           self.discord_thread.start()
           self.logger.info("Discord client thread started")

   async def _start_client(self):
       """Async method to start the Discord client"""
       if self.client:
           try:
               token = self.config.get('discord_bot_token', '')
               if not token:
                   self.logger.error("Discord bot token not found in config")
                   return
               await self.client.start(token)
           except Exception as e:
               self.logger.error(f"Error starting Discord client: {e}")

   def stop(self):
       """Stop the Discord client and clean up"""
       self.logger.info("Stopping Discord manager...")
       self.running = False
       
       if self.client and self.client.loop and not self.client.loop.is_closed():
           try:
               # Schedule the client close
               asyncio.run_coroutine_threadsafe(self.client.close(), self.client.loop)
           except Exception as e:
               self.logger.error(f"Error closing Discord client: {e}")

       # Wait for the thread to finish if it exists
       if self.discord_thread and self.discord_thread.is_alive():
           try:
               self.discord_thread.join(timeout=5)  # Wait up to 5 seconds
               if self.discord_thread.is_alive():
                   self.logger.warning("Discord thread did not terminate properly")
           except Exception as e:
               self.logger.error(f"Error joining Discord thread: {e}")

       self.logger.info("Discord manager stopped")

   def get_status(self):
       """Get the current status of the Discord manager"""
       return {
           "enabled": self.is_enabled(),
           "running": self.running,
           "connected": self.client and self.client.is_ready() if self.client else False,
           "channel_id": self.config.get('discord_channel_id', 'Not configured'),
           "bot_name": self.client.user.name if self.client and self.client.user else "Not connected",
           "messages_queued": self.message_queue.qsize()
       }