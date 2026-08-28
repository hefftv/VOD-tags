#####################
# IMPORT LIBS
#####################

import os
import time
import uuid
from multiprocessing import Process

import flask
from flask import request

os.environ['TOKENIZERS_PARALLELISM'] = 'true'

from config import Config
from processor import StreamProcessor

app = flask.Flask(__name__)
app.config['DEBUG'] = os.environ.get('FLASK_DEBUG', 'True').lower() in (
    '1',
    'true',
    'yes',
)


@app.route('/health', methods=['GET'])
def health():
    return {'status': 'ok'}


@app.route('/process_stream', methods=['GET'])
def process_stream():
    saved_prediction_indices = []
    stream_link = request.args.get('stream_link')
    user_name = request.args.get('user_name')
    stream_uid = str(uuid.uuid1())
    file_path = Config.recorded_stream_path(stream_link, f'{stream_uid}.mp4')

    stream_processor = StreamProcessor(stream_link, user_name, stream_uid)
    download_process = stream_processor.download_stream()

    print(f'Working for user: {user_name} and stream {stream_link}')
    print(download_process.pid)

    while not os.path.isfile(file_path):
        time.sleep(1)

    prediction_process = Process(target=stream_processor.get_predictions)
    prediction_process.start()

    cut_process = None
    while True:
        time_start, duration, saved_prediction_indices = (
            stream_processor.check_predictions(saved_prediction_indices)
        )

        if time_start is not None:
            cut_process = stream_processor.extract_time_frame(time_start, duration)
            if cut_process is not None:
                cut_process.wait()
            public_clip_path = stream_processor.publish_clip()
            stream_processor.send_clip_to_webapp(public_clip_path)
            if Config.uses_gcs():
                print('Clip added to google storage!')
            else:
                print('Clip published locally!')

        time.sleep(30)

    os.remove(f'{stream_uid}.csv')
    stream_processor.process_killer()
    if cut_process is not None:
        cut_process.terminate()
    download_process.terminate()
    return ''


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('ML_SERVER_PORT', '5555')))
