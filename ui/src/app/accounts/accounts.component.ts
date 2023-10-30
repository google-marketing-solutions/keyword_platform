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

import {AfterViewInit, ChangeDetectorRef, Component, EventEmitter, OnInit, Output, ViewChild} from '@angular/core';
import {AbstractControl, FormGroup} from '@angular/forms';

import {Selection} from '../models/interfaces';
import {SelectionGroup} from '../models/types';
import {MultiSelectComponent} from '../multi-select/multi-select.component';
import {GoogleAdsService} from '../services/google-ads.service';

const ACCOUNTS_CONTROL_NAME = 'accounts';

/**
 * An accounts component.
 *
 * TODO(): Consider creating abstract/base class for this component
 * as there are other components that follow the same pattern/logic.
 */
@Component({
  selector: 'app-accounts',
  templateUrl: './accounts.component.html',
  styleUrls: ['./accounts.component.scss']
})
export class AccountsComponent implements OnInit, AfterViewInit {
  @Output() readonly accountsLoadEvent = new EventEmitter<boolean>();
  @Output() readonly accountSelectionEvent = new EventEmitter<string[]>();
  @Output() readonly accountsValidationErrorEvent = new EventEmitter<boolean>();

  form = new FormGroup({});

  accounts!: Selection[];

  showSpinner = false;

  private accountIds: string[] = [];

  @ViewChild(MultiSelectComponent)
  private readonly control!: MultiSelectComponent;

  constructor(
      private readonly changeRefDetector: ChangeDetectorRef,
      private readonly googleAdsService: GoogleAdsService) {}

  ngOnInit() {
    this.getAccounts();
  }

  ngAfterViewInit() {
    this.form.addControl(ACCOUNTS_CONTROL_NAME, this.control.control);
    this.getFormControl().valueChanges.subscribe(() => {
      this.accountsValidationErrorEvent.emit(this.hasFormError());
    });
    this.changeRefDetector.detectChanges();
  }

  accountSelection(value: SelectionGroup) {
    const account = value as Selection[];
    const length = account.length;

    this.accountIds = [];
    if (length === 0) {
      return;
    }
    for (let i = 0; i < length; i++) {
      this.accountIds.push(account[i]['id']);
    }
    this.accountSelectionEvent.emit(this.accountIds);
  }

  disableForm(disable: boolean) {
    (disable) ? this.form.disable() : this.form.enable();
  }

  private getAccounts() {
    this.showSpinner = true;
    console.log('Accounts requested.');
    this.googleAdsService.getAccounts().subscribe(
        (response => {
          this.showSpinner = false;
          this.accounts = response.body!;
          this.disableForm(false);
          this.accountsLoadEvent.emit(true);
          console.log('Accounts request successful.');
        }),
        (error => {
          this.showSpinner = false;
          this.accountsLoadEvent.emit(false);
          console.error(error);
        }));
  }

  private getFormControl(): AbstractControl {
    const form = this.form as FormGroup;
    return form.controls[ACCOUNTS_CONTROL_NAME];
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
