#!/usr/bin/env sh
set -e

mkdir -p "${STREAMS_ROOT}" "${CLIPS_ROOT}"
exec python server.py
