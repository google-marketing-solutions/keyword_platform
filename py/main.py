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
from concurrent import futures
import http
import json
import logging
import os

import flask

from py import execution_runner as execution_runner_lib
from py.data_models import settings as settings_lib

app = flask.Flask(__name__)


@app.route('/run', methods=['POST'])
def main() -> flask.Response:
  """Entry point for Cloud Run."""
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
  execution_runner = execution_runner_lib.ExecutionRunner(settings)
  try:
    response_dict = execution_runner.run_workers()
  except RuntimeError as err:
    logging.error('Execution Runner raised an exception: %s', err)
    return flask.Response(status=http.HTTPStatus.BAD_REQUEST, content=err)
  return flask.make_response(flask.jsonify(response_dict), http.HTTPStatus.OK)


@app.route('/accessible_accounts', methods=['POST', 'GET'])
def get_accessible_accounts() -> flask.Response:
  """End point to get accounts.

  Returns:
    A list of dicts with account id and name.
  """
  settings = settings_lib.Settings()
  execution_runner = execution_runner_lib.ExecutionRunner(settings)
  try:
    accounts_list = execution_runner.get_accounts()
  except RuntimeError as err:
    logging.error('Google Ads Client raised an exception: %s', err)
    return flask.Response(status=http.HTTPStatus.BAD_REQUEST, content=err)
  return flask.make_response(flask.jsonify(accounts_list), http.HTTPStatus.OK)


@app.route('/campaigns', methods=['POST', 'GET'])
def get_campaigns() -> flask.Response:
  """End point to get campaigns.

  The endpoints expects a request argument containing a list of selected account
  ids, e.g. [1234567890, 2345678901]

  Returns:
    A list of dicts with campaign id and name.
  """
  selected_accounts = flask.request.args.get('selected_accounts').split(',')
  settings = settings_lib.Settings()
  execution_runner = execution_runner_lib.ExecutionRunner(settings)

  try:
    campaigns_list = execution_runner.get_campaigns_for_selected_accounts(
        selected_accounts
    )
  except RuntimeError as err:
    logging.error('Google Ads Client raised an exception: %s', err)
    return flask.Response(status=http.HTTPStatus.BAD_REQUEST, content=err)
  return flask.make_response(flask.jsonify(campaigns_list), http.HTTPStatus.OK)


if __name__ == '__main__':
  app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
