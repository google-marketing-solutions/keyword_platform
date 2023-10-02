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

import {AfterViewInit, ChangeDetectorRef, Component, OnInit, QueryList, ViewChildren} from '@angular/core';
import {AbstractControl, FormControl, FormGroup, ValidationErrors, ValidatorFn} from '@angular/forms';
import {MatDialog} from '@angular/material/dialog';
import {MatSlideToggle, MatSlideToggleChange} from '@angular/material/slide-toggle';

import {DialogComponent} from '../dialog/dialog.component';
import {DropDownComponent} from '../drop-down/drop-down.component';
import {RequestStatus, Worker} from '../models/enums';
import {GoogleAds, Language, Output} from '../models/interfaces';
import {SelectionDataGroup} from '../models/types';
import {GoogleAdsService} from '../services/google-ads.service';
import {RunService} from '../services/run.service';
import {TranslationService} from '../services/translation.service';


const CAMPAIGN_CONTROL = 'campaigns';

enum LanguageControl {
  SOURCE_LANGUAGE = 'source-language',
  TARGET_LANGUAGE = 'target-language'
}

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
 * The parent component of the form.
 *
 * TODO(): Move translation/language logic to its own "Translate"
 * component so that this component can be more like a parent component to child
 * components or in other words workers. E.g., translate component/worker,
 * classify component/worker, etc.
 */
@Component({
  selector: 'app-form',
  templateUrl: './form.component.html',
  styleUrls: ['./form.component.scss']
})
export class FormComponent implements OnInit, AfterViewInit {
  form = new FormGroup({});

  accounts!: GoogleAds[];
  campaigns!: GoogleAds[];

  languages!: Language[];
  sourceLanguageCode?: string;
  targetLanguageCode?: string;
  multipleTemplates = false;
  showSpinner = false;

  private accountIds: string[] = [];
  private campaignIds: string[] = [];

  requestStatus = RequestStatus.NONE;

  @ViewChildren('component')
  private readonly components!: QueryList<DropDownComponent>;

  @ViewChildren('slideToggle')
  private readonly slideToggles!: QueryList<MatSlideToggle>;

  constructor(
      private readonly changeRefDetector: ChangeDetectorRef,
      private readonly googleAdsService: GoogleAdsService,
      private readonly runService: RunService,
      private readonly translationService: TranslationService,
      private readonly dialog: MatDialog) {}

  ngOnInit() {
    this.languages = this.translationService.getLanguages();
    this.getAccounts();
  }

  ngAfterViewInit() {
    for (const component of this.components) {
      this.form.addControl(component.controllerName!, component.control);
    }
    this.addLanguageValidators();
    this.changeRefDetector.detectChanges();
  }

  accountSelection(value: SelectionDataGroup) {
    const account = value as GoogleAds[];
    const length = account.length;

    // Reset campaign selections anytime accounts get selected in order to
    // force validation handling otherwise campaign values from the previous UI
    // interaction gets used even though they aren't visible in the campaign's
    // selection field.
    const controls = this.getFormControls();
    const campaignControl = controls[CAMPAIGN_CONTROL];
    campaignControl.reset();

    this.accountIds = [];
    if (length === 0) {
      return;
    }
    for (let i = 0; i < length; i++) {
      this.accountIds.push(account[i].id);
    }
    this.getCampaigns();
  }

  campaignSelection(value: SelectionDataGroup) {
    const campaign = value as GoogleAds[];
    const length = campaign.length;
    this.campaignIds = [];
    if (length === 0) {
      return;
    }
    for (let i = 0; i < length; i++) {
      this.campaignIds.push(campaign[i].id);
    }
  }

  sourceLanguageSelection(value: SelectionDataGroup) {
    const language = value as Language;
    this.sourceLanguageCode = language.code;
  }

  targetLanguageSelection(value: SelectionDataGroup) {
    const language = value as Language;
    this.targetLanguageCode = language.code;
  }

  templatesTogglechange(event: MatSlideToggleChange) {
    this.multipleTemplates = event.checked;
  }

  onSubmit() {
    const workers = [];
    if (this.sourceLanguageCode && this.targetLanguageCode) {
      workers.push(Worker.TRANSLATION_WORKER);
    }

    this.disableForm(true);
    this.requestStatus = RequestStatus.REQUESTED;

    // The clientId property is defined as a window object by the Google Tag
    // Manager script so attemping to access it directly will fail because it's
    // not recognized as part of the native window object. E.g. window.clientId
    // returns undefined. So the native window object is set as a window object
    // that contains the clientId property in order to gets its value.
    const windowObject = window as unknown as ClientIdProperty;
    const clientId = windowObject.clientId;

    console.log('Run service requested.');
    this.runService
        .run(
            this.accountIds, this.campaignIds, this.sourceLanguageCode!,
            this.targetLanguageCode!, this.multipleTemplates, workers, clientId)
        .subscribe(
            (response => {
              this.requestStatus = RequestStatus.RESPONDED;
              this.disableForm(false);
              this.openDialog(response.statusText!, response.body!);
              console.log('Run service request successful.');
            }),
            (error => {
              this.requestStatus = RequestStatus.ERROR;
              this.disableForm(false);
              this.openDialog(error, null);
              console.error(error);
            }));
  }

  hasFormError(): boolean {
    const controls = this.getFormControls();
    const result = [];
    for (const control of Object.values(controls)) {
      if (control.errors) {
        result.push(control.errors);
      }
    }
    return result.length > 0;
  }

  isRunRequestedStatus(): boolean {
    return this.requestStatus === RequestStatus.REQUESTED;
  }

  private addLanguageValidators() {
    const controls = this.getFormControls();

    const sourceLanguageControl = controls[LanguageControl.SOURCE_LANGUAGE];
    const targetLanguageControl = controls[LanguageControl.TARGET_LANGUAGE];

    // See https://angular.io/api/forms/AbstractControl#addvalidators
    sourceLanguageControl.addValidators(
        this.isSameLanguageValidator(LanguageControl.SOURCE_LANGUAGE));
    targetLanguageControl.addValidators(
        this.isSameLanguageValidator(LanguageControl.TARGET_LANGUAGE));

    sourceLanguageControl.updateValueAndValidity();
    targetLanguageControl.updateValueAndValidity();
  }

  private isSameLanguageValidator(languageControl: string): ValidatorFn {
    return (control: AbstractControl): ValidationErrors|null => {
      const language =
          (languageControl === LanguageControl.SOURCE_LANGUAGE ?
               this.targetLanguageCode :
               this.sourceLanguageCode);
      const value = control.value?.code;
      // Only proceed with the validation check if the value of the language
      // field or the value of the language to compare it to is defined.
      // Otherwise the validation will trigger on load which is not desired.
      if (!language || !value) {
        return null;
      }
      const isSameLanguage = (value === language);
      return isSameLanguage ? {sameLanguage: {value}} : null;
    };
  }

  private disableForm(disable: boolean) {
    for (const control of Object.values(this.getFormControls())) {
      (disable) ? control.disable() : control.enable();
    }

    for (const slideToggle of this.slideToggles) {
      slideToggle.setDisabledState(disable);
    }
  }

  private getAccounts() {
    this.showSpinner = true;
    console.log('Accounts requested.');
    this.googleAdsService.getAccounts().subscribe(
        (response => {
          this.showSpinner = false;
          this.accounts = response.body!;
          this.disableForm(false);
          console.log('Accounts request successful.');
        }),
        (error => {
          this.showSpinner = false;
          this.disableForm(false);
          console.error(error);
        }));
  }

  private getCampaigns() {
    this.disableForm(true);
    this.showSpinner = true;
    console.log('Campaigns requested.');
    this.googleAdsService.getCampaigns(this.accountIds)
        .subscribe(
            (response => {
              this.showSpinner = false;
              this.campaigns = response.body!;
              this.disableForm(false);
              console.log('Campaigns request successful.');
            }),
            (error => {
              this.showSpinner = false;
              this.disableForm(false);
              console.error(error);
            }));
  }

  private getFormControls(): {[key: string]: FormControl;} {
    return this.form.controls;
  }

  private openDialog(statusText: string, value: Output|null) {
    this.dialog.open(DialogComponent, {data: {statusText, value}});
  }
}
