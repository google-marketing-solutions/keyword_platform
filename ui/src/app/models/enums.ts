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
 * @fileoverview Enums for expected values.
 */

/** List of workers to run. */
export enum Worker {
  TRANSLATION_WORKER = 'translationWorker'
}

/** Status of server requests. */
export enum RequestStatus {
  NONE = 'None',
  REQUESTED = 'Requested',
  RESPONDED = 'Responded',
  ERROR = 'Error'
}

/** Status of server responses. */
export enum ResponseStatus {
  SUCCESS = 200,
  SERVER_ERROR = 500
}

/** Messages for server responses. */
export enum ResponseMessage {
  SUCCESS = 'Success.',
  SERVER_ERROR =
      'Failed to process request. A developer can check the logs for details.',
  UNKNOWN_ERROR = 'Unknown error. A developer can check the logs for details.'
}
