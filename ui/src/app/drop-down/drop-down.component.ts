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

import {Component, EventEmitter, Input, OnInit, Output} from '@angular/core';
import {FormControl, Validators} from '@angular/forms';
import {MatOption} from '@angular/material/core';
import {MatSelect} from '@angular/material/select';
import {GoogleAds} from 'app/models/interfaces';

import {SelectionData} from '../models/types';

/** A drop down component. */
@Component({
  selector: 'app-drop-down',
  templateUrl: './drop-down.component.html',
  styleUrls: ['./drop-down.component.scss']
})
export class DropDownComponent implements OnInit {
  @Input() controllerName?: string;
  @Input() label?: string;
  @Input() className?: string;
  @Input() isMultiple?: boolean;
  @Input() isRequired?: boolean;
  @Input({required: true}) values!: SelectionData[];

  @Output() readonly selectionEvent = new EventEmitter<SelectionData[]>();

  names: string[] = [];

  control = new FormControl();

  ngOnInit() {
    if (this.isRequired) {
      this.control.addValidators(Validators.required);
    }
  }

  concatenateValue(value: SelectionData) {
    const googleAdsValue = value as GoogleAds;
    if (googleAdsValue.id) {
      return googleAdsValue.id.concat(' - ', googleAdsValue.name);
    }
    return value.name;
  }

  toggleAllSelection(selection: MatSelect) {
    const options = selection.options;
    const isSelected: boolean =
        // 'Select All' has value of 0.
        options
            .filter((item: MatOption) => item.value === 0)
            // Get value of selection to determine if 'Select All' is selected
            // or not.
            // Get the first element as there should only be 1 option with value
            // of 0 in the list.
            .map((item: MatOption) => item.selected)[0];
    if (isSelected) {
      options.forEach((item: MatOption) => item.select());
    } else {
      options.forEach((item: MatOption) => item.deselect());
    }
  }

  onChange(selection: SelectionData[]) {
    // If multi-select then make sure to remove the first element because its
    // value is undefined due to it being 'Select All'.
    if (this.isMultiple && !selection[0]) {
      selection.shift();
    }
    this.selectionEvent.emit(selection);
  }
}
