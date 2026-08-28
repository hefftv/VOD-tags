import os


class Config:
    #####################
    # GCP / original deployment (defaults preserved)
    #####################

    twitch_download_app_path = 'twitch_stream_recorder/twitch-recorder.py'
    google_cloud_storage_bucket_name = os.environ.get(
        'GCS_BUCKET_NAME',
        'YOUR-GOOGLE-CLOUD-STORAGE-BUCKET-NAME',
    )
    webapp_public_ip = os.environ.get('WEBAPP_PUBLIC_IP', '34.122.9.136')
    webapp_public_port = os.environ.get('WEBAPP_PUBLIC_PORT', '5555')

    #################
    # TWITCH OAUTH
    #################

    nickname = os.environ.get('TWITCH_CHAT_NICKNAME', 'YOUR-TWITCH-NAME')
    secret_id = os.environ.get('TWITCH_SECRET_ID', 'YOUR-TWITCH-SECRET-ID')
    oauth_token = os.environ.get('TWITCH_OAUTH_TOKEN', 'YOUR-TWITCH-OAUTH-TOKEN')

    #####################
    # Multi-environment scaffolding
    #####################

    # gcp (default): upload clips with gsutil to a public GCS bucket
    # local: publish clips to a shared volume / nginx (docker compose --profile full)
    clip_storage_backend = os.environ.get('CLIP_STORAGE_BACKEND', 'gcp').lower()

    streams_root = os.environ.get('STREAMS_ROOT', '../../streams')
    clips_root = os.environ.get('CLIPS_ROOT', '/clips')
    clip_public_base_url = os.environ.get(
        'CLIP_PUBLIC_BASE_URL',
        'http://localhost:8080',
    ).rstrip('/')
    panns_data_dir = os.environ.get('PANNS_DATA_DIR', '/app/panns_data')

    @classmethod
    def webapp_callback_host(cls):
        return os.environ.get('WEBAPP_HOST', cls.webapp_public_ip)

    @classmethod
    def webapp_callback_port(cls):
        return os.environ.get('WEBAPP_PORT', cls.webapp_public_port)

    @classmethod
    def uses_gcs(cls):
        return cls.clip_storage_backend in ('gcp', 'gcs', '')

    @classmethod
    def uses_local_clips(cls):
        return cls.clip_storage_backend == 'local'

    @classmethod
    def recorded_stream_path(cls, channel_name, filename):
        return os.path.join(cls.streams_root, 'recorded', channel_name, filename)

    @classmethod
    def panns_labels_path(cls):
        return os.path.join(cls.panns_data_dir, 'class_labels_indices.csv')

    @classmethod
    def gcs_public_clip_url(cls, clip_name):
        return (
            f'https://storage.googleapis.com/'
            f'{cls.google_cloud_storage_bucket_name}/{clip_name}'
        )
