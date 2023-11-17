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

"""Entry point for Cloud Run."""
import base64
import http
import json
import os

from absl import logging
import flask
import flask_cors
import google.cloud.logging

import execution_runner as execution_runner_lib
from data_models import settings as settings_lib

client = google.cloud.logging.Client()
client.setup_logging()

app = flask.Flask(__name__)
flask_cors.CORS(app)


@app.route('/run', methods=['POST'])
def main() -> flask.Response:
  """Entry point for Cloud Run."""
  logging.info('Received request: run/')

  source_language_code = flask.request.form.get('source_language_code').lower()
  target_language_codes = (
      flask.request.form.get('target_language_codes').lower().split(',')
  )
  customer_ids = flask.request.form.get('customer_ids').split(',')
  campaigns = flask.request.form.get('campaigns').split(',')
  workers_to_run = flask.request.form.get('workers_to_run').split(',')
  shorten_translations_to_char_limit = flask.request.form.get(
      'shorten_translations_to_char_limit',
      default=False,
      type=lambda v: v.lower() == 'true',
  )
  multiple_templates = flask.request.form.get(
      'multiple_templates', default=False, type=lambda v: v.lower() == 'true'
  )
  translate_ads = flask.request.form.get(
      'translate_ads', default=True, type=lambda v: v.lower() == 'true'
  )
  translate_keywords = flask.request.form.get(
      'translate_keywords', default=True, type=lambda v: v.lower() == 'true'
  )
  translate_extensions = flask.request.form.get(
      'translate_extensions', default=True, type=lambda v: v.lower() == 'true'
  )
  client_id = flask.request.form.get('client_id')
  glossary_id = flask.request.form.get('glossary_id')

  settings = settings_lib.Settings(
      source_language_code=source_language_code,
      target_language_codes=target_language_codes,
      customer_ids=customer_ids,
      campaigns=campaigns,
      workers_to_run=workers_to_run,
      shorten_translations_to_char_limit=shorten_translations_to_char_limit,
      multiple_templates=multiple_templates,
      client_id=client_id,
      translate_ads=translate_ads,
      translate_keywords=translate_keywords,
      translate_extensions=translate_extensions,
      glossary_id=glossary_id,
  )

  logging.info('Built run settings: %s', settings)

  execution_runner = execution_runner_lib.ExecutionRunner(settings)
  try:
    response_dict = execution_runner.run_workers()
  except Exception as exception:
    # (Isolation block for server)
    logging.error('Execution Runner raised an exception trying to run '
                  'workers: %s', exception)
    return flask.Response(
        ('The server encountered and error and could not complete your '
         'request. Developers can check the logs for details.'),
        http.HTTPStatus.INTERNAL_SERVER_ERROR)

  logging.info('Request complete: run/')

  return flask.make_response(flask.jsonify(response_dict), http.HTTPStatus.OK)


@app.route('/accessible_accounts', methods=['POST', 'GET'])
def get_accessible_accounts() -> flask.Response:
  """End point to get accounts.

  Returns:
    A list of dicts with account id and name.
  """
  logging.info('Received request: /accessible_accounts')

  settings = settings_lib.Settings()
  execution_runner = execution_runner_lib.ExecutionRunner(settings)

  try:
    accounts_list = execution_runner.get_accounts()
  except Exception as exception:
                                  # (Isolation block for server)
    logging.error('Execution Runner raised an exception trying to get '
                  'accessible accounts: %s', exception)
    return flask.Response(
        ('The server encountered and error and could not complete your '
         'request. Developers can check the logs for details.'),
        http.HTTPStatus.INTERNAL_SERVER_ERROR)

  logging.info('Request complete: /accessible_accounts')

  return flask.make_response(flask.jsonify(accounts_list), http.HTTPStatus.OK)


@app.route('/campaigns', methods=['POST', 'GET'])
def get_campaigns() -> flask.Response:
  """End point to get campaigns.

  The endpoints expects a request argument containing a list of selected account
  ids, e.g. [1234567890, 2345678901]

  Returns:
    A list of dicts with campaign id and name.
  """
  logging.info('Received request: /campaigns')

  selected_accounts = flask.request.form.get('selected_accounts').split(',')
  settings = settings_lib.Settings()
  execution_runner = execution_runner_lib.ExecutionRunner(settings)

  logging.info('Getting campaigns for: %s', selected_accounts)

  try:
    campaigns_list = execution_runner.get_campaigns_for_selected_accounts(
        selected_accounts
    )
  except Exception as exception:
                                  # (Isolation block for server)
    logging.error('Execution Runner raised an exception trying to get '
                  'campaigns: %s', exception)
    return flask.Response(
        ('The server encountered and error and could not complete your request.'
         ' Developers can check the logs for details.'),
        http.HTTPStatus.INTERNAL_SERVER_ERROR)

  logging.info('Request complete: /campaigns')

  return flask.make_response(flask.jsonify(campaigns_list), http.HTTPStatus.OK)


@app.route('/cost', methods=['POST'])
def get_cost() -> flask.Response:
  """End point to get cost estimate for translation.

  The endpoints expects a post request containing a list of selected customer
  ids and campaign ids.

  Returns:
    A response containing a string with the cost estimate and explanation.
  """
  logging.info('Received request: /cost')

  customer_ids = flask.request.form.get('customer_ids', '').split(',')
  campaigns = flask.request.form.get('campaigns', '').split(',')

  settings = settings_lib.Settings(
      customer_ids=customer_ids,
      campaigns=campaigns,
  )

  execution_runner = execution_runner_lib.ExecutionRunner(settings)

  logging.info('Getting cost estimate for: %s', campaigns)

  try:
    cost_estimate = execution_runner.get_cost_estimate()
  except Exception as exception:
    # (Isolation block for server)
    logging.error('Execution Runner raised an exception trying to get '
                  'cost estimate: %s', exception)
    return flask.Response(
        ('The server encountered and error and could not complete your request.'
         ' Developers can check the logs for details.'),
        http.HTTPStatus.INTERNAL_SERVER_ERROR)

  logging.info('Request complete: /cost')

  return flask.make_response(cost_estimate, http.HTTPStatus.OK)


@app.route('/list_glossaries', methods=['GET'])
def get_glossaries() -> flask.Response:
  """End point to get list of glossaries.

  Returns:
    A response containing a list of available glossaries.
  """
  logging.info('Received request: /list_glossaries')
  settings = settings_lib.Settings()
  execution_runner = execution_runner_lib.ExecutionRunner(settings)
  try:
    glossaries = execution_runner.list_glossaries()
  except Exception as exception:
    # (Isolation block for server)
    logging.error(
        'Cloud Translation Client raised an exception trying to get '
        'glossaries: %s',
        exception,
    )
    return flask.Response(
        ('The server encountered and error and could not complete your request.'
         ' Developers can check the logs for details.'),
        http.HTTPStatus.INTERNAL_SERVER_ERROR)
  logging.info('Request complete: /list_glossaries')

  return flask.make_response(glossaries, http.HTTPStatus.OK)


@app.route('/create_glossary', methods=['POST'])
def create_glossary() -> flask.Response:
  """End point to create a glossaries.

  Returns:
    A glossary operation response.
  """
  logging.info('Received request: /create_glossary')
  envelope = flask.request.get_json()
  if not envelope:
    msg = 'no Pub/Sub message received'
    logging.error('Bad Request: %s', msg)
    return flask.make_response(f'Bad Request: {msg}', 400)

  if not isinstance(envelope, dict) or 'message' not in envelope:
    msg = 'invalid Pub/Sub message format'
    logging.error('Bad Request: %s', msg)
    return flask.make_response(f'Bad Request: {msg}', 400)

  pubsub_message = envelope['message']
  event_data = json.loads(
      base64.b64decode(pubsub_message['data']).decode('utf-8').strip()
  )
  settings = settings_lib.Settings()
  execution_runner = execution_runner_lib.ExecutionRunner(settings)
  try:
    response = execution_runner.create_or_replace_glossary(event_data)
  except Exception as exception:
    # (Isolation block for server)
    logging.error(
        'Cloud Translation Client raised an exception trying to create a'
        ' glossary %s ',
        exception,
    )
    return flask.Response(
        (
            'The server encountered and error and could not complete your'
            ' request. Developers can check the logs for details.'
        ),
        http.HTTPStatus.INTERNAL_SERVER_ERROR,
    )
  logging.info('Request complete: /create_glossary')

  return flask.make_response(response, http.HTTPStatus.OK)


if __name__ == '__main__':
  app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
