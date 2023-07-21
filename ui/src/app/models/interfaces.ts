/**
 * @license
 * Copyright 2023 Google LLC.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

/**
 * @fileoverview Interfaces for data input/output and API request/response.
 */

/**
 * Google Ads interface for API request/response.
 */
export interface GoogleAds {
  id: string;
  name: string;
}

/**
 * Language interface for API request/response.
 */
export interface Language {
  code: string;
  name: string;
}

/**
 * Output interface for API response. Output of successful form submission.
 */
export interface Output {
  [key: string]: {[key: string]: string[]}|
      {[key: string]: {[key: string]: string}};
}
