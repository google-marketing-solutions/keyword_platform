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

"""Defines the Settings class."""

import dataclasses


@dataclasses.dataclass
class Settings:
  """A class for keeping track of the application settings."""

  source_language_code: str = ''
  target_language_codes: list[str] = dataclasses.field(default_factory=list)
  customer_ids: list[str] = dataclasses.field(default_factory=list)
  campaigns: list[str] = dataclasses.field(default_factory=list)
  credentials: dict[str, str] = dataclasses.field(
      default_factory=dict
  )
  workers_to_run: list[str] = dataclasses.field(default_factory=list)
  multiple_templates: bool = False
  client_id: str = ''
  translate_ads: bool = True
