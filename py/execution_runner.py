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

"""Executes workers to produce expanded / optimized Google Ads objects."""

from concurrent import futures
import math
import os
import time
from typing import Any

from absl import logging
import google.auth
from google.cloud import secretmanager

from common import cloud_translation_client as cloud_translation_client_lib
from common import execution_analytics_client as execution_analytics_client_lib
from common import google_ads_client as google_ads_client_lib
from common import storage_client as storage_client_lib
from common import vertex_client as vertex_client_lib
from data_models import accounts as accounts_lib
from data_models import ad_groups as ad_groups_lib
from data_models import ads as ads_lib
from data_models import campaigns as campaigns_lib
from data_models import extensions as extensions_lib
from data_models import google_ads_objects as google_ads_objects_lib
from data_models import keywords as keywords_lib
from data_models import settings as settings_lib
from workers import translation_worker as translation_worker_lib
from workers import worker_result

# Based on $20 / 1M chars https://cloud.google.com/translate/pricing
_TRANSLATION_PRICE_PER_CHAR_USD = 20.0/1000000.0

_WORKERS = {
    'translationWorker': translation_worker_lib.TranslationWorker,
    # Add new workers here, and they will be processed automatically.
}

_REQUIRED_SECRET_KEYS = [
    'developer_token',
    'client_id',
    'client_secret',
    'refresh_token',
    'login_customer_id',
]


class ExecutionRunner:
  """Executes workers to produce expanded / optimized Google Ads objects.

  This class serves as the main entry point for code logic. This logic is
  decoupled from the "main" entrypoint logic so it can be used independently of
  UI / web framework implementation.
  """

  def __init__(self, settings: settings_lib.Settings) -> None:
    """Initializes the ExecutionRunner class.

    Args:
      settings: The settings to use for this execution run.
    """
    self._settings = settings
    self._gcp_project_id = os.environ['GCP_PROJECT']
    self._gcp_region = os.environ['GCP_REGION']
    self._settings.credentials = self._get_credentials()
    self._bucket_name = os.environ['BUCKET_NAME']
    self._ga_opt_out = os.environ['GA_OPT_OUT'].lower() == 'true'

    logging.info('ExecutionRunner: initialized credentials.')

    try:
      self._vertex_client = vertex_client_lib.VertexClient()
      logging.info('ExecutionRunner: initialized Vertex API client.')
    except google.api_core.exceptions.PermissionDenied as err:
      self._vertex_client = None
      logging.info(
          'ExecutionRunner: Vertex API client could not be initialized.'
          ' Vertex AI will not be used: %s',
          err,
      )
    except google.api_core.exceptions.InternalServerError as err:
      self._vertex_client = None
      logging.exception(
          'ExecutionRunner: Vertex API client could not be initialized.'
          ' Vertex AI will not be used: %s',
          err,
      )

    self._google_ads_client = google_ads_client_lib.GoogleAdsClient(
        self._settings.credentials)

    logging.info('ExecutionRunner: initialized Google Ads client.')

    self._cloud_translation_client = (
        cloud_translation_client_lib.CloudTranslationClient(
            credentials=self._settings.credentials,
            gcp_project_name=self._gcp_project_id,
            gcp_region=self._gcp_region,
            vertex_client=self._vertex_client,
            shorten_translations_to_char_limit=(
                self._settings.shorten_translations_to_char_limit
            ),
        )
    )

    logging.info('ExecutionRunner: initialized Cloud Translation client.')

    if not self._ga_opt_out:
      self._execution_analytics_client = (
          execution_analytics_client_lib.ExecutionAnalyticsClient(
              settings=self._settings
          )
      )
      logging.info('ExecutionRunner: initialized Execution Analytics client.')
    else:
      self._execution_analytics_client = None
    logging.info('ExecutionRunner: initialization complete.')

  def _get_credentials(self) -> dict[str, str]:
    """Gets credentials from Cloud Secret Manager.

    Returns:
      A dictionary containing API credentials.
    """
    logging.info('Building credentials...')

    secret_manager_client = secretmanager.SecretManagerServiceClient()
    credentials = {}

    for secret_key in _REQUIRED_SECRET_KEYS:
      full_secret_name = (
          f'projects/{self._gcp_project_id}/secrets/{secret_key}/versions/'
          'latest')
      secret_response = secret_manager_client.access_secret_version(
          request={'name': full_secret_name}
      )
      credentials[
          secret_key] = secret_response.payload.data.decode('UTF-8').strip()

    return credentials

  def run_workers(self) -> dict[str, Any]:
    """Runs the selected workers and saves output as a csv.

    Returns:
      A dictionary consisting of:
        'worker_results': A list of results for each worker that was run.
        'asset_urls': A dictionary of filetypes with list of URLs for saved
            assets.
    """
    # UI validation should confirm at least 1 worker is selected, but in case
    # that fails, this check will exit early.
    if not self._settings.workers_to_run:
      logging.exception('No workers selected. Exiting...')
      return {'worker_results': [], 'asset_urls': {}}

    google_ads_objects = self._build_google_ads_objects()
    logging.info('Finished fetching Google Ads objects')

    results = self._run_workers(google_ads_objects)

    logging.info('RESULTS SUMMARY:')
    for worker, result in results.items():
      logging.info('Worker: %s | Result: %s', worker, result)

    asset_urls = self._save_to_bucket(google_ads_objects)

    logging.info('Wrote assets to Cloud Storage.')
    logging.info('Execution complete.')

    return {'worker_results': results, 'asset_urls': asset_urls}

  def get_accounts(self) -> list[accounts_lib.Account]:
    """Returns a list of accessible account objects."""
    login_customer_id = self._settings.credentials['login_customer_id']

    logging.info('Getting accounts for %s...', login_customer_id)
    accounts_responses = self._google_ads_client.get_accounts(
        mcc_id=login_customer_id
    )

    logging.info('Finished getting accounts for %s.', login_customer_id)

    return accounts_lib.Accounts(accounts_responses).accounts_list

  def get_campaigns_for_selected_accounts(
      self, selected_accounts: list[str]
  ) -> list[dict[str, str]]:
    """Gets the campaigns for the selected accounts.

    Args:
      selected_accounts: A list of selected account ids, e.g. [1234567890,
        2345678901]

    Returns:
      A list of dicts with campaign id and name.
    """
    with futures.ThreadPoolExecutor() as executor:
      responses = executor.map(
          self._google_ads_client.get_campaigns_for_account, selected_accounts
      )

    campaign_responses = [
        response for response in responses if isinstance(response, list)
    ]

    campaigns_list = campaigns_lib.Campaigns(
        campaign_responses
    ).campaigns_list()

    logging.info('Feteched %d campaigns', len(campaigns_list))

    return campaigns_list

  def get_cost_estimate(self) -> dict[str, str]:
    """Gets an estimated cost for translation.

    Returns:
      A message with the estimated cost.
    """
    google_ads_objects = self._build_google_ads_objects()
    logging.info('Finished fetching Google Ads objects')

    ads_char_count = (
        google_ads_objects.ads.char_count() if google_ads_objects.ads else 0
    )
    extensions_char_count = (
        google_ads_objects.extensions.char_count()
        if google_ads_objects.extensions
        else 0
    )
    keywords_char_count = (
        google_ads_objects.keywords.char_count()
        if google_ads_objects.keywords
        else 0
    )

    total_cost_usd_str = '{:.2f}'.format(
        (ads_char_count + extensions_char_count + keywords_char_count)
        * _TRANSLATION_PRICE_PER_CHAR_USD
    )

    cost_per_char_str = '{:f}'.format(_TRANSLATION_PRICE_PER_CHAR_USD)

    return {
        'total_cost_usd': total_cost_usd_str,
        'ads_char_count': str(ads_char_count),
        'extensions_char_count': str(extensions_char_count),
        'keywords_char_count': str(keywords_char_count),
        'cost_per_char': cost_per_char_str,
    }

  def _build_google_ads_objects(
      self,
  ) -> google_ads_objects_lib.GoogleAdsObjects:
    """Calls the Google Ads API to fetch Google Ads data.

    Returns:
      A GoogleAdsObjects instance containing Campaigns, Ad Groups, Ads,
      Keywords, and Extensions.
    """
    campaigns = self._build_campaigns()
    ads, ad_groups = self._build_ads_and_ad_groups()
    keywords = self._build_keywords()
    extensions = self._build_extensions()

    return google_ads_objects_lib.GoogleAdsObjects(
        ads, ad_groups, campaigns, keywords, extensions
    )

  def _build_campaigns(self) -> campaigns_lib.Campaigns:
    """Builds a Campaigns object."""
    campaign_responses = []
    customer_ids = self._settings.customer_ids
    campaigns = self._settings.campaigns

    with futures.ThreadPoolExecutor() as executor:
      responses = executor.map(
          lambda customer_id: self._google_ads_client.get_campaigns_for_account(
              customer_id, campaigns
          ),
          customer_ids,
      )

    for response in responses:
      if isinstance(response, list):
        campaign_responses.append(response)

    return campaigns_lib.Campaigns(campaign_responses)

  def _build_ads_and_ad_groups(
      self) -> tuple[ads_lib.Ads | None, ad_groups_lib.AdGroups]:
    """Builds Ads and Ad Groups objects."""
    ads_data_responses = []
    campaigns = self._settings.campaigns
    customer_ids = self._settings.customer_ids

    with futures.ThreadPoolExecutor() as executor:
      responses = executor.map(
          lambda customer_id:
          self._google_ads_client.get_ads_data_for_campaigns(
              customer_id, campaigns), customer_ids)

    for response in responses:
      if isinstance(response, list):
        ads_data_responses.append(response)

    if self._settings.translate_ads:
      ads = ads_lib.Ads(ads_data_responses)
    else:
      logging.info('Skipping ads translation.')
      ads = None

    ad_groups = ad_groups_lib.AdGroups(ads_data_responses)

    return ads, ad_groups

  def _build_extensions(
      self,
  ) -> extensions_lib.Extensions | None:
    """Builds an Extensions object."""
    if self._settings.translate_extensions:
      extensions_data_responses = []
      campaigns = self._settings.campaigns
      customer_ids = self._settings.customer_ids

      with futures.ThreadPoolExecutor() as executor:
        responses = executor.map(
            lambda customer_id: self._google_ads_client.get_extensions_for_campaigns(
                customer_id, campaigns
            ),
            customer_ids,
        )

      for response in responses:
        if isinstance(response, list):
          extensions_data_responses.append(response)
      extensions = extensions_lib.Extensions(extensions_data_responses)
    else:
      logging.info('Skipping extensions translation.')
      extensions = None
    return extensions

  def _build_keywords(self) -> keywords_lib.Keywords | None:
    """Builds a Keywords object."""
    keywords_responses = []
    customer_ids = self._settings.customer_ids
    campaigns = self._settings.campaigns

    with futures.ThreadPoolExecutor() as executor:
      responses = executor.map(
          lambda customer_id: self._google_ads_client.get_keywords_data_for_campaigns(
              customer_id, campaigns
          ),
          customer_ids,
      )

    for response in responses:
      if isinstance(response, list):
        keywords_responses.append(response)

    if self._settings.translate_keywords:
      keywords = keywords_lib.Keywords(keywords_responses)
    else:
      logging.info('Skipping keywords translation.')
      keywords = None
    return keywords

  def _run_workers(
      self, google_ads_objects: google_ads_objects_lib.GoogleAdsObjects
  ) -> dict[str, worker_result.WorkerResult]:
    """Runs the Google Ads workers to transform Google Ads Objects.

    Args:
      google_ads_objects: The Google Ads Objects to transform.

    Returns:
      A dictionary containing the names of the worker run, and the result of
        that worker run.
    """
    results = {}
    # TODO: b/300917779 - Extract to a util function somewhere and add tests.
    start_ms = math.floor(time.time() * 1000)
    for worker_id in self._settings.workers_to_run:
      worker = _WORKERS[worker_id](
          cloud_translation_client=self._cloud_translation_client,
          vertex_client=self._vertex_client,
      )

      logging.info('Running %s...', worker.name)
      result = worker.execute(self._settings, google_ads_objects)
      end_ms = math.floor(time.time() * 1000)
      duration_ms = end_ms - start_ms
      result.duration_ms = duration_ms
      results[worker.name] = result
      logging.info('Finished running %s.', worker.name)

      if self._execution_analytics_client:
        self._execution_analytics_client.send_worker_result(worker_id, result)
        logging.info('Finished sending results to GA4.')

    return results

  def _save_to_bucket(
      self, google_ads_objects: google_ads_objects_lib.GoogleAdsObjects
  ) -> dict[str, list[str]]:
    """Saves the Google Ads objects to a cloud storage bucket.

    Args:
      google_ads_objects: The Google Ads objects to save.

    Returns:
      A list URL strings to download the generated CSV files.
    """
    storage_client = storage_client_lib.StorageClient(
        bucket_name=self._bucket_name,
        google_ads_objects=google_ads_objects,
        multiple_templates=self._settings.multiple_templates,
    )

    return storage_client.export_google_ads_objects_to_gcs()

  def list_glossaries(self) -> list[cloud_translation_client_lib.Glossary]:
    """Gets a list of available glossaries."""
    return self._cloud_translation_client.list_glossaries()

  def create_or_replace_glossary(self, cloud_event_data: dict[str, Any]) -> Any:
    """Creates or replaces a glossary.

    Args:
      cloud_event_data: A cloud event data object.

    Returns:
      The glossary operation response.
    """
    glossary_id, source_language, target_language, glossary_uri = (
        self._cloud_translation_client.get_glossary_info_from_cloud_event_data(
            cloud_event_data
        )
    )
    return self._cloud_translation_client.create_or_replace_glossary(
        glossary_id, source_language, target_language, glossary_uri
    )
