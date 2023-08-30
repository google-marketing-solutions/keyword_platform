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
import {MatSlideToggleChange} from '@angular/material/slide-toggle';

import {DialogComponent} from '../dialog/dialog.component';
import {DropDownComponent} from '../drop-down/drop-down.component';
import {RequestStatus, Worker} from '../models/enums';
import {GoogleAds, Language, Output} from '../models/interfaces';
import {SelectionDataGroup} from '../models/types';
import {GoogleAdsService} from '../services/google-ads.service';
import {RunService} from '../services/run.service';
import {TranslationService} from '../services/translation.service';

enum LanguageControl {
  SOURCE_LANGUAGE = 'source-language',
  TARGET_LANGUAGE = 'target-language'
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

  private accountIds: string[] = [];
  private campaignIds: string[] = [];

  requestStatus = RequestStatus.NONE;

  @ViewChildren('component')
  private readonly components!: QueryList<DropDownComponent>;

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
    this.campaigns = [];
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
    // Disable form upon request.
    this.disableControls(true);
    this.requestStatus = RequestStatus.REQUESTED;
    this.runService
        .run(
            this.accountIds, this.campaignIds, this.sourceLanguageCode!,
            this.targetLanguageCode!, this.multipleTemplates, workers)
        .subscribe(
            (response => {
              this.requestStatus = RequestStatus.RESPONDED;
              this.openDialog(response.status!, response.body!);
            }),
            (error => {
              this.requestStatus = RequestStatus.ERROR;
              this.openDialog(0, null);
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

  private disableControls(disable: boolean) {
    for (const control of Object.values(this.getFormControls())) {
      (disable) ? control.disable() : control.enable();
    }
  }

  private getAccounts() {
    this.googleAdsService.getAccounts().subscribe(
        (response => {
          this.accounts = response.body!;
        }),
        (error => {
          console.error(error);
        }));
  }

  private getCampaigns() {
    this.campaigns = [];
    this.googleAdsService.getCampaigns(this.accountIds)
        .subscribe(
            (response => {
              this.campaigns = response.body!;
            }),
            (error => {
              console.error(error);
            }));
  }

  private getFormControls(): {[key: string]: FormControl;} {
    return this.form.controls;
  }

  private openDialog(status: number, value: Output|null) {
    this.dialog.open(DialogComponent, {data: {status, value}});
    this.dialog.afterAllClosed.subscribe(() => {
      // Enable form after the results rendered in the dialog container gets
      // closed so that the form can be interacted with again.
      this.disableControls(false);
    });
  }
}
