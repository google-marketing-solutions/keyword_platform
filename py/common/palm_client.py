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

"""Defines the PalmClient class.

See class doctring for more details.
"""
import ast
from absl import logging
import google.generativeai as genai

_MODEL = 'models/text-bison-001'

AVAILABLE_LANGUAGES = frozenset(['en'])


class PalmClient:
  """A client to make requests to the Palm API.

  This requires an api_key from the Cloud Platform Console.

  Example usage:
    palm_client = PalmClient(api_key)
    shortened_text = palm_client.shorten_text_to_char_limit(
      'Some long headline...', 'en', 50)
  """

  def __init__(self, api_key: str):
    self._client = genai.configure(api_key=api_key)

  def shorten_text_to_char_limit(
      self, text_list: list[str], language_code: str, char_limit: int
  ) -> list[str]:
    """Shortens a list of strings under the provided character limit.

    If a text list element is equal or under the character limit already, the
    original list element will be returned.

    Args:
      text_list: A list of strings to shorten.
      language_code: The language of the text.
      char_limit: The character limit to shorten the text to.

    Returns:
      The a list of strings that are under the passed character limit. If the
      passed language code isn't supported the original text list is returned.
    """
    if language_code not in AVAILABLE_LANGUAGES:
      logging.warning(
          'Language %s not supported. Returning original text list.',
          language_code,
      )
      return text_list
    else:
      shorten_prompt = f"""
        For each of the following list elements, shorten the sentences to be
        under {char_limit} characters only if it is above {char_limit}
        characters, retain the given sentence otherwise:

          {text_list}

        Return just a python list.
      """
      # TODO(): Batch requests to PaLM API.
      response = genai.generate_text(
          model=_MODEL,
          prompt=shorten_prompt,
          candidate_count=1,
          temperature=0,
      )
      return ast.literal_eval(response.result) if response.result else text_list
