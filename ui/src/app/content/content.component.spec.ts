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

import {HttpClientModule} from '@angular/common/http';
import {ComponentFixture, TestBed} from '@angular/core/testing';
import {FormsModule, ReactiveFormsModule} from '@angular/forms';
import {MatAutocompleteModule} from '@angular/material/autocomplete';
import {MatCheckboxModule} from '@angular/material/checkbox';
import {MatDialogModule} from '@angular/material/dialog';
import {MatIconModule} from '@angular/material/icon';
import {MatInputModule} from '@angular/material/input';
import {MatProgressSpinnerModule} from '@angular/material/progress-spinner';
import {MatSlideToggleModule} from '@angular/material/slide-toggle';
import {MatTabsModule} from '@angular/material/tabs';
import {BrowserAnimationsModule} from '@angular/platform-browser/animations';

import {AccountsComponent} from '../accounts/accounts.component';
import {CampaignsComponent} from '../campaigns/campaigns.component';
import {MultiSelectComponent} from '../multi-select/multi-select.component';
import {SingleSelectComponent} from '../single-select/single-select.component';
import {TranslationComponent} from '../translation/translation.component';

import {ContentComponent} from './content.component';

describe('ContentComponent', () => {
  let component: ContentComponent;
  let fixture: ComponentFixture<ContentComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [
        AccountsComponent, CampaignsComponent, ContentComponent,
        MultiSelectComponent, SingleSelectComponent, TranslationComponent
      ],
      imports: [
        BrowserAnimationsModule, FormsModule, HttpClientModule,
        MatAutocompleteModule, MatCheckboxModule, MatDialogModule,
        MatIconModule, MatInputModule, MatProgressSpinnerModule,
        MatSlideToggleModule, MatTabsModule, ReactiveFormsModule
      ]
    });
    fixture = TestBed.createComponent(ContentComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  // TODO(): Add effective unit tests.
  it('should be created', () => {
    expect(component).toBeTruthy();
  });
});
