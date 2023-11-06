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
 * @fileoverview Enums for workers, api/service request status, and others.
 */

/** Workers to run. */
export enum Worker {
  TRANSLATION_WORKER = 'translationWorker'
}

/** Form control names. */
export enum ControlName {
  ACCOUNTS = 'accounts',
  CAMPAIGNS = 'campaigns',
  SOURCE_LANGUAGE = 'source-language',
  TARGET_LANGUAGE = 'target-language',
  GLOSSARY = 'glossary'
}

/** Status of api/service requests. */
export enum RequestStatus {
  NONE = 'None',
  REQUESTED = 'Requested',
  RESPONDED = 'Responded',
  ERROR = 'Error'
}

/** Font icon names. */
export enum FontIcon {
  ERROR = 'error',
  PRIORITY = 'priority_high'
}
