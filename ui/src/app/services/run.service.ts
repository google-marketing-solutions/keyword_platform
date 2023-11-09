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

import {HttpClient, HttpErrorResponse, HttpHeaders, HttpResponse} from '@angular/common/http';
import {Injectable} from '@angular/core';
import {Observable, throwError} from 'rxjs';
import {catchError, map} from 'rxjs/operators';

import {Output} from '../models/interfaces';

/** Run service. */
@Injectable({providedIn: 'root'})
export class RunService {
  constructor(private readonly http: HttpClient) {}

  run(accountIds: string[], campaignIds: string[], sourceLanguageCode: string,
      targetLanguageCode: string, shortenTranslationsToCharLimit: boolean,
      workers: string[], client_id: string, translateKeywords: boolean,
      translateAds: boolean, translateExtensions: boolean, glossaryId: string
  ): Observable<HttpResponse<Output>> {
    return this.http
        .post<Output>(
            './proxy', {
              'customer_ids': accountIds.join(','),
              'campaigns': campaignIds.join(','),
              'source_language_code': sourceLanguageCode,
              'target_language_codes': targetLanguageCode,
              'shorten_translations_to_char_limit':
                  shortenTranslationsToCharLimit,
              'workers_to_run': workers.join(','),
              'client_id': client_id,
              'translate_keywords': translateKeywords.toString(),
              'translate_ads': translateAds.toString(),
              'translate_extensions': translateExtensions.toString(),
              'glossary_id': glossaryId,
              'endpoint': 'run'
            },
            {
              headers: new HttpHeaders({'Content-Type': 'application/json'}),
              observe: 'response',
              responseType: 'json'
            })
        .pipe(catchError(this.handleError), map(response => response));
  }

  private handleError(error: HttpErrorResponse) {
    return throwError(error.message);
  }
}
