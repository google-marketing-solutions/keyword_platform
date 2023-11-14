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

import {Component, QueryList, ViewChild, ViewChildren} from '@angular/core';
import {MatButton} from '@angular/material/button';
import {MatDialog} from '@angular/material/dialog';
import {MatSnackBar} from '@angular/material/snack-bar';
import {MatTab, MatTabGroup} from '@angular/material/tabs';

import {AccountsComponent} from '../accounts/accounts.component';
import {CampaignsComponent} from '../campaigns/campaigns.component';
import {DialogComponent} from '../dialog/dialog.component';
import {FontIcon, RequestStatus, Worker} from '../models/enums';
import {Output, Translation} from '../models/interfaces';
import {RunService} from '../services/run.service';
import {flattenAndFilter} from '../shared/utils';
import {SnackbarComponent} from '../snackbar/snackbar.component';
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

/**
 * Tab index values. New indices should be incrementality added when new tabs
 * are created.
 */
enum TabIndex {
  TRANSLATE = 1,
  // Example index of a new tab:
  // SOME_OTHER_TAB = 2
}

/**
 * A content component. Supports the addition of new tabs that represent new
 * features.
 */
@Component({
  selector: 'app-content',
  templateUrl: './content.component.html',
  styleUrls: ['./content.component.scss']
})
export class ContentComponent {
  /**
   * List of account IDs for translation.
   */
  translationAccountIds?: string[];

  /**
   * List of campaign IDs for translation.
   */
  translationCampaignIds?: string[];

  /**
   * Validation error status of translation accounts.
   */
  translationAccountsHasValidationError = true;

  /**
   * Validation error status of translation campaigns.
   */
  translationCampaignsHasValidationError = true;

  /**
   * Validation error status of translation settings.
   */
  translationHasValidationError = true;

  // A similar pattern can be followed for storing values provided by new
  // components:
  // someOtherAccountIds?: string[];
  // someOtherAccountsHasValidationError = true;
  // someOtherComponentHasValidationError = true;

  /**
   * Status of run request.
   */
  requestStatus = RequestStatus.NONE;

  // Depending on the use case, @ViewChild or @ViewChildren can be used to
  // declare a new component (that represents a new feature) to be instantiated:
  // @ViewChild(SomeOtherComponent)
  // private readonly someOtherComponent!: SomeOtherComponent;

  @ViewChild(TranslationComponent)
  private readonly translationComponent!: TranslationComponent;

  @ViewChild(MatTabGroup) private readonly tabGroup!: MatTabGroup;

  @ViewChildren(AccountsComponent)
  private readonly accountsComponents!: QueryList<AccountsComponent>;

  @ViewChildren(CampaignsComponent)
  private readonly campaignsComponents!: QueryList<CampaignsComponent>;

  @ViewChildren(MatButton) private readonly buttons!: QueryList<MatButton>;

  @ViewChildren(MatTab) private readonly tabs!: QueryList<MatTab>;

  // When adding a new tab make sure to create a boolean property whose value is
  // read by the *ngIf directive in the HTML template as it determines the
  // availability of content within the tab when selecting it:
  // someOtherTab = false;

  constructor(
      private readonly dialog: MatDialog,
      private readonly snackbar: MatSnackBar,
      private readonly runService: RunService) {}

  /**
   * The tabGroup selected callback function for changing tabs. Used to listen
   * for the selection of a new tab.
   * @param selectedIndex The index of the selected tab.
   */
  onSelectedTabChange(selectedIndex: number) {
    // New tabs can be activated by setting its corresponding condition to true.
    // For example, a boolean property of someOtherTab can be set to true:
    // if (selectedIndex === TabIndex.SOME_OTHER_TAB) {
    //   this.someOtherTab = true;
    // }
    // The HTML template would then respond to the value change and display
    // the tab:
    // <div class="tab" *ngIf="someOtherTab">
    // This condition prevents data in all tabs from being requested at the same
    // time on initial load. Note that the value should never be reset to false
    // otherwise initial data would be requested everytime the selection of the
    // tab changes.
  }

  /**
   * The AccountsComponent load callback function for account requests.
   * @param value Whether accounts were successfully loaded or not.
   */
  accountsLoad(value: boolean) {
    // Should a new tab be available then the same conditional pattern must be
    // implemented for its specific component whenever AccountsComponent gets
    // used across multiple tabs:
    // (this.getSelectedTabIndex() === TabIndex.SOME_OTHER_TAB)
    if (this.getSelectedTabIndex() === TabIndex.TRANSLATE) {
      // Control enablement/disablement of translationComponent depending on
      // whether accounts where successfully loaded or not.
      this.translationComponent.disable(!value);
      // Only make a request for glossaries if accounts successfully loaded.
      if (value) {
        this.translationComponent.getGlossaries();
      }
    }
  }

  /**
   * The AccountsComponent selection callback function for selected options.
   * @param values List of account IDs.
   */
  accountSelection(values: string[]) {
    // Should a new tab be available then the same conditional pattern must be
    // implemented whenever AccountsComponent gets used across multiple tabs:
    // (this.getSelectedTabIndex() === TabIndex.SOME_OTHER_TAB)
    //
    // Note that resetting CampaignsComponent is required in all conditions in
    // order to force validation handling whenever accounts get selected
    // otherwise values from the previous UI interaction will get used even
    // though they arent't visible in the campaign's selection field.
    if (this.getSelectedTabIndex() === TabIndex.TRANSLATE) {
      const campaignsComponent =
          this.getCampaignsComponentByTabIndex(TabIndex.TRANSLATE);
      campaignsComponent.reset();
      this.translationAccountIds = values;
      campaignsComponent.getCampaigns(this.translationAccountIds);
    }
  }

  /**
   * The AccountsComponent validation callback function for errors.
   * @param value Whether accounts validation returned errors or not.
   */
  accountsValidationError(value: boolean) {
    // Should a new tab be available then the same conditional pattern must be
    // implemented whenever AccountsComponent gets used across multiple tabs:
    // (this.getSelectedTabIndex() === TabIndex.SOME_OTHER_TAB)
    if (this.getSelectedTabIndex() === TabIndex.TRANSLATE) {
      this.translationAccountsHasValidationError = value;
    }
  }

  /**
   * The CampaignsComponent selection callback function for selected options.
   * @param values List of campaign IDs.
   */
  campaignSelection(values: string[]) {
    // Should a new tab be available then the same conditional pattern must be
    // implemented whenever CampaignsComponent gets used across multiple tabs:
    // (this.getSelectedTabIndex() === TabIndex.SOME_OTHER_TAB)
    if (this.getSelectedTabIndex() === TabIndex.TRANSLATE) {
      this.translationCampaignIds = values;
    }
  }

  /**
   * The CampaignsComponent validation callback function for errors.
   * @param value Whether campaigns validation returned errors or not.
   */
  campaignsValidationError(value: boolean) {
    // Should a new tab be available then the same conditional pattern must be
    // implemented whenever CampaignsComponent gets used across multiple tabs:
    // (this.getSelectedTabIndex() === TabIndex.SOME_OTHER_TAB)
    if (this.getSelectedTabIndex() === TabIndex.TRANSLATE) {
      this.translationCampaignsHasValidationError = value;
    }
  }

  /**
   * The translationComponent validation callback function for errors.
   * @param value Whether translation validation returned errors or not.
   */
  translationValidationError(value: boolean) {
    this.translationHasValidationError = value;
  }

  /**
   * Returns whether translation tab has errors or not.
   * @returns The error status of the translation tab.
   */
  hasTranslationError(): boolean {
    return this.translationHasValidationError ||
        this.translationAccountsHasValidationError ||
        this.translationCampaignsHasValidationError;
  }

  // New error functions for new components must be created as it controls the
  // disabling/enabling of the run button within their corresponding tabs:
  // hasSomeOtherError(): boolean {
  //   return this.someOtherComponentHasValidationError ||
  //       this.someOtherAccountsHasValidationError;
  // }

  isRunRequestedStatus(): boolean {
    return this.requestStatus === RequestStatus.REQUESTED;
  }

  run() {
    // Close the snackbar in case it is open.
    this.snackbar.dismiss();

    this.requestStatus = RequestStatus.REQUESTED;
    // The clientId property is defined as a window object by the Google Tag
    // Manager script so attemping to access it directly will fail because it's
    // not recognized as part of the native window object. E.g. window.clientId
    // returns undefined. So the native window object is set as a window object
    // that contains the clientId property in order to gets its value.
    const windowObject = window as unknown as ClientIdProperty;
    const clientId = windowObject.clientId;

    const accountIds = [];
    const campaignIds = [];
    const workers = [];

    let translationData: Translation;
    if (!this.hasTranslationError()) {
      accountIds.push(this.translationAccountIds!);
      campaignIds.push(this.translationCampaignIds!);
      translationData = this.translationComponent.getTranslationData();
      workers.push(Worker.TRANSLATION_WORKER);
    }

    // Should a new tab that represents a new feature be available then similar
    // logic for appending its required data must be added:
    // if (!this.hasSomeOtherError()) {
    //   accountIds.push(this.someOtherAccountIds!);
    //   someOtherData = this.someOtherCompoent.getSomeOtherData();
    //   workers.push(Worker.SOME_OTHER_WORKER);
    // }

    this.disable(true);
    this.runService
        .run(
            // Concatenate account IDs and campaign IDs that were selected
            // across all tabs.
            flattenAndFilter(accountIds), flattenAndFilter(campaignIds),
            translationData!? translationData!.sourceLanguageCode : '',
            translationData!? translationData!.targetLanguageCode : '',
            translationData!? translationData!.shortenTranslationsToCharLimit :
                              false,
            translationData!? translationData!.translateKeywords : false,
            translationData!? translationData!.translateAds : false,
            translationData!? translationData!.translateExtensions : false,
            translationData!? translationData!.glossaryId : '', workers,
            clientId)
        .subscribe(
            (response => {
              this.requestStatus = RequestStatus.RESPONDED;
              this.disable(false);
              this.openDialog(response.body!);
              console.log('Run service request for translation successful.');
            }),
            (error => {
              this.requestStatus = RequestStatus.ERROR;
              this.disable(false);
              this.openSnackBar(error, FontIcon.ERROR);
              console.error(error);
            }));
  }

  /**
   * Returns the index of the selected tab.
   * @returns The index of the selected tab.
   */
  private getSelectedTabIndex(): number {
    return this.tabGroup.selectedIndex!;
  }

  /**
   * Returns a CampaignsComponent by the index of the tab. Useful when other
   * instances of the component exist in multiple tabs.
   * @param index The index of the tab.
   * @returns An instance of the CampaignsComponent.
   */
  private getCampaignsComponentByTabIndex(index: number): CampaignsComponent {
    return this.campaignsComponents.get(index - 1)!;
  }

  /**
   * Returns a MatButton by the index of the tab. Useful when other instances of
   * the component exist in multiple tabs.
   * @param index The index of the tab.
   * @returns An instance of the MatButton.
   */
  private getButtonByTabIndex(index: number): MatButton {
    return this.buttons.get(index - 1)!;
  }

  /**
   * Disables/enables all tabs and their content.
   * @param isDisabled Whether tab/component is disabled or not.
   */
  private disable(isDisabled: boolean) {
    // Disabling/enabling a tab does not disable its content so each component
    // within it must be disabled/enabled.
    this.translationComponent.disable(isDisabled);
    for (const component of this.accountsComponents) {
      component.disable(isDisabled);
    }
    for (const component of this.campaignsComponents) {
      component.disable(isDisabled);
    }
    // Only disable/enable button in selected active tab.
    this.getButtonByTabIndex(this.tabGroup.selectedIndex!);
    // Make sure all tabs are not selectable when isDisabled is true.
    for (const component of this.tabs) {
      component.disabled = isDisabled;
    }
  }

  private openDialog(value: Output) {
    this.dialog.open(DialogComponent, {data: {value}});
  }

  private openSnackBar(message: string, fontIcon: string) {
    this.snackbar.openFromComponent(
        SnackbarComponent, {data: {message, fontIcon}});
  }
}
