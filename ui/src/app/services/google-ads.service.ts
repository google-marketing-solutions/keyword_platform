/**
 * @license
 * Copyright 2024 Google LLC.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     https://www.apache.org/licenses/LICENSE-2.0
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

import {Selection} from '../models/interfaces';
import {LOCATION_TOKEN} from '../shared/tokens';

/**
 * Google Ads service.
 *
 * TODO(): Consider creating abstract/base class for this service
 * as there are other services that follow the same pattern/logic.
 */
@Injectable({providedIn: 'root'})
export class GoogleAdsService {
  constructor(
      private readonly http: HttpClient,
      @Inject(LOCATION_TOKEN) private readonly location: Location) {}

  getAccounts(): Observable<HttpResponse<Selection[]>> {
    const params =
        new HttpParams({fromObject: {'endpoint': 'accessible_accounts'}});
    return this.http
        .get<Selection[]>(
            this.getPathname('accessible_accounts'),
            {
              headers: this.getHeaders(),
              observe: 'response',
              params,
              responseType: 'json'
            },
            )
        .pipe(catchError(this.handleError), map(response => response));
  }

  getCampaigns(accountIds: string[]): Observable<HttpResponse<Selection[]>> {
    return this
        .getRequestMethod('campaigns', {
          'selected_accounts': accountIds.join(','),
          'endpoint': 'campaigns'
        })
        .pipe(map(response => response), catchError(this.handleError));
  }

  private getPathname(api: string): string {
    return (
        this.location.hostname === 'localhost' ? './test-api/' + api + '.json' :
                                                 './proxy');
  }

  private getHeaders(): HttpHeaders {
    return new HttpHeaders({'Content-Type': 'application/json'});
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
      Observable<HttpResponse<Selection[]>> {
    const pathname = this.getPathname(api);
    const headers = this.getHeaders();
    const params = new HttpParams({fromObject: values});
    let request: Observable<HttpResponse<Selection[]>>;
    if (this.location.hostname === 'localhost') {
      request = this.http.get<Selection[]>(
          pathname,
          {headers, observe: 'response', params, responseType: 'json'});
    } else {
      request = this.http.post<Selection[]>(
          pathname, values,
          {headers, observe: 'response', responseType: 'json'});
    }
    return request;
  }

  private handleError(error: HttpErrorResponse):
      Observable<HttpResponse<Selection[]>> {
    return throwError(error.message);
  }
}
