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

"""Utility functions."""
import functools
import time
from typing import Any

from absl import logging


class MaxRetriesExceededError(Exception):
  """Custom exception when the maximum number of retries has been exceeded."""


def exponential_backoff_retry(
    base_delay: int,
    back_off_factor: int = 1,
    max_retries: int = 10,
    exceptions: list[type[Exception]] = [Exception],
) -> Any:
  """A decorator that retries the function with exponential backoff.

  Args:
    base_delay: The base delay in seconds.
    back_off_factor: The factor to increase the delay by.
    max_retries: The number of maximum retries before raising an error.
    exceptions: A list of exceptions for which to retry.

  Returns:
    The decorated function.

  Raises:
    Exception: Any exception encountered not in the list of exceptions.
    MaxRetriesExceededError: When the maximum number of retries has been
    exceeded.
  """
  def decorator(func) -> Any:
    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> Any:
      retries = 0
      while retries < max_retries:
        try:
          return func(*args, **kwargs)
        except Exception as err:
          retries += 1
          if not isinstance(err, tuple(exceptions)):
            logging.exception(
                '%s not within exception to retry.', type(err).__name__
            )
            raise err
          if retries == max_retries:
            logging.exception('Max retries of %d reached: %s', retries, err)
            raise MaxRetriesExceededError(
                f'Max retries of {retries} reached.'
            ) from err
          delay = int(base_delay * back_off_factor**retries)
          logging.exception(
              'Exception when attempting to run %s: %s. Retrying in %ds.',
              func,
              err,
              delay,
          )
          time.sleep(delay)

    return wrapper

  return decorator
