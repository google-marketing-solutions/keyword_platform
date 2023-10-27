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

import {Component, ViewChild} from '@angular/core';
import {MatButton} from '@angular/material/button';
import {MatDialog} from '@angular/material/dialog';
import {MatTabGroup} from '@angular/material/tabs';

import {AccountsComponent} from '../accounts/accounts.component';
import {CampaignsComponent} from '../campaigns/campaigns.component';
import {DialogComponent} from '../dialog/dialog.component';
import {RequestStatus, Worker} from '../models/enums';
import {Output} from '../models/interfaces';
import {RunService} from '../services/run.service';
import {TranslationComponent} from '../translation/translation.component';

/**
 * Interface for the clientId window property that is set by the Google Tag
 * Manager (GTM) script. The data type for the clientId property is a string
 * as its value is defined by the Google Analytics client_id field.
 *
 * See
 * https://developers.google.com/analytics/devguides/collection/ga4/reference/config#client_id
 */
declare interface ClientIdProperty {
  clientId: string;
}

enum TabIndex {
  TRANSLATE = 1
}

/**
 * A content component.
 */
@Component({
  selector: 'app-content',
  templateUrl: './content.component.html',
  styleUrls: ['./content.component.scss']
})
export class ContentComponent {
  accountIds?: string[];
  campaignIds?: string[];

  requestStatus = RequestStatus.NONE;

  accountsHasValidationError = true;
  campaignsHasValidationError = true;
  translationHasValidationError = true;

  @ViewChild(AccountsComponent)
  private readonly accountsComponent!: AccountsComponent;
  @ViewChild(CampaignsComponent)
  private readonly campaignsComponent!: CampaignsComponent;
  @ViewChild(TranslationComponent)
  private readonly translationComponent!: TranslationComponent;

  @ViewChild(MatTabGroup) private readonly tabGroup!: MatTabGroup;
  @ViewChild(MatButton) private readonly button!: MatButton;

  constructor(
      private readonly dialog: MatDialog,
      private readonly runService: RunService) {}

  accountSelection(value: string[]) {
    // Reset campaign selections anytime accounts get selected in order to
    // force validation handling otherwise campaign values from the previous UI
    // interaction gets used even though they aren't visible in the campaign's
    // selection field.
    this.campaignsComponent.resetCampaigns();

    this.accountIds = value;
    this.campaignsComponent.getCampaigns(this.accountIds);
  }

  accountsValidationError(value: boolean) {
    this.accountsHasValidationError = value;
  }

  campaignSelection(value: string[]) {
    this.campaignIds = value;
  }

  campaignsValidationError(value: boolean) {
    this.campaignsHasValidationError = value;
  }

  translationValidationError(value: boolean) {
    this.translationHasValidationError = value;
  }

  hasFormError(): boolean {
    const error = this.translationHasValidationError ||
        this.accountsHasValidationError || this.campaignsHasValidationError;
    return error;
  }

  isRunRequestedStatus(): boolean {
    return this.requestStatus === RequestStatus.REQUESTED;
  }

  run() {
    this.requestStatus = RequestStatus.REQUESTED;

    // The clientId property is defined as a window object by the Google Tag
    // Manager script so attemping to access it directly will fail because it's
    // not recognized as part of the native window object. E.g. window.clientId
    // returns undefined. So the native window object is set as a window object
    // that contains the clientId property in order to gets its value.
    const windowObject = window as unknown as ClientIdProperty;
    const clientId = windowObject.clientId;

    const workers = [];

    if (this.tabGroup.selectedIndex === TabIndex.TRANSLATE) {
      workers.push(Worker.TRANSLATION_WORKER);
    }

    this.disableForm(true);

    const translationData = this.translationComponent.getTranslationData();

    this.runService
        .run(
            this.accountIds!, this.campaignIds!,
            translationData.sourceLanguageCode,
            translationData.targetLanguageCode,
            translationData.shortenTranslationsToCharLimit, workers, clientId,
            translationData.translateKeywords, translationData.translateAds,
            translationData.glossaryId)
        .subscribe(
            (response => {
              this.requestStatus = RequestStatus.RESPONDED;
              this.disableForm(false);
              this.openDialog(response.statusText!, response.body!);
              console.log('Run service request for translation successful.');
            }),
            (error => {
              this.requestStatus = RequestStatus.ERROR;
              this.disableForm(false);
              this.openDialog(error, null);
              console.error(error);
            }));
  }

  private disableForm(disable: boolean) {
    // TODO(): Enabling/disabling each control individually seems
    // like the only way to manipulate the state of the entire form. Still
    // haven't found how to disable all content through a single call.
    // E.g. this.tab[1].setDisable().
    this.accountsComponent.disableForm(disable);
    this.campaignsComponent.disableForm(disable);
    this.translationComponent.disableForm(disable);
    this.button.disabled = disable;
  }

  private openDialog(statusText: string, value: Output|null) {
    this.dialog.open(DialogComponent, {data: {statusText, value}});
  }
}
