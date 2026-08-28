FROM docker.io/library/python:3.8-slim-bullseye

ARG INSTALL_GCLOUD=false

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TOKENIZERS_PARALLELISM=true \
    CLIP_STORAGE_BACKEND=gcp \
    STREAMS_ROOT=/streams \
    CLIPS_ROOT=/clips \
    PANNS_DATA_DIR=/app/panns_data

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    streamlink \
    curl \
    procps \
    ca-certificates \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Optional: gsutil for original GCS clip uploads (CLIP_STORAGE_BACKEND=gcp)
RUN if [ "$INSTALL_GCLOUD" = "true" ]; then \
      curl -fsSL https://packages.cloud.google.com/apt/doc/apt-key.gpg \
        | gpg --dearmor -o /usr/share/keyrings/cloud.google.gpg \
      && echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" \
        > /etc/apt/sources.list.d/google-cloud-sdk.list \
      && apt-get update \
      && apt-get install -y --no-install-recommends google-cloud-cli \
      && rm -rf /var/lib/apt/lists/*; \
    fi

COPY server/requirements.txt ./server/requirements.txt
RUN pip install --no-cache-dir -r server/requirements.txt

RUN mkdir -p /app/panns_data \
    && curl -fsSL \
      https://raw.githubusercontent.com/qiuqiangkong/audioset_tagging_cnn/master/metadata/class_labels_indices.csv \
      -o /app/panns_data/class_labels_indices.csv

COPY server/ ./server/

WORKDIR /app/server

RUN chmod +x entrypoint.sh

EXPOSE 5555

ENTRYPOINT ["./entrypoint.sh"]
