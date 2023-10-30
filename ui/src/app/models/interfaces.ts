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
 * @fileoverview Interfaces for data input/output and API requests/responses.
 */

/**
 * Selection interface for API requests/responses.
 *
 * TODO(): Declare properties that represent API responses once
 * they're updated to share the same shape so that this interface can be
 * stronger typed.
 */
export interface Selection {
  [key: string]: string;
}

/**
 * Translation interface for API requests.
 */
export interface Translation {
  sourceLanguageCode: string;
  targetLanguageCode: string;
  glossaryId: string;
  translateKeywords: boolean;
  translateAds: boolean;
  shortenTranslationsToCharLimit: boolean;
}

/**
 * Output interface for API response. Output of successful form submission.
 */
export interface Output {
  [key: string]: {[key: string]: string[]}|
      {[key: string]: {[key: string]: number | string}};
}
