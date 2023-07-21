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

import { HttpClient, HttpErrorResponse, HttpHeaders, HttpParams, HttpResponse } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable, throwError } from 'rxjs';
import { catchError, map } from 'rxjs/operators';

import { GoogleAds } from '../models/interfaces';

/**
 * Google Ads service.
 *
 * TODO(): Modify HTTP requests to support Cloud Run environment.
 */
@Injectable({providedIn: 'root'})
export class GoogleAdsService {
  constructor(private readonly http: HttpClient) {}

  getAccounts(): Observable<HttpResponse<GoogleAds[]>> {
    return this.http
        .get<GoogleAds[]>(
            this.getHost('accessible_accounts'),
            {
              headers: this.getHeader(),
              observe: 'response',
              responseType: 'json'
            },
            )
        .pipe(catchError(this.handleError), map(response => response));
  }

  getCampaigns(accountIds: string[]): Observable<HttpResponse<GoogleAds[]>> {
    return this.http
        .get<GoogleAds[]>(this.getHost('campaigns'), {
          headers: this.getHeader(),
          observe: 'response',
          params:
              new HttpParams().set('selected_accounts', accountIds.join(',')),
          responseType: 'json'
        })
        .pipe(map(response => response), catchError(this.handleError));
  }

  private getHost(api: string) {
    return (
        window.location.hostname === 'localhost' ?
            './test-api/' + api + '.json' :
            './' + api);
  }

  private getHeader() {
    return new HttpHeaders({'Content-Type': 'application/json'});
  }

  private handleError(error: HttpErrorResponse) {
    return throwError(error.message);
  }
}
