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

import { ComponentFixture, TestBed } from '@angular/core/testing';
import {MAT_DIALOG_DATA} from '@angular/material/dialog';
import {MatIconModule} from '@angular/material/icon';

import {Output} from '../models/interfaces';

import { DialogComponent } from './dialog.component';

interface DialogData {
  [key: string]: Output;
}

describe('DialogComponent', () => {
  let component: DialogComponent;
  let fixture: ComponentFixture<DialogComponent>;

  function getDialogData() {
    const data: DialogData = {
      'value': {
        'asset_urls': [
          'http://storage.googleapis.com/bucket/file1',
          'http://storage.googleapis.com/bucket/file2',
          'http://storage.googleapis.com/bucket/file3'
        ],
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
            'status': 'SUCCESS',
            'warning_msg': ''
          }
        }
      }
    }
    return data;
  }

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [DialogComponent],
      imports: [MatIconModule],
      providers: [
        {provide: MAT_DIALOG_DATA, useFactory: getDialogData},
      ],
    });
    fixture = TestBed.createComponent(DialogComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  // TODO(): Add effective unit tests.
  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
