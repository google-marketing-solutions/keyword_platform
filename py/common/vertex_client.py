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

"""Defines the VertexClient class.

See class doctring for more details.
"""
import ast
from concurrent import futures
import math
import os
from absl import logging
import vertexai
from vertexai.language_models import TextGenerationModel
import numpy as np

_MODEL = 'text-bison@001'

AVAILABLE_LANGUAGES = frozenset(['en', 'es', 'ko', 'hi', 'zh'])


def split_list(input_list: list[str], max_len: int = 10) -> list[list[str]]:
  """Splits a list into a list of shorter lists.

  Args:
    input_list: The list to split up.
    max_len: The max length of the splits.

  Returns:
    A list of lists.
  """
  num_batches = math.ceil(len(input_list) / max_len)
  result = []
  batches = np.array_split(input_list, num_batches)
  for batch in batches:
    result.append(batch.tolist())
  return result


class VertexClient:
  """A client to make requests to the Vertex API.

  This requires an api_key from the Cloud Platform Console.

  Example usage:
    vertex_client = VertexClient()
    shortened_text = vertex_client.shorten_text_to_char_limit(
      'Some long headline...', 'en', 50)
  """

  def __init__(self) -> None:
    vertexai.init(
        project=os.environ['GCP_PROJECT'], location=os.environ['GCP_REGION']
    )
    self._client = TextGenerationModel.from_pretrained(_MODEL)
    # Making a call in __init__ to ensure initialization of VertexClient fails
    # if the GCP_PROJECT was not allowlisted to use Vertex LLMs.
    self._client.predict('Are you there?')

  def shorten_text_to_char_limit(
      self, text_list: list[str], language_code: str, char_limit: int
  ) -> list[str]:
    """Shortens a list of strings under the provided character limit.

    To prevent sending too long of a string to the model, we split the list of
    strings to process into smaller chunks and process them in parallel.

    Args:
      text_list: A list of strings to shorten.
      language_code: The language of the text.
      char_limit: The character limit to shorten the text to.

    Returns:
      The a list of strings that are under the passed character limit. If the
      passed language code isn't supported the original text list is returned.
    """
    batches = split_list(text_list)
    result = []
    with futures.ThreadPoolExecutor() as executor:
      shortened_batches = executor.map(
          lambda text_list: self._shorten_text_to_char_limit(
              text_list, language_code, char_limit
          ),
          batches,
      )

    for shortened_batch in shortened_batches:
      logging.info('shortened_batch: %s', shortened_batch)

      if isinstance(shortened_batch, list):
        result.extend(shortened_batch)
    return result

  def _shorten_text_to_char_limit(
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
      # Sets temperature to be deterministic and select the most probable
      # output via top_p and top_k. More details here:
      # https://cloud.google.com/vertex-ai/docs/generative-ai/model-reference/text
      parameters = {'temperature': 0, 'top_p': 0.8, 'top_k': 1}
      shorten_prompt = f"""
        Make each of the following sentences shorter

        Sentences:
          {text_list}

        Do so until this Python function returns true:
          all(len(sentence) < {char_limit} for shortened_sentence in Sentences)

        Shortened sentences list:
      """
      response = self._client.predict(shorten_prompt, **parameters)
      return ast.literal_eval(response.text) if response.text else text_list
