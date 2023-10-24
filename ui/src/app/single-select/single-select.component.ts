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

import {Component, EventEmitter, Input, OnChanges, OnInit, Output, SimpleChanges} from '@angular/core';
import {FormControl, Validators} from '@angular/forms';
import {MatOption} from '@angular/material/core';
import {SelectionData} from 'app/models/interfaces';
import {Observable} from 'rxjs';
import {map, startWith} from 'rxjs/operators';

/** A single select component. */
@Component({
  selector: 'app-single-select',
  templateUrl: './single-select.component.html',
  styleUrls: ['./single-select.component.scss']
})
export class SingleSelectComponent implements OnInit, OnChanges {
  @Input() controllerName?: string;
  @Input() label?: string;
  @Input() className?: string;
  @Input() isDisabled?: boolean;
  @Input() isRequired?: boolean;
  @Input({required: true}) values!: SelectionData[];

  @Output() readonly selectionEvent = new EventEmitter<SelectionData>();

  control = new FormControl();

  filteredValues?: Observable<SelectionData[]>;

  selected = false;

  ngOnInit() {
    if (this.isRequired) {
      this.control.addValidators(Validators.required);
    }

    if (this.isDisabled) {
      this.control.disable();
    }
  }

  /**
   * Callback method for changes.
   *
   * @param changes Provides values of a new input change from a previous one.
   * Required because the instantiator of this component might depend on a
   * service (api) that doesn't return data when the OnInit callback is invoked.
   */
  ngOnChanges(changes: SimpleChanges) {
    if (changes['values']['currentValue']) {
      this.filteredValues = this.control.valueChanges.pipe(
          startWith(''),
          map(value => this.filter(value || '')),
      );
    }
  }

  // TODO(): Remove this function when responses of services are
  // updated to share the same shape.
  getDisplayName(option: SelectionData): string {
    let optionName = option['name'];
    if (option['display_name']) {
      optionName = option['display_name']
    }
    return optionName;
  }

  displaySelectOption(option: SelectionData): string {
    if (option) {
      return this.getDisplayName(option);
    }
    return '';
  }

  onSelected(selection: MatOption) {
    this.selected = true;
    this.selectionEvent.emit(selection.value);
  }

  onClosed() {
    // If no option is selected when the selection panel is closed then set a
    // validation error. This can occur when searching and no option is selected
    // thus leaving the select field with an invalid selection.
    if (!this.selected && !this.control.hasError('required')) {
      this.control.setErrors({invalidText: true});
    }
    this.selected = false;
  }

  private filter(value: SelectionData|string): SelectionData[] {
    const selectionDataValue = value as SelectionData;
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
}
