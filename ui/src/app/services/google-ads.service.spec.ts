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

import {HttpClientModule, HttpResponse} from '@angular/common/http';
import {HttpClientTestingModule, HttpTestingController} from '@angular/common/http/testing';
import {TestBed} from '@angular/core/testing';
import {of} from 'rxjs';

import {LOCATION_TOKEN} from '../shared/tokens';

import {GoogleAdsService} from './google-ads.service';

describe('GoogleAdsService', () => {
  let service: GoogleAdsService;
  let httpMock: HttpTestingController;
  let getAccountsSpy: jasmine.Spy;
  let getCampaignsSpy: jasmine.Spy;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientModule, HttpClientTestingModule],
      providers: [{
        provide: LOCATION_TOKEN,
        useValue: {hostname: 'hostname.0.0.0.0.nip.io'}
      }]
    });
    service = TestBed.inject(GoogleAdsService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should use http GET method with getAccounts', () => {
    service.getAccounts().subscribe();
    const request = httpMock.expectOne('./proxy?endpoint=accessible_accounts');
    expect(request.request.method).toBe('GET');
    httpMock.verify();
  });

  it('should respond successfully using getAccounts', () => {
    const body =
        [{'id': '1', 'name': 'Account 1', 'display_name': '[1] Account 1'}];
    const httpResponse =
        new HttpResponse({body, status: 200, statusText: 'OK'});
    getAccountsSpy = spyOn(TestBed.inject(GoogleAdsService), 'getAccounts');
    getAccountsSpy.and.returnValue(of(httpResponse));
    service.getAccounts().subscribe(response => {
      expect(response.status).toBe(200);
      expect(response.statusText).toBe('OK');
      expect(response.body).toBe(body);
    });
  });

  it('should use http POST method with getCampaigns', () => {
    service.getCampaigns(['1']).subscribe();
    const request = httpMock.expectOne('./proxy');
    expect(request.request.method).toBe('POST');
    httpMock.verify();
  });

  it('should respond successfully using getCampaigns', () => {
    const body =
        [{'id': '1', 'name': 'Campaign 1', 'display_name': '[1] Campaign 1'}];
    const httpResponse =
        new HttpResponse({body, status: 200, statusText: 'OK'});
    getCampaignsSpy = spyOn(TestBed.inject(GoogleAdsService), 'getCampaigns');
    getCampaignsSpy.and.returnValue(of(httpResponse));
    service.getCampaigns(['1']).subscribe(response => {
      expect(response.status).toBe(200);
      expect(response.statusText).toBe('OK');
      expect(response.body).toBe(body);
    });
  });
});
