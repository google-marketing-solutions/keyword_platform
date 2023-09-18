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

"""Translation Google Ads Worker."""


from absl import logging
import requests

from data_models import ad_groups as ad_groups_lib
from data_models import ads as ads_lib
from data_models import campaigns as campaigns_lib
from data_models import google_ads_objects as google_ads_objects_lib
from data_models import keywords as keywords_lib
from data_models import settings as settings_lib
from workers import base_worker
from workers import worker_result


class TranslationWorker(base_worker.BaseWorker):
  """Translates keywords, and ad headlines / descriptions."""

  def execute(
      self,
      settings: settings_lib.Settings,
      google_ads_objects: google_ads_objects_lib.GoogleAdsObjects
  ) -> worker_result.WorkerResult:
    """Performs the work to translate keywords, and ad headlines / descriptions.

    Args:
      settings: The user settings, passed in via the UI.
      google_ads_objects: The Google Ads objects to transform.

    Returns:
      A summary of results based on the work done by this worker.
    """
    logging.info('Starting execution: %s', self.name)

    if not google_ads_objects.keywords or not google_ads_objects.ads:
      logging.warning('Skipping translation: Google Ads or Keywords empty.')
      return worker_result.WorkerResult(
          status=worker_result.Status.FAILURE,
          warning_msg='Skipping translation: Google Ads or Keywords empty.',
      )

    self._translate_keywords(
        keywords=google_ads_objects.keywords,
        source_language_code=settings.source_language_code,
        target_language_code=settings.target_language_codes[0])

    self._translate_ads(
        ads=google_ads_objects.ads,
        source_language_code=settings.source_language_code,
        target_language_code=settings.target_language_codes[0])

    self._apply_translation_suffix_to_campaigns_and_ad_groups(
        campaigns=google_ads_objects.campaigns,
        ad_groups=google_ads_objects.ad_groups,
        target_language_code=settings.target_language_codes[0],
    )

    logging.info('Finished execution: %s', self.name)

    return worker_result.WorkerResult(
        status=worker_result.Status.SUCCESS,
        warning_msg=self._warning_msg,
        error_msg=self._error_msg,
        keywords_modified=google_ads_objects.keywords.size(),
    )

  def _translate_keywords(
      self,
      keywords: keywords_lib.Keywords,
      source_language_code: str,
      target_language_code: str) -> None:
    """Translates the keywords data model.

    Args:
      keywords: The keywords data object to translate.
      source_language_code: The language code to translate from.
      target_language_code: The language code to translate to.
    """
    logging.info('Starting keyword translation...')

    keywords_translation_frame = keywords.get_translation_frame()

    try:
      self._cloud_translation_client.translate(
          translation_frame=keywords_translation_frame,
          source_language_code=source_language_code,
          target_language_code=target_language_code,
      )
    except requests.exceptions.HTTPError as http_error:
      # Catch the exception so we can write the data we did manage to
      # translate.
      logging.exception(
          'Encountered error during calls to Translation API: %s', http_error)
      self._warning_msg += (
          'Encountered an error during keyword translation. Check the output '
          'files before uploading. A developer can check logs for more details.'
          )

    keywords.apply_translations(
        target_language=target_language_code,
        translation_frame=keywords_translation_frame,
        update_ad_group_and_campaign_names=True,
    )

    logging.info('Finished keyword translation.')

  def _translate_ads(
      self,
      ads: ads_lib.Ads,
      source_language_code: str,
      target_language_code: str) -> None:
    """Translates the ads data model.

    Args:
      ads: The ads data object to translate.
      source_language_code: The language code to translate from.
      target_language_code: The language code to translate to.
    """
    logging.info('Starting ad translation...')

    ads_translation_frame = ads.get_translation_frame()

    try:
      self._cloud_translation_client.translate(
          translation_frame=ads_translation_frame,
          source_language_code=source_language_code,
          target_language_code=target_language_code,
      )
    except requests.exceptions.HTTPError as http_error:
      # Catch the exception so we can write the data we did manage to
      # translate.
      logging.exception(
          'Encountered error during calls to Translation API: %s', http_error)
      self._warning_msg += (
          'Encountered an error during ad translation. Check the output files '
          ' before uploading. A developer can check logs for more details.')

    ads.apply_translations(
        target_language=target_language_code,
        translation_frame=ads_translation_frame,
        update_ad_group_and_campaign_names=True,
    )

    logging.info('Finished ad translation.')

  def _apply_translation_suffix_to_campaigns_and_ad_groups(
      self,
      campaigns: campaigns_lib.Campaigns,
      ad_groups: ad_groups_lib.AdGroups,
      target_language_code: str,
  ) -> None:
    """Adds traget language code suffix to campaign and ad group names."""
    campaigns.add_suffix(f'({target_language_code})')
    ad_groups.add_suffix(f'({target_language_code})')
