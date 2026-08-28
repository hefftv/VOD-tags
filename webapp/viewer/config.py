import os


class Config:
    #####################
    # TWITCH CONFIG
    #####################

    client_id = os.environ.get('TWITCH_CLIENT_ID', 'TWITCH-CLIENT-ID')
    secret_id = os.environ.get('TWITCH_SECRET_ID', 'TWITCH-SECRET-ID')

    # ML server target (compose/local). Original GCP deploy used public IP + port 5555.
    server_ip = os.environ.get('ML_SERVER_HOST', os.environ.get('SERVER_IP', ''))
    server_port = os.environ.get('ML_SERVER_PORT', os.environ.get('SERVER_PORT', '5555'))
