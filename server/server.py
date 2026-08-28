#####################
# IMPORT LIBS
#####################

import os

import flask
from flask import request

os.environ['TOKENIZERS_PARALLELISM'] = 'true'

from jobs import get_job, list_jobs, start_stream_job

app = flask.Flask(__name__)
app.config['DEBUG'] = os.environ.get('FLASK_DEBUG', 'True').lower() in (
    '1',
    'true',
    'yes',
)


@app.route('/health', methods=['GET'])
def health():
    return {'status': 'ok'}


@app.route('/jobs', methods=['GET'])
def jobs_index():
    return {'jobs': list_jobs()}


@app.route('/jobs/<job_id>', methods=['GET'])
def jobs_show(job_id):
    job = get_job(job_id)
    if job is None:
        return {'error': 'job not found'}, 404
    return job.to_dict()


@app.route('/process_stream', methods=['GET'])
def process_stream():
    stream_link = request.args.get('stream_link')
    user_name = request.args.get('user_name')

    if not stream_link or not user_name:
        return {'error': 'stream_link and user_name are required'}, 400

    job = start_stream_job(stream_link, user_name)
    return job.to_dict(), 202


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('ML_SERVER_PORT', '5555')))
