# Copyright 2024 Google LLC.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Frontend server for serving static files and proxying secure requests.

Requests to the backend container must be authenticated to enable secure
container-to-container communication in Cloud Run. This lightweight server
serves static web content, and attaches authorization headers to requests to the
backend container.
"""

import logging
import os
import signal as signal_lib
import sys
import types
import urllib


import flask
import flask_cors
import google.auth.transport.requests
import google.cloud.logging
import google.oauth2.id_token


# The name of the environment variable containing the URL of the backend
# Cloud Run Python container.
_BACKEND_URL_ENV_VAR = 'BACKEND_URL'

client = google.cloud.logging.Client()
client.setup_logging()

app = flask.Flask(
    __name__,
    static_url_path='',
    static_folder='/var/www',
    template_folder='/var/www',
)
flask_cors.CORS(app)


@app.route('/')
def index() -> flask.Response:
  """Serves the main Angular page."""
  return flask.send_from_directory('/var/www', 'index.html')


@app.route('/favicon.ico')
def favicon() -> flask.Response:
  """Serves the favicon."""
  return flask.send_from_directory(
      '/var/www', 'favicon.ico', mimetype='image/vnd.microsoft.icon'
  )


@app.route('/proxy', methods=['POST', 'GET'])
def proxy() -> flask.Response:
  """Makes a secure request to the backend Python container."""
  logging.info('Received proxy request')

  # Gets the id token to make a secure request.
  auth_request = google.auth.transport.requests.Request()
  url = os.environ.get(_BACKEND_URL_ENV_VAR)
  id_token = google.oauth2.id_token.fetch_id_token(auth_request, url)

  if id_token:
    logging.info('Got id_token for %s', url)
  else:
    logging.warning('Failed to get id_token for %s', url)

  # Makes the request to the backend container endpoint.

  if flask.request.method == 'GET':
    # Builds and sends GET request
    endpoint = flask.request.args.get('endpoint')
    params = urllib.parse.urlencode(flask.request.args)
    request = urllib.request.Request(f'{url}/{endpoint}?{params}')
    logging.info('Making GET request: %s', request)
    request.add_header('Authorization', f'Bearer {id_token}')

    return urllib.request.urlopen(request)
  else:
    # Builds and sends POST request
    data = ''
    endpoint = ''

    if flask.request.form:
      endpoint = flask.request.form.get('endpoint')
      data = urllib.parse.urlencode(flask.request.form)
    elif flask.request.json:
      endpoint = flask.request.json.get('endpoint')
      data = urllib.parse.urlencode(flask.request.json)

    data = data.encode('utf-8')
    request = urllib.request.Request(f'{url}/{endpoint}', data)
    logging.info('Making POST request: %s', request)
    request.add_header('Authorization', f'Bearer {id_token}')

    return urllib.request.urlopen(request)


# [START cloudrun_sigterm_handler]
def shutdown_handler(signal: int, frame: types.FrameType) -> None:
  """Gracefully shutdown app."""
  del frame  # Unused.
  logging.info('Signal received: %s. Shutting down.', signal)
  sys.exit(0)


if __name__ == '__main__':
  # handles Ctrl-C locally
  signal_lib.signal(signal_lib.SIGINT, shutdown_handler)

  app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
else:
  # handles Cloud Run container termination
  signal_lib.signal(signal_lib.SIGTERM, shutdown_handler)
