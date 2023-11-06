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

import {Component, EventEmitter, Input, OnChanges, OnInit, Output, SimpleChanges, ViewChild} from '@angular/core';
import {AbstractControl, FormControl, ValidationErrors, ValidatorFn, Validators} from '@angular/forms';
import {MatOption} from '@angular/material/core';
import {Selection} from 'app/models/interfaces';
import {Observable} from 'rxjs';
import {map, startWith} from 'rxjs/operators';

/** A single select component. */
@Component({
  selector: 'app-single-select',
  templateUrl: './single-select.component.html',
  styleUrls: ['./single-select.component.scss']
})
export class SingleSelectComponent implements OnInit, OnChanges {
  @Input() controlName?: string;
  @Input() label?: string;
  @Input() className?: string;
  @Input() isRequired?: boolean;
  @Input({required: true}) values!: Selection[];

  @Output() readonly selectionEvent = new EventEmitter<Selection>();

  control = new FormControl();

  options: string[] = [];

  filteredValues?: Observable<Selection[]>;

  ngOnInit() {
    if (this.isRequired) {
      this.control.addValidators(Validators.required);
    }

    // Disable control by default until it gets succesful results from parent
    // component.
    this.control.disable();
  }

  /**
   * Callback method for changes.
   *
   * @param changes Provides values of a new input change from a previous one.
   * Required because the instantiator of this component might depend on a
   * service (api) that doesn't return data when the OnInit callback is invoked.
   */
  ngOnChanges(changes: SimpleChanges) {
    const currentValue = changes['values']['currentValue'];
    if (currentValue) {
      this.filteredValues = this.control.valueChanges.pipe(
          startWith(''),
          map(value => this.filter(value || '')),
      );
      // Store results in an array for the inputTextValidator.
      for (const value of currentValue) {
        this.options.push(value['name']);
      }
      // Invoke this validator on changes as it is dependent on successful
      // results from the parent component.
      if (this.isRequired) {
        this.control.addValidators(this.inputTextValidator());
      }
    }
  }

  displaySelectOption(option: Selection): string {
    if (option) {
      return this.getDisplayName(option);
    }
    return '';
  }

  // TODO(): Remove this function when responses of services are
  // updated to share the same shape.
  getDisplayName(option: Selection): string {
    let optionName = option['name'];
    if (option['display_name']) {
      optionName = option['display_name']
    }
    return optionName;
  }

  onClosed() {
    const value = this.control.value;
    // Emitting the value after closing the selection panel and not selecting an
    // option should send an invalid value that does not match the expected
    // shape of the value's object so it should not be read by the parent
    // component/element when this component does not have validation.
    if ((!this.isRequired && !this.isValidValue(value))) {
      this.emitSelectionEvent(value);
    }
  }

  onSelected(selection: MatOption) {
    this.emitSelectionEvent(selection.value);
  }

  private emitSelectionEvent(selection: Selection) {
    this.selectionEvent.emit(selection);
  }

  private filter(value: Selection|string): Selection[] {
    const selectionDataValue = value as Selection;
    const selectionName = this.getDisplayName(selectionDataValue);
    const stringValue = value as string;
    let filterValue = '';
    if (selectionName) {
      filterValue = selectionName.toLowerCase();
    } else {
      filterValue = stringValue.toLowerCase();
    }
    return this.values.filter(
        value =>
            this.getDisplayName(value).toLowerCase().includes(filterValue));
  }

  // TODO(): Consider creating abstract/base class for validators as
  // there are other custom validators in the repository.
  private inputTextValidator(): ValidatorFn {
    return (control: AbstractControl): ValidationErrors|null => {
      const value = control.value;
      if (!value) {
        return null;
      }
      return (!this.isValidValue(control.value)) ? {invalidText: true} : null;
    };
  }

  private isValidValue(value: Selection): boolean {
    if (!value) {
      return false;
    }
    return this.options.includes(value['name']);
  }
}
