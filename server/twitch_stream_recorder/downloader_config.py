import os

from config import Config

root_path = Config.streams_root
username = os.environ.get('TWITCH_DEFAULT_USERNAME', 'ninja')
client_id = os.environ.get('TWITCH_CLIENT_ID', '')
client_secret = os.environ.get('TWITCH_SECRET_ID', '')
