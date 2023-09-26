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

import {HttpClientModule, HttpErrorResponse, HttpResponse} from '@angular/common/http';
import {HttpClientTestingModule, HttpTestingController} from '@angular/common/http/testing';
import {TestBed} from '@angular/core/testing';
import {of, throwError} from 'rxjs';

import {LOCATION_TOKEN} from '../shared/tokens';

import {RunService} from './run.service';

describe('RunService', () => {
  const ENDPOINT =
      './proxy?customer_ids=1&campaigns=1&source_language_code=en' +
      '&target_language_codes=de&workers_to_run=translationWorker' +
      '&multiple_templates=false&client_id=aaa.bbb&endpoint=run';

  let service: RunService;
  let httpMock: HttpTestingController;
  let spy: jasmine.Spy;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientModule, HttpClientTestingModule],
      providers: [{
        provide: LOCATION_TOKEN,
        useValue: {hostname: 'hostname.0.0.0.0.nip.io'}
      }],

    });

    service = TestBed.inject(RunService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should use http GET method', () => {
    service
        .run(['1'], ['1'], 'en', 'de', false, ['translationWorker'], 'aaa.bbb')
        .subscribe();
    const request = httpMock.expectOne(ENDPOINT);
    expect(request.request.method).toBe('GET');
    httpMock.verify();
  });

  it('should respond successfully', () => {
    const body = {
      'asset_urls': {
        'csv': ['http://storage.googleapis.com/bucket/file1.csv'],
        'xlsx': ['http://storage.googleapis.com/bucket/file1.xlsx']
      },
      'worker_results': {
        'miningWorker': {
          'error_msg': '',
          'keywords_added': 10,
          'keywords_modified': 0,
          'status': 'SUCCESS',
          'warning_msg': 'Added weird words'
        },
        'translationWorker': {
          'error_msg': '',
          'keywords_added': 0,
          'keywords_modified': 10,
          'ads_added': 0,
          'ads_modified': 0,
          'translation_chars_sent': 0,
          'genai_chars_sent': 0,
          'status': 'SUCCESS',
          'warning_msg': '',
          'duration_ms': 0
        }
      }
    };
    const httpResponse =
        new HttpResponse({body, status: 200, statusText: 'OK'});
    spy = spyOn(TestBed.inject(RunService), 'run');
    spy.and.returnValue(of(httpResponse));
    service
        .run(['1'], ['1'], 'en', 'de', false, ['translationWorker'], 'aaa.bbb')
        .subscribe(response => {
          expect(response.status).toBe(200);
          expect(response.statusText).toBe('OK');
          expect(response.body).toBe(body);
        });
  });

  it('should throw internal server error', () => {
    const statusText = 'The server encountered and error and could not ' +
        'complete your request. Developers can check the logs for details.'
    const httpError = new HttpErrorResponse({
      error: 'Internal Service Error',
      status: 500,
      url: ENDPOINT,
      statusText
    });
    spy = spyOn(TestBed.inject(RunService), 'run');
    spy.and.returnValue(throwError(httpError));
    service
        .run(['1'], ['1'], 'en', 'de', false, ['translationWorker'], 'aaa.bbb')
        .subscribe(() => {}, error => {
          expect(error.message)
              .toBe(`Http failure response for ${ENDPOINT}: 500 ${statusText}`);
        });
  });
});
