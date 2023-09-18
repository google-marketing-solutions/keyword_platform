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

"""Classes to represent the result of a Google Ads worker."""
import dataclasses
import enum


class Status(str, enum.Enum):
  """The status of a Google Ads worker."""
  SUCCESS = 'SUCCESS'
  FAILURE = 'FAILURE'


@dataclasses.dataclass
class WorkerResult:
  """The result of a Google Ads worker."""

  status: Status
  keywords_modified: int = 0
  keywords_added: int = 0
  ads_modified: int = 0
  ads_added: int = 0
  warning_msg: str|None = ''
  error_msg: str|None = ''
  translation_chars_sent: int = 0
  genai_chars_sent: int = 0
  duration_ms: int = 0
