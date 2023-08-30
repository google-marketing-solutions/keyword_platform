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

import {HttpClient, HttpErrorResponse, HttpHeaders, HttpParams, HttpResponse} from '@angular/common/http';
import {Injectable} from '@angular/core';
import {Observable, throwError} from 'rxjs';
import {catchError, map} from 'rxjs/operators';

import {Output} from '../models/interfaces';

/** Run service. */
@Injectable({providedIn: 'root'})
export class RunService {
  constructor(private readonly http: HttpClient) {}

  run(accountIds: string[], campaignIds: string[], sourceLanguageCode: string,
      targetLanguageCode: string, multipleTemplates: boolean,
      workers: string[]): Observable<HttpResponse<Output>> {
    const params = new HttpParams({
      fromObject: {
        'customer_ids': accountIds.join(','),
        'campaigns': campaignIds.join(','),
        'source_language_code': sourceLanguageCode,
        'target_language_codes': targetLanguageCode,
        'workers_to_run': workers.join(','),
        'multiple_templates': multipleTemplates.toString(),
        'endpoint': 'run'
      }
    });
    return this.http
        .get<Output>(
            (window.location.hostname === 'localhost' ? './test-api/run.json' :
                                                        './proxy'),
            {
              headers: new HttpHeaders({'Content-Type': 'application/json'}),
              observe: 'response',
              params,
              responseType: 'json',
            },
            )
        .pipe(catchError(this.handleError), map(response => response));
  }

  private handleError(error: HttpErrorResponse) {
    return throwError(error.message);
  }
}
