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

"""Defines the Accounts data model class."""

import dataclasses
from typing import Any
from absl import logging


@dataclasses.dataclass
class Account:
  """A class to represent a Google Ads account."""

  id: str = dataclasses.field(default_factory=str)
  name: str = dataclasses.field(default_factory=str)


class Accounts:
  """A class to represent data for a customer's Google Ads Accounts.

  Attributes:
    accounts_list: A list of account objects.
  """

  def __init__(self, response_jsons: list[Any]):
    """Initializes the Accounts object.

    Creates a list of accounts.

    See class docstring for more details.

    Args:
      response_jsons: A list of JSON responses from a Google Ads API
        searchStream request. The request should contain the following fields:
        customerClient.id, customerClient.descriptive_name,
    """
    self._accounts = []
    for response_json in response_jsons:
      for batch in response_json:
        for result in batch['results']:
          self._accounts.append(
              Account(
                  id=result['customerClient']['id'],
                  name=result['customerClient']['descriptiveName'],
              )
          )
    logging.info(
        'Initialized Accounts list with length %d.', len(self._accounts)
    )

  @property
  def accounts_list(self) -> list[Account]:
    return self._accounts
