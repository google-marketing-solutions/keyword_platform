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
import http
import logging
import os

import flask

from . import execution_runner as execution_runner_lib
from ..data_models import settings as settings_lib

app = flask.Flask(__name__)


@app.route('/run', methods=['POST'])
def main() -> flask.Response:
  """Entry point for Cloud Run."""
  logging.info('Received request: run/')

  source_language_code = flask.request.args.get('source_language_code').lower()
  target_language_codes = (
      flask.request.args.get('target_language_codes').lower().split(',')
  )
  customer_ids = flask.request.args.get('customer_ids').split(',')
  campaigns = flask.request.args.get('campaigns').split(',')
  workers_to_run = flask.request.args.get('workers_to_run').split(',')
  settings = settings_lib.Settings(
      source_language_code=source_language_code,
      target_language_codes=target_language_codes,
      customer_ids=customer_ids,
      campaigns=campaigns,
      workers_to_run=workers_to_run,
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
        status=http.HTTPStatus.INTERNAL_SERVER_ERROR,
        content=('The server encountered and error and could not complete your '
                 'request. Developers can check the logs for details.'))

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
        status=http.HTTPStatus.INTERNAL_SERVER_ERROR,
        content=('The server encountered and error and could not complete your '
                 'request. Developers can check the logs for details.'))

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

  selected_accounts = flask.request.args.get('selected_accounts').split(',')
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
        status=http.HTTPStatus.INTERNAL_SERVER_ERROR,
        content=('The server encountered and error and could not complete your '
                 'request. Developers can check the logs for details.'))

  logging.info('Request complete: /campaigns')

  return flask.make_response(flask.jsonify(campaigns_list), http.HTTPStatus.OK)


if __name__ == '__main__':
  app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
