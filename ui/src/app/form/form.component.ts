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
import {FormControl, FormGroup} from '@angular/forms';
import {MatDialog} from '@angular/material/dialog';

import {DialogComponent} from '../dialog/dialog.component';
import {DropDownComponent} from '../drop-down/drop-down.component';
import {Worker} from '../models/enums';
import {GoogleAds, Language, Output} from '../models/interfaces';
import {SelectionDataGroup} from '../models/types';
import {GoogleAdsService} from '../services/google-ads.service';
import {RunService} from '../services/run.service';
import {TranslationService} from '../services/translation.service';

/** The parent component of the form. */
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

  private accountIds: string[] = [];
  private campaignIds: string[] = [];

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

  onSubmit() {
    const workers = [];
    if (this.sourceLanguageCode && this.targetLanguageCode) {
      workers.push(Worker.TRANSLATION_WORKER);
    }
    this.runService
        .run(
            this.accountIds, this.campaignIds, this.sourceLanguageCode!,
            this.targetLanguageCode!, workers)
        .subscribe(
            (response => {
              this.openDialog(response.body!);
            }),
            (error => {
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

  private openDialog(response: Output) {
    this.dialog.open(DialogComponent, {data: {value: response}});
  }
}
