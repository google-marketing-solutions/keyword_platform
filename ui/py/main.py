# Copyright 2023 Google LLC.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
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
import urllib

import flask
import flask_cors
import google.auth.transport.requests
import google.oauth2.id_token


# The name of the environment variable containing the URL of the backend
# Cloud Run Python container.
_BACKEND_URL_ENV_VAR = 'BACKEND_URL'


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
  endpoint = flask.request.args.get('endpoint')
  params = urllib.parse.urlencode(flask.request.args)
  request = urllib.request.Request(f'{url}/{endpoint}?{params}')
  logging.info('Making request: %s', request)
  request.add_header('Authorization', f'Bearer {id_token}')

  return urllib.request.urlopen(request)


if __name__ == '__main__':
  app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
