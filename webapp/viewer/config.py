import os


class Config:
    client_id = os.environ.get('TWITCH_CLIENT_ID', '')
    secret_id = os.environ.get('TWITCH_SECRET_ID', '')
    server_ip = os.environ.get('ML_SERVER_HOST', '')
    server_port = os.environ.get('ML_SERVER_PORT', '5555')
