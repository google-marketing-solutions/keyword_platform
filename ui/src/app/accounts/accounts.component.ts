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
import {MatSnackBar} from '@angular/material/snack-bar';

import {ControlName, FontIcon} from '../models/enums';
import {Selection} from '../models/interfaces';
import {SelectionGroup} from '../models/types';
import {MultiSelectComponent} from '../multi-select/multi-select.component';
import {GoogleAdsService} from '../services/google-ads.service';
import {SnackbarComponent} from '../snackbar/snackbar.component';

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
  @Output() readonly loadEvent = new EventEmitter<boolean>();
  @Output() readonly selectionEvent = new EventEmitter<string[]>();
  @Output() readonly validationErrorEvent = new EventEmitter<boolean>();

  form = new FormGroup({});

  entities!: Selection[];

  showSpinner = false;

  controlName = '';

  private ids: string[] = [];

  @ViewChild(MultiSelectComponent)
  private readonly component!: MultiSelectComponent;

  constructor(
      private readonly changeRefDetector: ChangeDetectorRef,
      private readonly snackbar: MatSnackBar,
      private readonly googleAdsService: GoogleAdsService) {}

  ngOnInit() {
    this.controlName = ControlName.ACCOUNTS;
    this.getAccounts();
  }

  ngAfterViewInit() {
    this.form.addControl(this.controlName, this.component.control);
    this.getControl().valueChanges.subscribe(() => {
      this.validationErrorEvent.emit(this.hasError());
    });
    this.changeRefDetector.detectChanges();
  }

  selection(value: SelectionGroup) {
    const account = value as Selection[];
    const length = account.length;

    this.ids = [];
    if (length === 0) {
      return;
    }
    for (let i = 0; i < length; i++) {
      this.ids.push(account[i]['id']);
    }
    this.selectionEvent.emit(this.ids);
  }

  disable(isdisabled: boolean) {
    (isdisabled) ? this.form.disable() : this.form.enable();
  }

  private getAccounts() {
    this.showSpinner = true;
    console.log('Accounts requested.');
    this.googleAdsService.getAccounts().subscribe(
        (response => {
          this.showSpinner = false;
          this.entities = response.body!;
          if (this.entities.length > 0) {
            this.disable(false);
            this.loadEvent.emit(true);
            console.log('Accounts request successful.');
          } else {
            this.openSnackBar(
                'No eligible accounts available.', FontIcon.PRIORITY);
            this.loadEvent.emit(false);
          }
        }),
        (error => {
          this.showSpinner = false;
          this.openSnackBar(error, FontIcon.ERROR);
          this.loadEvent.emit(false);
          console.error(error);
        }));
  }

  private getControl(): AbstractControl {
    const form = this.form as FormGroup;
    return form.controls[this.controlName];
  }

  private hasError(): boolean {
    const control = this.getControl();
    const result = [];
    if (control.errors) {
      result.push(control.errors);
    }
    return result.length > 0;
  }

  private openSnackBar(message: string, fontIcon: string) {
    this.snackbar.openFromComponent(
        SnackbarComponent, {data: {message, fontIcon}});
  }
}
