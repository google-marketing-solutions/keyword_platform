/**
 * @license
 * Copyright 2024 Google LLC.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     https://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

import {Component, EventEmitter, Input, OnChanges, OnInit, Output, QueryList, SimpleChanges, ViewChildren} from '@angular/core';
import {FormControl, Validators} from '@angular/forms';
import {MatCheckbox} from '@angular/material/checkbox';
import {Selection} from 'app/models/interfaces';
import {Observable} from 'rxjs';
import {map, startWith} from 'rxjs/operators';

/** Enum for Select All option in the select drop down. */
enum SelectAllOption {
  id = '0',
  name = 'Select All'
}

/**
 * Interface for select options. Useful for controlling the selected state of
 * each option.
 */
interface Option {
  selectionData: Selection;
  selected: boolean;
}

/** A multi select component. */
@Component({
  selector: 'app-multi-select',
  templateUrl: './multi-select.component.html',
  styleUrls: ['./multi-select.component.scss']
})
export class MultiSelectComponent implements OnInit, OnChanges {
  @ViewChildren('checkbox') checkboxes!: QueryList<MatCheckbox>;

  @Input() controlName?: string;
  @Input() label?: string;
  @Input() className?: string;
  @Input() isRequired?: boolean;
  @Input({required: true}) values!: Selection[];

  @Output() readonly selectionEvent = new EventEmitter<Selection[]>();

  control = new FormControl();

  selectionValues: Option[] = [];

  filteredSelectionValues?: Observable<Option[]>;
  lastFilteteredSelectionValue = '';
  hasUpdatedSelection = false;

  selectedOptions: Option[] = [];

  ngOnInit() {
    if (this.isRequired) {
      this.control.addValidators(Validators.required);
    }

    // Disable control by default until it gets successful results from parent
    // component.
    this.control.disable();

    this.control.statusChanges.subscribe(() => {
      // Reset all selections if the autocomplete input textfield is empty and
      // options are still included in the selectedOptions array. This can occur
      // when all input from the text field is deleted without unchecking
      // selection options first.
      if (this.selectedOptions.length > 0 && this.control.errors) {
        this.disableAllSelectedOptions(false);
        this.removeAndUncheckAllSelectedOptions();
      }
    });
  }

  /**
   * Callback method for changes.
   *
   * @param changes Provides values of a new input change from a previous one.
   * Required because the instantiator of this component might depend on a
   * service (api) that doesn't return data when the OnInit callback is invoked.
   */
  ngOnChanges(changes: SimpleChanges) {
    // Reset array of options anytime data changes otherwise data would
    // continuously be appended to the array. This can occur when this component
    // is dependent on data from another component. For example, if a specific
    // Google Ads account is selected then its campaigns should be appended but
    // if that account is unselected and another account is selected after the
    // selection panel is closed then only the campaigns from that new account
    // selection should be appended, not campaigns from both.
    this.selectionValues = [];

    const currentValue = changes['values']['currentValue'];
    if (currentValue) {
      if (currentValue.length > 1) {
        this.selectionValues.push({
          selectionData: {id: SelectAllOption.id, name: SelectAllOption.name},
          selected: false
        });
      }
      for (const value of currentValue) {
        this.selectionValues.push({selectionData: value, selected: false});
      }

      this.filteredSelectionValues = this.control.valueChanges.pipe(
          startWith(''),
          map(value => typeof value === 'string' ?
                  value :
                  this.lastFilteteredSelectionValue),
          map(filter => this.filter(filter)));
    }
  }

  /**
   * Displays select options in the autocomplete input text field.
   * @param selectOptions The select options that get checked/unchecked.
   * @returns The name of the checked select options to display.
   */
  displaySelectOptions(selectOptions: Option[]): string {
    let displayOptions = '';

    if (Array.isArray(selectOptions)) {
      const length = selectOptions.length;
      selectOptions.forEach((option, index) => {
        const selectAllOptionId = SelectAllOption.id;
        const firstOption = selectOptions[0];
        // Only show the current option that was selected individually.
        if (length === 1 &&
            (selectOptions[index].selectionData['id'] !== selectAllOptionId)) {
          displayOptions = this.getDisplayName(option);
          // Show options that were incrementally selected.
        } else if (
            length > 1 &&
            (firstOption.selectionData['id'] !== selectAllOptionId)) {
          displayOptions = this.getDisplayName(firstOption) + ' and (+' +
              (length - 1) + ' more selected)';
          // When interactions above do not occur then all is selected.
        } else {
          displayOptions = 'All ' + (length - 1) + ' options selected';
        }
      });
    }

    return displayOptions;
  }

  // TODO(): Remove this function when responses of services are
  // updated to share the same shape.
  getDisplayName(option: Option): string {
    const selectionData = option.selectionData;
    let optionName = selectionData['name'];
    if (selectionData['display_name']) {
      optionName = selectionData['display_name'];
    }
    return optionName;
  }

  /**
   * The checkbox change callback for selecting options.
   *
   * @param selectedOption The select option that gets checked/unchecked.
   */
  onCheckboxChange(selectedOption: Option) {
    const selectAllOptionId = SelectAllOption.id;
    const selectedOptionId = selectedOption.selectionData['id'];

    // Set/reset selected state of checkbox based on interaction.
    selectedOption.selected = !selectedOption.selected;

    // Select all conditions.
    if (selectedOptionId === selectAllOptionId) {
      if (selectedOption.selected) {
        this.removeAllSelectedOptions();
        this.appendAllSelectedOptions(true);
        this.setCheckStatusForAllSelectedOptions(true);
        this.disableAllSelectedOptions(true);
      } else {
        this.disableAllSelectedOptions(false);
        this.removeAndUncheckAllSelectedOptions();
        selectedOption.selected = false;
      }
      // Non-select all conditions.
    } else {
      // Reset selected state and halt process when all options are checked
      // and attempts are being made to check/uncheck other options (excluding
      // select all).
      if (this.getAllSelectedOptions().length === this.selectionValues.length) {
        selectedOption.selected = false;
        return;
      }
      if (selectedOption.selected) {
        this.appendSelectedOption(selectedOption);
      } else {
        const index = this.getSelectedOptionIndex(selectedOption);
        this.removeSelectedOption(index);
      }
    }

    // Set selectedOptions as the value for the form control.
    this.control.setValue(this.getAllSelectedOptions());

    this.hasUpdatedSelection = true;
  }

  /**
   * The closed callback for closing the autocomplete panel. Emits the selection
   * event to the parent component/element.
   */
  onClosed() {
    if (this.getAllSelectedOptions().length > 0 && this.hasUpdatedSelection) {
      // Clone a version of selectedOptions that only includes SelectionData
      // because the selection boolean is not a valid SelectionData property
      // and then emit it to the receiving parent element/component.
      const selectionDataValue: Selection[] = this.getAllSelectedOptions().map(
          ({selectionData}) => (selectionData));
      // Remove SelectAllOption when it is included because it is not a valid
      // SelectionData value.
      if (selectionDataValue[0]['id'] === SelectAllOption.id) {
        selectionDataValue.shift();
      }
      this.selectionEvent.emit(selectionDataValue);
      this.hasUpdatedSelection = false;
    }
  }

  private appendAllSelectedOptions(selected: boolean) {
    for (const value of this.selectionValues) {
      this.appendSelectedOption({selectionData: value.selectionData, selected});
    }
  }

  private appendSelectedOption(option: Option) {
    this.selectedOptions.push(option);
  }

  private disableAllSelectedOptions(disable: boolean) {
    if (this.checkboxes) {
      this.checkboxes.forEach((checkbox, index) => {
        if (index !== 0) {
          checkbox.disabled = disable;
        }
      });
    }
  }

  private isMatchingValue(value: string): Option[] {
    return this.selectionValues.filter(option => {
      return this.getDisplayName(option).toLowerCase().includes(
          value.toLowerCase());
    });
  }

  private filter(value: string): Option[] {
    this.lastFilteteredSelectionValue = value;
    if (value) {
      // If select all is already checked then filtering is not needed.
      const selectedOption = this.selectedOptions[0];
      if (selectedOption &&
          selectedOption.selectionData['id'] === SelectAllOption.id &&
          selectedOption.selected) {
        return this.selectionValues;
      }

      const matchingValue = this.isMatchingValue(value);
      // Prevent select all from being filtered.
      if (matchingValue[0] &&
          matchingValue[0].selectionData['id'] === SelectAllOption.id &&
          !matchingValue[0].selected) {
        return this.selectionValues;
      } else {
        return matchingValue;
      }
    } else {
      return this.selectionValues;
    }
  }

  private getAllSelectedOptions(): Option[] {
    return this.selectedOptions;
  }

  private getSelectedOptionIndex(selectedOption: Option): number {
    const index = this.selectedOptions.findIndex(
        option =>
            option.selectionData['id'] === selectedOption.selectionData['id']);
    return index;
  }

  private removeAllSelectedOptions() {
    this.selectedOptions = [];
  }

  private removeAndUncheckAllSelectedOptions() {
    // Reset selected state before removing all selections in case their states
    // persist.
    for (const value of this.selectionValues) {
      value.selected = false;
    }
    this.removeAllSelectedOptions();
    this.setCheckStatusForAllSelectedOptions(false);
  }

  private removeSelectedOption(index: number) {
    this.selectedOptions.splice(index, 1);
  }

  private setCheckStatusForAllSelectedOptions(checked: boolean) {
    for (const checkbox of this.checkboxes) {
      checkbox.checked = checked;
    }
  }
}
