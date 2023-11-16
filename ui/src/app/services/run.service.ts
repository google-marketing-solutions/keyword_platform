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
import {Inject, Injectable} from '@angular/core';
import {Observable, throwError} from 'rxjs';
import {catchError, map} from 'rxjs/operators';

import {Output} from '../models/interfaces';
import {LOCATION_TOKEN} from '../shared/tokens';

/**
 * Run service.
 *
 * TODO(): Consider creating abstract/base class for this service
 * as there are other services that follow the same pattern/logic.
 */
@Injectable({providedIn: 'root'})
export class RunService {
  constructor(
      private readonly http: HttpClient,
      @Inject(LOCATION_TOKEN) private readonly location: Location) {}

  run(accountIds: string[], campaignIds: string[], sourceLanguageCode: string,
      targetLanguageCode: string, shortenTranslationsToCharLimit: boolean,
      translateKeywords: boolean, translateAds: boolean,
      translateExtensions: boolean, glossaryId: string, workers: string,
      client_id: string): Observable<HttpResponse<Output>> {
    return this
        .getRequestMethod('run', {
          'customer_ids': accountIds.join(','),
          'campaigns': campaignIds.join(','),
          'source_language_code': sourceLanguageCode,
          'target_language_codes': targetLanguageCode,
          'shorten_translations_to_char_limit':
              shortenTranslationsToCharLimit.toString(),
          'translate_keywords': translateKeywords.toString(),
          'translate_ads': translateAds.toString(),
          'translate_extensions': translateExtensions.toString(),
          'glossary_id': glossaryId,
          'workers_to_run': workers,
          'client_id': client_id,
          'endpoint': 'run'
        })
        .pipe(catchError(this.handleError), map(response => response));
  }

  private getPathname(api: string): string {
    return (
        this.location.hostname === 'localhost' ? './test-api/' + api + '.json' :
                                                 './proxy');
  }

  /**
   * Returns observable http response depending on whether http request is being
   * made locally or live/prod. Useful when viewing or testing locally as post
   * requests natively respond with 404 errors on localhost.
   * @param api Name of the api.
   * @param values Values of the parameters provided.
   * @returns An observable http response.
   */
  private getRequestMethod(api: string, values: {[key: string]: string}):
      Observable<HttpResponse<Output>> {
    const pathname = this.getPathname(api);
    const headers = new HttpHeaders({'Content-Type': 'application/json'});
    const params = new HttpParams({fromObject: values});
    let request: Observable<HttpResponse<Output>>;
    if (this.location.hostname === 'localhost') {
      request = this.http.get<Output>(
          pathname,
          {headers, observe: 'response', params, responseType: 'json'});
    } else {
      request = this.http.post<Output>(
          pathname, values,
          {headers, observe: 'response', responseType: 'json'});
    }
    return request;
  }

  private handleError(error: HttpErrorResponse):
      Observable<HttpResponse<Output>> {
    return throwError(error.message);
  }
}
