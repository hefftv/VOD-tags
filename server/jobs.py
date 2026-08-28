import os
import threading
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from multiprocessing import Process
from typing import Dict, Optional

from config import Config
from processor import StreamProcessor

_jobs: Dict[str, 'StreamJob'] = {}
_lock = threading.Lock()


@dataclass
class StreamJob:
    job_id: str
    stream_link: str
    user_name: str
    stream_uid: str
    status: str = 'queued'
    error: Optional[str] = None
    clips_published: int = 0
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self):
        return {
            'job_id': self.job_id,
            'stream_link': self.stream_link,
            'user_name': self.user_name,
            'stream_uid': self.stream_uid,
            'status': self.status,
            'error': self.error,
            'clips_published': self.clips_published,
            'artifact_dir': Config.job_artifact_dir(self.stream_uid),
            'created_at': self.created_at,
            'updated_at': self.updated_at,
        }

    def _touch(self, status: str):
        self.status = status
        self.updated_at = datetime.now(timezone.utc).isoformat()


def get_job(job_id: str) -> Optional[StreamJob]:
    with _lock:
        return _jobs.get(job_id)


def list_jobs() -> list:
    with _lock:
        return [job.to_dict() for job in _jobs.values()]


def _register_job(job: StreamJob):
    with _lock:
        _jobs[job.job_id] = job


def run_stream_pipeline(job: StreamJob):
    saved_prediction_indices = []
    download_process = None
    prediction_process = None
    cut_process = None

    try:
        job._touch('recording')
        file_path = Config.recorded_stream_path(job.stream_link, f'{job.stream_uid}.mp4')
        processor = StreamProcessor(job.stream_link, job.user_name, job.stream_uid)
        download_process = processor.download_stream()

        while not os.path.isfile(file_path):
            time.sleep(1)

        job._touch('processing')
        prediction_process = Process(target=processor.get_predictions)
        prediction_process.start()

        while True:
            time_start, duration, saved_prediction_indices = processor.check_predictions(
                saved_prediction_indices,
            )

            if time_start is not None:
                cut_process = processor.extract_time_frame(time_start, duration)
                if cut_process is not None:
                    cut_process.wait()
                public_clip_path = processor.publish_clip()
                processor.send_clip_to_webapp(public_clip_path)
                job.clips_published += 1
                job.updated_at = datetime.now(timezone.utc).isoformat()
                if Config.uses_gcs():
                    print('Clip added to google storage!')
                else:
                    print('Clip published locally!')

            time.sleep(30)
    except Exception as exc:
        job.error = str(exc)
        job._touch('failed')
        print(f'Job {job.job_id} failed: {exc}')
    finally:
        if prediction_process is not None and prediction_process.is_alive():
            prediction_process.terminate()
        if cut_process is not None:
            cut_process.terminate()
        if download_process is not None:
            download_process.terminate()


def start_stream_job(stream_link: str, user_name: str) -> StreamJob:
    stream_uid = str(uuid.uuid1())
    job = StreamJob(
        job_id=str(uuid.uuid4()),
        stream_link=stream_link,
        user_name=user_name,
        stream_uid=stream_uid,
    )
    Config.ensure_job_artifact_dir(stream_uid)
    _register_job(job)
    thread = threading.Thread(target=run_stream_pipeline, args=(job,), daemon=True)
    thread.start()
    return job
