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

import {HttpClientModule, HttpResponse} from '@angular/common/http';
import {HttpClientTestingModule, HttpTestingController} from '@angular/common/http/testing';
import {TestBed} from '@angular/core/testing';
import {of} from 'rxjs';
import {LOCATION_TOKEN} from '../shared/tokens';

import {TranslationService} from './translation.service';

describe('TranslationService', () => {
  let service: TranslationService;
  let httpMock: HttpTestingController;
  let getGlossariesSpy: jasmine.Spy;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientModule, HttpClientTestingModule],
      providers: [{
        provide: LOCATION_TOKEN,
        useValue: {hostname: 'hostname.0.0.0.0.nip.io'}
      }],

    });
    service = TestBed.inject(TranslationService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should use http GET method with getGlossaries', () => {
    service.getGlossaries().subscribe();
    const request = httpMock.expectOne('./proxy?endpoint=list_glossaries');
    expect(request.request.method).toBe('GET');
    httpMock.verify();
  });

  it('should respond successfully using getGlossaries', () => {
    const body = [
      {
        'id': 'glossary_1',
        'name': 'projects/some-project/locations/some-location/glossary_1',
        'display_name': 'glossary_1'
      },
      {
        'id': 'glossary_2',
        'name': 'projects/some-project/locations/some-location/glossary_2',
        'display_name': 'glossary_2'
      },
      {
        'id': 'glossary_3',
        'name': 'projects/some-project/locations/some-location/glossary_3',
        'display_name': 'glossary_3'
      },
      {
        'id': 'glossary_4',
        'name': 'projects/some-project/locations/some-location/glossary_4',
        'display_name': 'glossary_4'
      }
    ];
    const httpResponse =
        new HttpResponse({body, status: 200, statusText: 'OK'});
    getGlossariesSpy = spyOn(TestBed.inject(TranslationService), 'getGlossaries');
    getGlossariesSpy.and.returnValue(of(httpResponse));
    service.getGlossaries().subscribe(response => {
      expect(response.status).toBe(200);
      expect(response.statusText).toBe('OK');
      expect(response.body).toBe(body);
    });
  });
});
