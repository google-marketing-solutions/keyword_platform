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

import {AfterViewInit, ChangeDetectorRef, Component, EventEmitter, Output, ViewChild} from '@angular/core';
import {AbstractControl, FormGroup} from '@angular/forms';

import {Selection} from '../models/interfaces';
import {SelectionGroup} from '../models/types';
import {MultiSelectComponent} from '../multi-select/multi-select.component';
import {GoogleAdsService} from '../services/google-ads.service';

const CAMPAIGN_CONTROL_NAME = 'campaigns';

/**
 * A campaigns component.
 *
 * TODO(): Consider creating abstract/base class for this component
 * as there are other components that follow the same pattern/logic.
 */
@Component({
  selector: 'app-campaigns',
  templateUrl: './campaigns.component.html',
  styleUrls: ['./campaigns.component.scss']
})
export class CampaignsComponent implements AfterViewInit {
  @Output() readonly campaignSelectionEvent = new EventEmitter<string[]>();
  @Output()
  readonly campaignsValidationErrorEvent = new EventEmitter<boolean>();

  form = new FormGroup({});

  campaigns!: Selection[];

  showSpinner = false;

  private campaignIds: string[] = [];

  @ViewChild(MultiSelectComponent)
  private readonly control!: MultiSelectComponent;

  constructor(
      private readonly changeRefDetector: ChangeDetectorRef,
      private readonly googleAdsService: GoogleAdsService) {}

  ngAfterViewInit() {
    this.form.addControl(CAMPAIGN_CONTROL_NAME, this.control.control);
    this.getFormControl().valueChanges.subscribe(() => {
      this.campaignsValidationErrorEvent.emit(this.hasFormError());
    });
    this.changeRefDetector.detectChanges();
  }

  campaignSelection(value: SelectionGroup) {
    const campaign = value as Selection[];
    const length = campaign.length;
    this.campaignIds = [];
    if (length === 0) {
      return;
    }
    for (let i = 0; i < length; i++) {
      this.campaignIds.push(campaign[i]['id']);
    }
    this.campaignSelectionEvent.emit(this.campaignIds);
  }

  disableForm(disable: boolean) {
    (disable) ? this.form.disable() : this.form.enable();
  }

  getCampaigns(accountIds: string[]) {
    this.disableForm(true);
    this.showSpinner = true;
    console.log('Campaigns requested.');
    this.googleAdsService.getCampaigns(accountIds)
        .subscribe(
            (response => {
              this.showSpinner = false;
              this.campaigns = response.body!;
              this.disableForm(false);
              console.log('Campaigns request successful.');
            }),
            (error => {
              this.showSpinner = false;
              console.error(error);
            }));
  }

  resetCampaigns() {
    this.form.reset();
  }

  private getFormControl(): AbstractControl {
    const form = this.form as FormGroup;
    return form.controls[CAMPAIGN_CONTROL_NAME];
  }

  private hasFormError(): boolean {
    const control = this.getFormControl();
    const result = [];
    if (control.errors) {
      result.push(control.errors);
    }
    return result.length > 0;
  }
}
